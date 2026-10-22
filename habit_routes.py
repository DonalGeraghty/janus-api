"""Aether's habit API. Shared authentication and encrypted AI selections remain in Janus."""

from datetime import timedelta
from functools import wraps

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from core.habit_service import (HabitInput, HabitUpdate, HabitCheckinInput,
                               HabitLabelInput, HabitLabelUpdate, HabitSettingsInput, habit_today)
from services.firebase.habits import (HabitError, read_habits, create_habit, update_habit,
                                     delete_habit, list_checkins, save_checkin, save_settings, manage_label)
from services.ai_contract import HabitDraftResponse
from services.ai_service import draft_habits
from services.ai_errors import (AIAuthenticationError, AIAuthorizationError, AIBillingError,
                               AIRateLimitError, AIServiceError)
from services.credential_service import CredentialConfigurationError, CredentialEncryptionError


def habit_blueprint(authenticate, selected_credential, decrypt, aad_version):
    routes = Blueprint('aether_habits', __name__)

    def protected(function):
        @wraps(function)
        def endpoint(*args, **kwargs):
            identity = authenticate()
            if not identity:
                return jsonify(status='error', error='Unauthorized'), 401
            try:
                return function(identity, *args, **kwargs)
            except ValidationError:
                return jsonify(status='error', error='Invalid habit data', message='Check the name, schedule, colour, and other fields.'), 400
            except HabitError as error:
                return jsonify(status='error', error=str(error)), error.status
        return endpoint

    def payload(model, partial=False):
        return model.model_validate(request.get_json(silent=True) or {}).model_dump(mode='json', exclude_unset=partial)

    @routes.get('/api/habits')
    @protected
    def habits_list(identity):
        return jsonify(status='success', **read_habits(identity['email'], identity['account_id']))

    @routes.post('/api/habits')
    @protected
    def habits_create(identity):
        return jsonify(status='success', **create_habit(identity['email'], identity['account_id'], payload(HabitInput))), 201

    @routes.put('/api/habits/<habit_id>')
    @protected
    def habits_update(identity, habit_id):
        return jsonify(status='success', **update_habit(identity['email'], identity['account_id'], habit_id, payload(HabitUpdate, True)))

    @routes.delete('/api/habits/<habit_id>')
    @protected
    def habits_delete(identity, habit_id):
        return jsonify(status='success', **delete_habit(identity['email'], identity['account_id'], habit_id))

    @routes.put('/api/habits/settings')
    @protected
    def habits_settings(identity):
        return jsonify(status='success', **save_settings(identity['email'], identity['account_id'], payload(HabitSettingsInput)))

    @routes.get('/api/habit-checkins')
    @protected
    def checkins_list(identity):
        # Defaults do not depend on the account's timezone; explicit calendar ranges should be supplied.
        today = habit_today()
        start = request.args.get('start', (today - timedelta(days=31)).isoformat())
        end = request.args.get('end', today.isoformat())
        return jsonify(status='success', checkins=list_checkins(identity['email'], identity['account_id'], start, end))

    @routes.put('/api/habits/<habit_id>/checkins/<day>')
    @protected
    def checkins_save(identity, habit_id, day):
        return jsonify(status='success', **save_checkin(identity['email'], identity['account_id'], habit_id, day, payload(HabitCheckinInput)))

    @routes.route('/api/habit-<kind>', methods=['POST'])
    @routes.route('/api/habit-<kind>/<item_id>', methods=['PUT', 'DELETE'])
    @protected
    def labels_manage(identity, kind, item_id=None):
        if kind not in ('categories', 'groups'):
            raise HabitError('Not found', 404)
        data = None if request.method == 'DELETE' else payload(HabitLabelInput if request.method == 'POST' else HabitLabelUpdate, request.method == 'PUT')
        return jsonify(status='success', **manage_label(identity['email'], identity['account_id'], kind, request.method, data, item_id)), 201 if request.method == 'POST' else 200

    @routes.post('/api/habits/draft')
    @protected
    def habits_draft(identity):
        data = request.get_json(silent=True)
        message = data.get('message') if isinstance(data, dict) else None
        if not isinstance(message, str) or not message.strip() or len(message.strip()) > 2000:
            raise HabitError('Describe your habits in 1 to 2000 characters')
        email, account_id = identity['email'], identity['account_id']
        selection, credential, error = selected_credential(email, account_id)
        if error:
            return jsonify(status='error', error=error, message='Secure AI settings are unavailable.'), 503
        provider = selection['provider']
        if not credential:
            return jsonify(status='error', error='provider_key_required', provider=provider,
                           message='Connect your selected AI provider in Account to draft habits.'), 409
        state = read_habits(email, account_id)
        context = {'habits': [{'name': habit['name'], 'archived': habit['archived']} for habit in state['habits']],
                   'categories': [item['name'] for item in state['categories']], 'groups': [item['name'] for item in state['groups']]}
        try:
            api_key = decrypt(credential.get('ciphertext', ''), email, provider=provider,
                              aad_version=aad_version(provider, credential))
            draft = draft_habits(message.strip(), context, email, api_key, provider, selection['model'])
            draft = HabitDraftResponse.model_validate(draft).model_dump()
        except (CredentialConfigurationError, CredentialEncryptionError):
            return jsonify(status='error', error='credential_service_unavailable', message='Secure credential storage is unavailable.'), 503
        except (AIAuthenticationError, AIAuthorizationError, AIBillingError, AIRateLimitError, AIServiceError, ValidationError) as failure:
            mappings = [(AIAuthenticationError, 'provider_key_invalid', 'Your provider key is no longer valid.', 422),
                        (AIAuthorizationError, 'provider_access_denied', 'Your provider key does not allow this model.', 403),
                        (AIBillingError, 'provider_billing_required', 'Your provider account needs billing or credit.', 402),
                        (AIRateLimitError, 'provider_rate_limited', 'Your AI provider is busy. Try again shortly.', 429)]
            code, detail, status = 'provider_unavailable', 'Could not draft habits. Try again shortly.', 502
            for error_type, mapped_code, mapped_detail, mapped_status in mappings:
                if isinstance(failure, error_type):
                    code, detail, status = mapped_code, mapped_detail, mapped_status
                    break
            return jsonify(status='error', error=code, provider=provider, message=detail), status
        return jsonify(status='success', draft=draft)

    return routes
