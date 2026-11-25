"""Owner-scoped monthly budget evidence and AI planning. No workbook or plan writes."""
from datetime import datetime, timezone

from flask import current_app, g, jsonify, request
from pydantic import ValidationError

from core.finance import budget as planner
from core.finance.chat import PRIVACY_NOTE
from services import ai_service
from services.ai_credentials import selected_ai_credential, stored_credential_aad_version
from services.ai_errors import AIAuthenticationError, AIAuthorizationError, AIBillingError, AIRateLimitError, AIResponseValidationError, AIServiceError
from services.credential_service import CredentialConfigurationError, CredentialEncryptionError, decrypt_api_key
from services.finance import sync
from services.firebase.finance.rules import FinanceError
from .reports import _snapshot_and_rules
from .shared import blueprint


def _evidence(identity):
    snapshot, rules = _snapshot_and_rules(identity)
    try:
        context = planner.build_context(snapshot, rules)
    except ValueError as error:
        raise FinanceError(str(error), 422) from None
    status = sync.sync_status(identity["email"], identity["account_id"])
    meta = {key: snapshot[key] for key in ("snapshot_id", "rule_set_version", "fetched_at", "source", "coverage")}
    return snapshot, context, {**meta, "stale": status.get("stale", False)}


@blueprint.get("/budget/context")
def budget_context():
    _snapshot, context, meta = _evidence(g.finance_identity)
    return jsonify(status="success", context=context, meta=meta)


@blueprint.post("/budget/plan")
def budget_plan():
    identity = g.finance_identity
    try:
        body = planner.PlanRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError:
        return jsonify(status="error", error="invalid_budget_request", message="Check the notes, cash cushion and corrected assumptions."), 400
    snapshot, context, meta = _evidence(identity)
    if meta["stale"]:
        return jsonify(status="error", error="budget_stale_data", message="Import the latest data in Account before assessing a new plan. Your existing plan is retained."), 409
    if len({item.id for item in body.corrections}) != len(body.corrections) or any(
        item.due_date.strftime('%Y-%m') != context['month'] or
        item.status == 'expected' and item.due_date.isoformat() < context['today']
        for item in body.corrections
    ):
        return jsonify(status='error', error='invalid_budget_request',
                       message='Check that payment corrections have unique IDs and dates in this month. For a payment still expected, use today or a future expected payment date.'), 400

    def ensure_current_evidence():
        current_snapshot, _rules = _snapshot_and_rules(identity)
        current_status = sync.sync_status(identity['email'], identity['account_id'])
        if current_status.get('stale') or current_snapshot['snapshot_id'] != snapshot['snapshot_id'] or current_snapshot['rule_set_version'] != snapshot['rule_set_version']:
            raise FinanceError('Your imported data or rules changed during assessment. Update the plan again.', 409,
                               details={'code': 'budget_data_changed'})

    demo = bool(current_app.config.get('LOCAL_DEMO'))
    selection = {'provider': 'local_demo', 'model': 'illustrative_fixture'}
    if not demo:
        selection, credential, error = selected_ai_credential(identity['email'], identity['account_id'])
        if error:
            return jsonify(status='error', error=error, message='Secure AI settings are unavailable.'), 503
        if not credential:
            return jsonify(status='error', error='provider_key_required', message='Connect your selected AI provider in Account to create a budget plan.'), 409
        try:
            key = decrypt_api_key(credential.get('ciphertext', ''), identity['email'], provider=selection['provider'],
                                  aad_version=stored_credential_aad_version(selection['provider'], credential))
        except (CredentialConfigurationError, CredentialEncryptionError):
            return jsonify(status='error', error='credential_service_unavailable', message='Secure credential storage is unavailable.'), 503
    messages = [{'role': 'user', 'content': planner.prompt(context, body)}]
    attempts = 1 if demo else 2
    reason = ''
    for attempt in range(attempts):
        ensure_current_evidence()
        try:
            raw = planner.demo_proposal(context, body.corrections) if demo else ai_service.finance_budget(
                planner.SYSTEM_PROMPT, messages, identity['email'], key, selection['provider'], selection['model'])
            ensure_current_evidence()
            plan = planner.validate_plan(raw, context, body)
            return jsonify(status='success', plan=plan, context=context,
                meta={**meta, **selection, 'generated_at': datetime.now(timezone.utc).isoformat(),
                      'privacy': PRIVACY_NOTE, 'demo': demo, 'repair_attempted': attempt > 0})
        except AIResponseValidationError as error:
            reason = str(error)
        except (ValueError, ValidationError) as error:
            reason = planner.validation_feedback(error)
        except (AIAuthenticationError, AIAuthorizationError, AIBillingError, AIRateLimitError, AIServiceError):
            return jsonify(status='error', error='budget_provider_unavailable', message='Your AI provider could not create the plan. Check your key, model access, billing and provider limits in Account, then try again.'), 502
        ensure_current_evidence()
        if attempt + 1 < attempts:
            # Ask for a fresh full proposal against the same evidence. Do not
            # replay arbitrary model text or persist/log financial responses.
            messages = messages + [{'role': 'user', 'content':
                'The previous proposal did not pass validation. Return a corrected complete proposal using the same evidence. '
                'Validation feedback (DATA): ' + reason[:1500]}]
    return jsonify(status='error', error='budget_invalid_proposal',
        message='The provider could not produce a consistent budget after an automatic repair attempt. Your previous plan is retained. Try again or adjust the payment assumptions.',
        validation_reason=reason[:1000]), 422
