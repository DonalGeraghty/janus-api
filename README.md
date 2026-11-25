# Janus API

Janus API is the shared backend for three sibling frontends — [Aether](https://github.com/DonalGeraghty/aether) (habits), [Minerva](https://github.com/DonalGeraghty/minerva) (personal finance), and [Nyx](https://github.com/DonalGeraghty/nyx) (nutrition). It provides authentication, encrypted per-user AI credentials, selectable AI models, habit drafting and tracking, meal analysis, finance rules and read-only Sheets access, and account-owned storage.

Read-only ledger sync: `POST /api/finance/sync` reads the account's workbook (`combined data` A:Q) with an automatically refreshed service-account token (or an existing legacy token), mapping columns by header name. Sheets native values are parsed explicitly (1900-system serial dates, native numerics); money is handled as `Decimal` and serialized as decimal strings with `currency: EUR`, timezone `Europe/Dublin`; unknown values stay null, never zero. Snapshots are derived, in-memory and per-account: one sync lock per account, atomic swap on success, and a failed or rejected sync retains the last good snapshot with `stale: true` (a 401/403 from Google maps to 409 `sheets_reconnect_required`). After a restart the status endpoint reports `sync_required` rather than empty data. The snapshot cache is never shared across instances or treated as durable; a private Cloud Storage snapshot is the follow-up if multi-instance stability is required. Janus never writes to the workbook.

Read API: every endpoint reads one pinned snapshot (meta carries `snapshot_id` + `rule_set_version`; no mixed versions) and requires a prior successful sync (`409 sync_required` otherwise). Periods are whole calendar months in Europe/Dublin (`this_month` default, `last_month`, `last_3/6/12` including current, `ytd`, `all`, or custom `start`/`end`); missing months are reported as gaps, never zeros. Budget math sums signed Amount EUR for Income/Expense/Refund with inclusion YES, applies active rules deterministically (priority desc, rule_id asc; first match per independent effect wins) with per-row reasons, excludes transfers/savings/Food Pot from budget cash flow, reports investment principal separately, never subtracts Fee EUR twice, counts receipt groups once, and enforces duplicate/failed/reverted exclusions in code regardless of rules. The sinking fund keeps a stateful recognised-balance ledger across all history; unknown opening recognition blocks unsupported exclusions and is flagged provisional. Money is Decimal, serialized as decimal strings in EUR.

Finance chat: `POST /api/finance/chat` requires a synced snapshot and the account's selected, KMS-stored AI credential. The backend runs the read-only tool registry (`core/finance/chat.py`) itself and sends the bounded pack (<=24 KiB) with the question to the chosen provider — the model never calculates and all financial text is treated as data. Responses carry snapshot/rule-set metadata, coverage, stale flag and a privacy note; they are `no-store` and never logged.

## Monthly AI budget planning

Minerva's Budget tab reads `GET /api/finance/budget/context` for the current Dublin calendar month plus six complete prior months. Context uses canonical rule-adjusted amounts, monthly categories, bounded merchant/payment-day patterns and recent transactions, coverage gaps, and a dated cash snapshot when recognized. Existing cash reserves are never added as income. Context is bounded to 60 KiB; truncation is disclosed and oversized category histories fail explicitly.

`POST /api/finance/budget/plan` accepts `{notes, cushion_eur, corrections}` and uses the account's selected OpenAI, Mistral or Anthropic credential. The LLM infers likely remaining income, bills, seasonal costs and three approaches (Save more, Balanced, More breathing room). Provider-native structured output supplies the proposal. Janus preserves authoritative actuals and user corrections, normalizes unambiguous category casing and numeric cents, and checks dates, monotonic limits, fixed-cost consistency and bill reserves. Already-spent categories omitted from the forecast retain their actual spending with an explicit zero-future-allowance note. A failed structure or business check gets at most one automatic repair attempt against the same evidence; failures return a safe validation reason without logging financial payloads. Janus computes every monthly limit, savings figure and funding gap using Decimal. A changed import, connection or rule set during inference rejects publication; stale data requires a successful import first. Prompts, answers and plans are not stored by Janus and responses are no-store. Minerva keeps the selected plan only in its account-scoped browser session.

The original `/api/finance/budgets` endpoint still describes availability of verified workbook budgets; AI suggestions are a separate planning feature. The local demo returns an explicitly illustrative synthetic plan without calling a provider.

## Retired flashcard functionality

Minerva now uses its finance dashboard and Account pages. The former flashcard CRUD/due/review endpoints, `POST /api/minerva/respond`, and `GET/PUT /api/user/minerva-settings` are removed and return 404. Card drafting prompts, provider methods, scheduling, and operational card storage code are removed too.

Existing stored flashcards and review history are not migrated or erased by this release. Shared legacy-account cleanup removes historical collections and retired integration credentials during explicit account deletion, with account-generation and deletion-token checks. Habit, nutrition and finance routes, shared authentication, and AI credential/model settings remain active.

Deploy the updated Minerva frontend before retiring the backend endpoints if older browser clients still need the study interface.

## Finance rules (Minerva finance migration)

Finance access requires an account-owned connection. New connections use a dedicated Sheets service account and an administrator-approved workbook binding for the exact Janus account generation. The shared reader's Google access does not authorize other Janus users to connect to a workbook. Existing KMS-encrypted token connections keep working until a successful migration replaces their token document with metadata only. Google Sheets remains authoritative; Janus only reads it. All finance responses are `Cache-Control: no-store`.

### Keyless Google Sheets setup

Run once as a Google Cloud administrator from the repository root:

```powershell
python scripts/setup_sheets_reader.py --project YOUR_PROJECT --developer-email YOUR_GOOGLE_LOGIN
```

This discovers Janus's current Cloud Run runtime identity, creates `minerva-sheets-reader` if needed, enables the Sheets/IAM Credentials APIs, and grants Token Creator to the runtime and optional developer **on the reader account only**. It creates no key files and performs no deployment. The reader needs no project-wide data role. Share the specific spreadsheet with its email as **Viewer**.

Approve the private workbook for an existing Janus account. The command prompts for the Janus login email and spreadsheet link; neither belongs in source control:

```powershell
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT
python scripts/approve_finance_workbook.py --project YOUR_PROJECT
```

Approval stores the current account ID and workbook ID under the account's `finance_settings/settings` document. Clients cannot create approvals. Recreating an account requires fresh approval. To switch workbooks, approve the replacement first. Disconnect retains approval and rules; revoking Google access separately requires removing the reader from the Sheet's sharing settings.

Configure `FINANCE_SHEETS_SERVICE_ACCOUNT=minerva-sheets-reader@YOUR_PROJECT.iam.gserviceaccount.com`. Cloud Run's attached identity impersonates the reader. Locally, `gcloud auth application-default login` supplies the developer identity; it needs Token Creator on the reader. Python's google-auth requests only the `spreadsheets.readonly` target scope and refreshes credentials on demand. The deployment workflow configures the reader email for its project. Provision the reader before deploying this change. Synthetic demo mode still needs no cloud credentials.

Account displays the reader email with a Copy button and accepts a spreadsheet link or ID. Connecting checks approval **before** calling Google, verifies the combined-data header, then replaces the connection. Failed verification preserves the existing connection. The frontend starts a full import after connecting and confirms completion separately.

Snapshots and sync statuses are bound to the account generation, workbook, connection ID and reader identity. Replacing/disconnecting invalidates derived data; an in-flight import rechecks its binding before publication, and every read verifies its snapshot still belongs to the current connection. Removed approvals deny service-account access. Historical accounting, receipt allocation and Ask-context improvements remain separate follow-ups.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/finance/connection` | Safe connection metadata and service-account setup/approval status |
| `PUT` | `/api/finance/connection` | Verify `{ "mode": "service_account", "workbook_id": "Sheet link or ID" }`; legacy token requests remain supported |
| `DELETE` | `/api/finance/connection` | Disconnect and clear imported data; saved rules and approval are retained |
| `POST` | `/api/finance/sync` | Pull `combined data` A:Q via Sheets API (UNFORMATTED_VALUE), validate, atomically publish an in-memory snapshot; failed sync keeps last good data with `stale` |
| `GET` | `/api/finance/sync/status` | Last success/attempt, snapshot ID, rule-set version, stale flag, coverage (months, cutoff) and `sync_required` after restart |
| `GET` | `/api/finance/transactions` | Filtered, paginated, bounded rows with per-row rule reason; `period` preset or `start`/`end` whole months |
| `GET` | `/api/finance/summary` | Income/spending/refunds/net, separate transfers and investment, sheet-vs-rule-adjusted reconciliation bridge, gaps, provisional flag |
| `GET` | `/api/finance/cashflow?by=month\|category\|breakdown` | Signed monthly net movements, category totals, or per-month income/expense/refund category breakdowns for in-chart drilldown |
| `GET` | `/api/finance/categories`, `/merchants`, `/trends` | Server-side aggregates over a period |
| `GET` | `/api/finance/net-worth` | Dated snapshot-tab balances; subtotals never double counted; explicit unavailable state when the tab is missing/unrecognized |
| `GET` | `/api/finance/sinking-funds` | Stateful recognised-balance ledger; provisional until the opening balance is verified |
| `GET` | `/api/finance/budgets` | Explicit `available: false` until verified budget data exists |
| `POST` | `/api/finance/chat` | `{message, history?}` answered by the selected provider over a server-computed, owner-scoped context pack of read-only tool results (summary, transactions, categories, merchants, cashflow, period comparison, budgets, sinking funds, net worth, rules, data quality); no write tools; prompt/answer not persisted |
| `GET` | `/api/finance/rules?include_deleted=&scope=&status=` | List rules and the current `rule_set_version` |
| `POST` | `/api/finance/rules` | Create one validated rule (201) |
| `PUT` | `/api/finance/rules/{rule_id}` | Version-checked update (`revision` required; 409 on mismatch) |
| `DELETE` | `/api/finance/rules/{rule_id}?revision=` | Soft delete (kept in history, hidden from default listing) |
| `POST` | `/api/finance/rules/import` | `{ "csv": "...", "mode": "preview" \| "commit" }`; preview validates and lists create/update/unchanged, held and conflicting rows; commit applies atomically in one transaction and bumps the rule-set version once. Missing rows are never implicitly replaced |
| `GET` | `/api/finance/rules/export?format=csv\|json` | CSV download (formula-injection escaped) or lossless JSON |
| `POST` | `/api/finance/rules/test` | Dry-run active rules against up to 100 sample rows; no mutations |
| `GET` | `/api/finance/rules/history` | Rule-set versions with actor, summary and changed IDs |
| `POST` | `/api/finance/rules/restore/{version}` | Restore a previous rule-set version |

Rules are data, never code. Fields, operators and actions are validated against fixed allowlists (`core/finance/rule_engine.py`); an unknown action can never activate and is held with status `review`. Conflicting active assignments (same condition and priority, different outcomes) are reported and the incoming rows are held for review. Priority order is deterministic: higher `priority` first, then `rule_id`. CSV columns are `rule_id,scope,name,type,field,operator,value,action,action_value,priority,status,source_section,description`; `scope` is `janus` (executable/reporting) or `chatgpt_workflow` (reference only). Request bodies are capped at 256 KiB.

Row rules have three independent effects: an accounting decision (`classify`, `exclude`, `allocate`, `reverse`), a category override (`set_category`), and a review flag (`flag`). The first matching rule for each effect wins, so a high-priority classification does not hide a category or review rule. Predicates use the original row plus inferred event fields; actions do not trigger other predicates. `classify` accepts Income, Expense, Refund or Transfer, optionally `Type:Category`; an explicit `set_category` overrides that fallback category. Conflicts are checked within each effect, so compatible classification and category rules can be imported together.

`allocate:unfunded_portion_only` uses the covered-sinking-bill calculation. `reverse:previously_recognised_expense` uses the sinking-release calculation, capped by the recognised balance; it never blindly negates a bank amount. A rule used on the wrong event is flagged for review with `rule_context_not_supported`; any unrecognised release remainder is flagged too. Existing stateful accounting and integrity safeguards remain authoritative. In particular, rules cannot include sheet-NO, invalid, duplicate, failed or reverted rows. An explicit matching exclusion is respected, including on sinking events; use priority to place specific accounting rules before broad transfer exclusions. `allow:sinking_fund` and `include:cash_assets` are reference policies, not row mutations, and cannot suppress executable rules.

Ledger rows expose `derived.applied_rules`, the primary accounting outcome, warnings, and the effective amount. The dry-run endpoint returns the same `derived` interpretation and uses the same accounting engine, alongside all predicate matches. Stateful dry runs need the relevant preceding contributions in the supplied rows; a partial sample cannot establish a historical recognised balance. Invalid JSON action values are rejected; CSV action values that cannot execute are held for review.

Storage lives under `users/{email}` in Firestore: `finance_rules/{rule_id}`, `finance_rule_history/{version}` (full snapshot per version) and `finance_settings/settings` (holds `rule_set_version`). Every mutation is one transaction that reads first, guards the account generation and deletion tombstone, and writes rules, settings and history together. The local in-memory fallback follows the same rules, and guarded account deletion removes all three collections without touching the external Sheet. Run the finance tests with `python -m unittest discover -s tests -p test_finance_rules_api.py`.

## Responsibilities

- Register users and issue seven-day JWT access tokens
- Store password hashes rather than plaintext passwords
- Verify user-supplied OpenAI, Mistral AI, and Anthropic API keys
- Encrypt provider keys with Google Cloud KMS before persistence
- Persist each user's selected provider and model
- Analyze meal descriptions with structured responses from the selected model (Nyx)
- Create, list, update, and delete user-owned nutrition entries (Nyx)
- Generate structured meal recommendations from today's calorie and protein progress (Nyx)
- Manage Aether habits, categories, groups, schedules, timezone settings, dated check-ins, and streak statistics
- Draft reviewable habits from intentions using the selected AI provider and existing habit/label context
- Store opt-in Web Push settings/subscriptions and dispatch local-time reminders
- Delete credentials, nutrition data, workout history, and flashcards when an account is removed
- Delete habit definitions and check-ins as part of guarded account deletion
- Expose health and database-status endpoints for deployment checks

## Architecture

```text
Aether, Minerva, or Nyx (React/Vite frontends)
  └─ Janus API (Flask)
       ├─ Firestore
       │    ├─ users/{email}                          (shared account settings)
       │    ├─ users/{email}/nutrition_entries/{entry}
       │    ├─ users/{email}/aether/state
       │    ├─ users/{email}/habit_checkins/{habit_id}_{date}
       │    ├─ users/{email}/workout_history/{entry}       (legacy cleanup only)
       │    ├─ users/{email}/flashcards/{card}           (legacy cleanup only)
       │    ├─ users/{email}/flashcard_reviews/{review} (legacy cleanup only)
       │    ├─ users/{email}/private/openai
       │    ├─ users/{email}/private/mistral
       │    └─ users/{email}/private/anthropic
       ├─ Google Cloud KMS
       │    └─ encrypts and decrypts each provider key
       ├─ OpenAI Responses API
       ├─ Mistral AI Chat API
       └─ Anthropic Messages API
```

See [Overall architecture](#overall-architecture) below for how this fits together with the three frontends and Google Cloud.

## Tech stack

- Python 3.11
- Flask and Flask-CORS
- Pydantic
- PyJWT
- Firebase Admin and Google Cloud Firestore
- Google Cloud KMS
- OpenAI, Mistral AI, and Anthropic Python SDKs
- pywebpush/py-vapid for standards-based Web Push

## Local development

### Run Janus and Minerva together with a demo user

With this repository at `C:\GitHub\janus-api` and Minerva at
`C:\GitHub\minerva`, run in PowerShell:

```powershell
cd C:\GitHub\janus-api
.\.venv\Scripts\python.exe start_local_demo.py
```

Open http://127.0.0.1:5173 and click **Use demo account**, or sign in with
`demo@minerva.local` / `minerva-demo`. Janus runs at http://127.0.0.1:5000.
Press Ctrl+C in the launcher terminal to stop both apps. Ports 5000 and 5173
must be free. Logs are under the ignored `.local-demo` directory.
For a different Minerva checkout, pass `--minerva C:\path\to\minerva`.

The dedicated `run_demo.py` development harness substitutes in-memory storage
and synthetic Sheets responses, while using the normal password/JWT login,
ledger parser, sync, accounting, rules and finance routes. It supplies six months
of invented transactions and horizontal wealth snapshots relative to today's
Europe/Dublin date. Data and edits reset on restart; tokens expire on restart.
Responses identify the source as `local_demo`. No Firestore, Sheets, KMS or AI
credentials are needed or used. AI requests and external connection changes are
disabled. Budgets remain unavailable and sinking recognition remains provisional.
This preview does not verify the accounting corrections described in the handoff.
Production still uses `app:app`; the demo is bound to loopback only.

For a fresh checkout, create `.venv`, install `requirements.txt`, and run `npm ci`
in Minerva first. Use the Python and Node versions specified by the repositories.
Alternatively, start `.\.venv\Scripts\python.exe run_demo.py` here and
`npm run dev:demo` in Minerva in separate terminals.

### Requirements

- Python 3.11 or newer
- A Firestore-enabled Google Cloud project for persistent data
- A symmetric Cloud KMS key for AI credential storage
- Google Application Default Credentials or a service-account credential

Create a virtual environment and install the dependencies:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

Activate the environment before running commands:

```powershell
# PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS or Linux
source .venv/bin/activate
```

Copy [`.env.example`](.env.example) to `.env` and fill in real values:

```dotenv
FLASK_ENV=development
JWT_SECRET_KEY=replace-with-a-long-random-secret
OPENAI_MODEL=gpt-5.6-sol
MISTRAL_MODEL=mistral-small-2603
ANTHROPIC_MODEL=claude-sonnet-5
AI_KMS_KEY_NAME=projects/PROJECT_ID/locations/REGION/keyRings/janus-gate/cryptoKeys/user-openai-keys
VAPID_PRIVATE_KEY=base64url-private-key
VAPID_PUBLIC_KEY=base64url-public-key
VAPID_SUBJECT=mailto:admin@example.com
PUSH_CRON_SECRET=replace-with-a-long-random-secret

# Optional when Application Default Credentials are not available:
# GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json

# Optional; defaults to 5000:
# PORT=5000

# Optional; otherwise JWT_SECRET_KEY is used:
# OPENAI_SAFETY_SALT=replace-with-an-independent-random-secret
```

Start the API:

```bash
python app.py
```

The server listens on `http://localhost:5000` unless `PORT` is set.

When Firestore is unavailable, local authentication, profile settings, nutrition operations, and habit tracking fall back to process memory. That data disappears when the server restarts. AI credential storage deliberately has no plaintext or in-memory fallback: Firestore or KMS failures cause those operations to fail closed.

## Authentication

Register or log in to receive a JWT, then supply it to protected endpoints:

```http
Authorization: Bearer <token>
```

Passwords must contain at least eight characters. JWTs use HS256 and expire after seven days.

## API

| Method | Path | Authentication | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/auth/register` | No | Create an account and return a JWT |
| `POST` | `/api/auth/login` | No | Authenticate and return a JWT |
| `GET` | `/api/auth/me` | Bearer JWT | Return the current user |
| `DELETE` | `/api/auth/account` | Bearer JWT | Delete the account after password confirmation |
| `GET` | `/api/user/ai-settings` | Bearer JWT | Return the selected model, provider catalog, and safe key statuses |
| `PUT` | `/api/user/ai-settings` | Bearer JWT | Select an allowlisted provider and model |
| `PUT` | `/api/user/ai-credentials/{provider}` | Bearer JWT | Authenticate, encrypt, and store that provider's API key without generating output |
| `GET` | `/api/user/ai-credentials/{provider}` | Bearer JWT | Return safe credential-status metadata |
| `DELETE` | `/api/user/ai-credentials/{provider}` | Bearer JWT | Remove that provider's credential |
| `GET/PUT` | `/api/user/push-settings` | Bearer JWT | Read or change daily reminder settings |
| `POST/DELETE` | `/api/user/push-subscriptions` | Bearer JWT | Add or remove this device's Push subscription |
| `PUT/GET/DELETE` | `/api/user/openai-key` | Bearer JWT | Compatibility alias for the OpenAI credential |
| `POST` | `/api/nutrition/analyze` | Bearer JWT | Analyze a meal without saving it |
| `POST` | `/api/nutrition/recommend` | Bearer JWT | Recommend meals for the rest of the day |
| `POST` | `/api/nutrition/entries` | Bearer JWT | Save a reviewed nutrition entry |
| `GET` | `/api/nutrition/entries` | Bearer JWT | List entries, optionally filtered by date |
| `PUT` | `/api/nutrition/entries/{entry_id}` | Bearer JWT | Replace an owned entry and recalculate totals |
| `DELETE` | `/api/nutrition/entries/{entry_id}` | Bearer JWT | Delete an owned entry |
| `GET` | `/api/habits` | Bearer JWT | Return habits, categories, groups, timezone, streak statistics, and today's check-ins |
| `POST` | `/api/habits` | Bearer JWT | Create a yes/no habit |
| `PUT/DELETE` | `/api/habits/{habit_id}` | Bearer JWT | Edit, reorder, archive/restore, or permanently delete a habit and its check-ins |
| `PUT` | `/api/habits/settings` | Bearer JWT | Set the account's IANA habit timezone |
| `GET` | `/api/habit-checkins` | Bearer JWT | List check-ins for an inclusive start/end date range of at most 366 days |
| `PUT` | `/api/habits/{habit_id}/checkins/{date}` | Bearer JWT | Idempotently complete/undo a dated habit and save an optional note |
| `POST` | `/api/habit-categories` or `/api/habit-groups` | Bearer JWT | Create a category or routine group |
| `PUT/DELETE` | `/api/habit-categories/{id}` or `/api/habit-groups/{id}` | Bearer JWT | Rename/reorder/remove a label; removing it clears its habit associations |
| `POST` | `/api/habits/draft` | Bearer JWT | Draft up to eight editable habits without saving them |
| `POST` | `/api/internal/push/reminders` | `X-Cron-Secret` | Dispatch due reminders from Cloud Scheduler |
| `GET` | `/health` | No | Return service and database status |
| `GET` | `/` | No | List the available endpoints |

The entries list accepts:

- `date=YYYY-MM-DD` to select one UTC calendar day
- `limit=1..100`, defaulting to `50`
- `start=<ISO-8601>&end=<ISO-8601>` to select an inclusive/exclusive
  timezone-aware range of up to eight days; range requests default to a limit
  of `500`
- `all=true` to return the complete nutrition history for an explicit export;
  it cannot be combined with date, range, or limit parameters

Use either `date` or `start`/`end`, not both. Range responses include
`pagination.start`, `pagination.end`, `pagination.limit`, and
`pagination.truncated`.

AI settings accept only these provider/model combinations:

- OpenAI: `gpt-5.6-sol`, `gpt-5.6-terra`, or `gpt-5.6-luna`
- Mistral AI: `mistral-small-2603`, `mistral-large-2512`, or `mistral-medium-3-5`
- Claude (Anthropic): `claude-opus-5`, `claude-sonnet-5`, or `claude-haiku-4-5-20251001`

Existing users without saved AI settings default to OpenAI and `gpt-5.6-sol`. Selecting a provider does not delete any other provider's key. Meal analysis, habit drafting, and recommendation requests never fall back silently: when the selected provider has no stored key, the API returns `409 provider_key_required`.

Credential setup authenticates keys with provider model-metadata endpoints and
does not spend inference tokens. A key can be stored when the provider reports
that billing or credit is required; the successful response includes a
non-fatal `provider_billing_required` warning. Actual analysis and recommendation
requests return `402 provider_billing_required` when the account has no
available credit or has reached its spending limit. Authentication, permission,
rate-limit, and provider-availability failures remain distinct.

Deployments that introduce account generations invalidate older JWTs without an
`account_id` claim. Existing users must sign in once; a successful password
login atomically assigns the legacy account an ID and issues a new token.

### Example nutrition entry

```json
{
  "items": [
    {
      "food": "Scrambled eggs",
      "portion": "2 large eggs",
      "calories": 180,
      "protein_g": 13
    }
  ],
  "eaten_at": "2026-07-22T12:30:00Z",
  "source_message": "I ate two scrambled eggs"
}
```

The API recalculates total calories and protein from the submitted items. Meal analysis is an estimate and is not saved automatically.

An optional UUID `client_request_id` makes nutrition creation idempotent. Janus
API derives an account-scoped document ID from it and returns the existing
entry when a client retries, preventing duplicate records after an ambiguous
network failure.

## Web Push reminders

Generate deployment-safe VAPID values once:

```bash
python scripts/generate_vapid_keys.py
```

Store the printed values as `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`, and
`PUSH_CRON_SECRET` secrets; do not commit their output. Set `VAPID_SUBJECT` to
an administrator `mailto:` or HTTPS contact.

The deployment workflow passes those four GitHub Actions secrets to Cloud Run
and creates or updates a Cloud Scheduler job that invokes the internal endpoint
every five minutes. Each enabled account stores an `HH:MM` reminder time and
IANA timezone. Dispatch uses an atomic, expiring per-user claim so overlapping
scheduler attempts do not send the same daily reminder twice. Failed batches
release the claim for a later retry; HTTP 404/410 Push responses remove expired
subscriptions.

Push payloads are intentionally generic and contain no meal or nutrition data.
Subscription endpoints and key material are never returned by the settings
endpoint. Disabling reminders stops delivery before the browser subscription
is removed. Account deletion removes all subscription documents.

## AI credential security

- Each user supplies their own OpenAI, Mistral AI, and/or Anthropic API key.
- The selected provider authenticates a new key through model metadata before an existing credential is replaced.
- Credit availability is checked during real AI requests rather than stored as durable credential state.
- The plaintext key is encrypted with Cloud KMS and is never returned by the API.
- Firestore stores each provider separately with only ciphertext, the last four characters, version metadata, and timestamps.
- New KMS additional authenticated data includes the normalized user email and provider, binding ciphertext to both.
- Legacy OpenAI ciphertext remains decryptable with its original user-bound authenticated data.
- The plaintext key is decrypted only when Janus API calls the selected provider.
- Credential operations fail closed if Firestore or KMS is unavailable.
- JWTs and guarded data operations carry an immutable account ID, so a token or in-flight request from a deleted account cannot cross into a newly registered account with the same email.
- Account deletion marks the user first; credential and nutrition writes transactionally require the matching live, non-deleting parent account so concurrent requests cannot recreate orphaned data.
- Deletion cleanup is idempotent and generation-bound. Failed deletions remain marked for an authenticated retry, and stale markers resume cleanup automatically.
- Account deletion removes all encrypted provider credentials and all nutrition entries.
- Account deletion also removes Web Push subscriptions; reminder settings disappear with the user document.

Protected data is scoped through the authenticated email. The API currently allows cross-origin requests to `/api/*` from any origin while restricting methods and headers. Replace the wildcard with an origin allowlist before moving to cookie-based authentication.

## Tests

Aether's 282 allowed habit icons are defined in `core/habit_icons.json`, generated alongside the frontend's searchable icon catalog. Manual create/update validation and AI drafts use the same enum. To update both catalogs, run `node scripts/generate-habit-icons.mjs ../janus-api/core/habit_icons.json` from the Aether repository. Existing icon IDs remain valid.

Aether state is stored in `users/{email}/aether/state`; dated check-ins are separate `users/{email}/habit_checkins/{habit_id}_{date}` documents. State is bounded to 100 habits, 50 categories and 50 groups, with a byte-size guard below Firestore's document limit. Every read/write transaction checks the account generation and deletion marker. Cleanup is batched and retryable. The local in-memory fallback follows the same rules; configured Firestore failures fail closed.

Habit input uses `name`, optional `description`, allowlisted `icon`, `colour` as `#RRGGBB`, unique `days` integers (0=Monday through 6=Sunday), nullable `category_id` and `group_id`, and a `start_date` from today through the next ten years. Updates accept these editable fields except start date, plus `archived` and `order`. Schedule/archive revisions are server-owned and take effect tomorrow or on a future start date. Check-ins require a strict boolean `completed` and optional `note` of at most 1000 characters. Future and pre-start check-ins are rejected, and an unscheduled day cannot be completed.

The old `/api/workouts` and `/api/workouts/*` routes are retired and return 404. Historical workout documents remain stored and are still purged by guarded account deletion. Coordinate this deployment with the habit-based Aether frontend; older workout clients are no longer supported.

Streaks count consecutive scheduled completions, skip unscheduled dates, and treat an unfinished today as pending. The last-30-day rate includes elapsed scheduled dates and a completed today. Bootstrap statistics read the account's full check-in history for exact lifetime streaks; calendar range requests query only the requested dates. AI drafts use `{ "message": "..." }`, at most 2000 characters. Context comes from the authenticated account, and the draft is validated across OpenAI, Mistral, and Anthropic.

Run the complete test suite:

```bash
python -m unittest discover -s tests -v
```

The tests cover authentication, provider/model selection, three-provider key isolation, ownership isolation, nutrition CRUD, deterministic total calculation, all provider adapters, API-key lifecycle behavior, and KMS user/provider binding.

## Docker

Build and run the production image:

```bash
docker build -t janus-api .
docker run --rm -p 8080:8080 \
  -e JWT_SECRET_KEY=replace-with-a-long-random-secret \
  -e OPENAI_MODEL=gpt-5.6-sol \
  -e MISTRAL_MODEL=mistral-small-2603 \
  -e ANTHROPIC_MODEL=claude-sonnet-5 \
  -e AI_KMS_KEY_NAME=projects/PROJECT_ID/locations/REGION/keyRings/janus-gate/cryptoKeys/user-openai-keys \
  janus-api
```

The container runs as a non-root user, listens on port `8080`, and checks `/health`.

## Google Cloud deployment

The workflow in [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) tests the application and deploys it from source to Google Cloud Run in `europe-west1`.

Configure these GitHub Actions secrets:

| Secret | Purpose |
| --- | --- |
| `GCP_SA_KEY` | Authenticates the deployment workflow to Google Cloud |
| `JWT_SECRET_KEY` | Signs production JWTs |
| `VAPID_PRIVATE_KEY` | Signs outgoing Web Push messages |
| `VAPID_PUBLIC_KEY` | Sent to browsers when they subscribe to Web Push |
| `VAPID_SUBJECT` | Contact `mailto:`/HTTPS URL required by the Web Push protocol |
| `PUSH_CRON_SECRET` | Shared secret the Cloud Scheduler job sends as `X-Cron-Secret` to authorize `/api/internal/push/reminders` |

The workflow also creates or updates a Cloud Scheduler job (still named `nyx-push-reminders`, a pre-rename name kept because renaming it has no functional benefit) that calls that endpoint every five minutes, but only when `PUSH_CRON_SECRET` is set.

The Cloud Run runtime service account needs:

- Firestore access for users, credentials, nutrition entries, workout history, and flashcards
- `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the configured KMS key

The workflow grants that KMS role directly on the existing, legacy-named key
`projects/PROJECT_ID/locations/europe-west1/keyRings/janus-gate/cryptoKeys/user-openai-keys`
before deployment. The key ring retains its pre-rename resource ID so existing
encrypted credentials remain usable. The workflow assumes the key ring and symmetric key already exist and
does not create or rotate either one. The identity behind `GCP_SA_KEY` must be
allowed to read and update that key's IAM policy.

The deployment sets `OPENAI_MODEL`, `MISTRAL_MODEL`, `ANTHROPIC_MODEL`, and `AI_KMS_KEY_NAME`. The service still accepts the legacy `OPENAI_KMS_KEY_NAME` during migration. Shared provider API keys are not required because every user supplies their own keys.

## Project structure

Code is separated by responsibility: `routes` handles HTTP, `core` contains business rules and validation, and `services` coordinates external APIs and persistence. Finance has its own folder in each layer so its related files stay together.

```text
app.py                              Application factory and entry point
routes/
  auth.py, ai_settings.py            Shared login and AI account settings
  habits.py, nutrition.py, push.py   Aether, Nyx and reminders
  health.py                         Health check and API index
  finance/
    __init__.py                     Registers the finance blueprint
    shared.py                       Authentication gate, errors, request helpers
    connection.py                   Workbook connection and migration endpoints
    rules.py                        Rule CRUD, CSV imports and version history
    reports.py                      Sync, ledger, dashboard and other reports
    chat.py                         Ask endpoint and provider error handling
core/
  finance/
    calculations.py                 Canonical accounting and report aggregates
    sheets.py                       Ledger column/date/money parsing
    rule_engine.py                  Rule validation, matching and dry runs
    rule_csv.py                     Rule CSV interchange
    chat.py                         Read-only AI context and prompt preparation
  auth_service.py, request_auth.py   Passwords, JWTs and account identity
  habit_service.py, habit_icons.py   Habit validation, schedules and streaks
  nutrition_service.py              Nutrition validation and totals
  push_service.py                   Reminder settings and subscription validation
services/
  finance/
    sync.py                         Import orchestration and snapshot lifecycle
    connection.py                   Workbook approval and access verification
    identity.py                     Keyless reader credentials and token renewal
    sheets.py                       Read-only Google Sheets HTTP client
  firebase/
    finance/
      connections.py                Account/workbook bindings and connection state
      rules.py                      Transactional rule storage and history
    users.py, account_state.py       Account lifecycle and deletion guards
    habits.py, nutrition.py, push.py Feature persistence
    legacy_data.py, workouts.py      Historical data cleanup on account deletion
    openai_credentials.py           Stored credentials for all AI providers
    core.py, db_state.py            Firebase initialization and local stores
  firebase_service.py               Shared Firebase API used by existing apps
  ai_*.py, *_service.py              AI adapters, credentials, logging and Web Push
scripts/                            One-time provisioning and administrator tools
run_demo.py                         Synthetic Janus development harness
start_local_demo.py                 Starts the sibling Janus and Minerva demos
tests/                              Accounting, API and lifecycle regression checks
```

For a finance change, start with its endpoint under `routes/finance`, follow the calculation into `core/finance`, or the import/Google request into `services/finance`. Firestore writes belong under `services/firebase/finance`. Source workbook values and guarded legacy-data deletion remain part of the existing contracts.

## Related projects

- [Aether](https://github.com/DonalGeraghty/aether) — React frontend for habit tracking and AI-assisted habit creation
- [Minerva](https://github.com/DonalGeraghty/minerva) — React frontend for the personal finance dashboard
- [Nyx](https://github.com/DonalGeraghty/nyx) — React frontend for nutrition tracking

## Overall architecture

Janus API is the shared backend behind three independently deployed React/Vite frontends — Aether, Minerva, and Nyx. All four services run as separate Cloud Run services in the same Google Cloud project (`donal-geraghty-home`, region `europe-west1`).

```text
Aether (React/Vite, Cloud Run)   ─┐
Minerva (React/Vite, Cloud Run)  ─┼─▶ Janus API (Flask, Cloud Run) ─┬─▶ Firestore
Nyx (React/Vite, Cloud Run)      ─┘                                 │     (users, credentials, nutrition,
                                                                     │      workouts, flashcards)
                                                                     ├─▶ Cloud KMS
                                                                     │     (encrypts each user's provider key)
                                                                     ├─▶ OpenAI / Mistral AI / Anthropic
                                                                     │     (called with the user's own key)
                                                                     └─▶ Cloud Scheduler
                                                                           (POST /api/internal/push/reminders,
                                                                            every 5 minutes)
```

- Each frontend is a static Vite build served by nginx in its own container (Node build stage, then `nginx:alpine`, port `8080`, with a `/health` endpoint), deployed from its own Artifact Registry repository (`aether`, `minerva`, `nyx`) by its own `deploy-gcp.yml` GitHub Actions workflow. Those workflows build, push, then `gcloud run deploy`, preferring Workload Identity Federation with a `GCP_SA_KEY` secret as a fallback.
- Janus API deploys differently: `.github/workflows/deploy.yml` runs `gcloud run deploy --source .`, which lets Cloud Build produce the container directly from source, so there is no separate Artifact Registry push step and no Workload Identity Federation — authentication uses only the static `GCP_SA_KEY` secret.
- Every frontend points at this service via a `VITE_JANUS_API_URL` build-time variable (defaulting to the deployed Janus API URL). Because all three frontends talk to the same Janus API deployment and Firestore project, a single account's credentials, selected AI provider/model, and login session are shared across Aether, Minerva, and Nyx.
- Each frontend calls its own product endpoints (Aether → `/api/habits/*` and habit label/check-in endpoints, Nyx → `/api/nutrition/*`, Minerva → `/api/finance/*`) plus shared authentication and AI-credential endpoints. Workout and retired integration records are retained only for guarded account-deletion cleanup.
- Two pieces of infrastructure still carry pre-rename names from when this service only served Nyx: the KMS keyring `janus-gate` (kept because existing encrypted credentials are bound to its resource name) and the Cloud Scheduler job `nyx-push-reminders` (renaming it has no functional benefit, since it now dispatches reminders for every app's users).
