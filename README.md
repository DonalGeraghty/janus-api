# Janus API

Janus API is the shared backend for three sibling frontends — [Aether](https://github.com/DonalGeraghty/aether) (workouts), [Minerva](https://github.com/DonalGeraghty/minerva) (flashcards), and [Nyx](https://github.com/DonalGeraghty/nyx) (nutrition). It provides account authentication, per-user encrypted OpenAI, Mistral AI, and Anthropic credentials, selectable AI models, structured meal and workout analysis, an AI flashcard assistant with spaced-repetition scheduling, and user-scoped data storage for all three apps.

## Responsibilities

- Register users and issue seven-day JWT access tokens
- Store password hashes rather than plaintext passwords
- Verify user-supplied OpenAI, Mistral AI, and Anthropic API keys
- Encrypt provider keys with Google Cloud KMS before persistence
- Persist each user's selected provider and model
- Analyze meal descriptions with structured responses from the selected model (Nyx)
- Create, list, update, and delete user-owned nutrition entries (Nyx)
- Generate structured meal recommendations from today's calorie and protein progress (Nyx)
- Analyze natural-language workout descriptions and manage workout history (Aether)
- Answer flashcard questions and draft reviewable flashcards with an AI assistant (Minerva)
- Create, list, update, delete, and spaced-repetition-schedule user-owned flashcards (Minerva)
- Store opt-in Web Push settings/subscriptions and dispatch local-time reminders
- Delete credentials, nutrition data, workout history, and flashcards when an account is removed
- Expose health and database-status endpoints for deployment checks

## Architecture

```text
Aether, Minerva, or Nyx (React/Vite frontends)
  └─ Janus API (Flask)
       ├─ Firestore
       │    ├─ users/{email}                          (includes minerva_settings)
       │    ├─ users/{email}/nutrition_entries/{entry}
       │    ├─ users/{email}/workout_history/{entry}
       │    ├─ users/{email}/flashcards/{card}
       │    ├─ users/{email}/flashcard_reviews/{review}
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

Create a local `.env` file:

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

When Firestore is unavailable, local authentication, profile settings, nutrition operations, and workout history fall back to process memory. That data disappears when the server restarts. AI credential storage deliberately has no plaintext or in-memory fallback: Firestore or KMS failures cause those operations to fail closed.

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
| `GET` | `/api/user/minerva-settings` | Bearer JWT | Return Minerva assistant settings (for example, whether existing cards are used as context) |
| `PUT` | `/api/user/minerva-settings` | Bearer JWT | Update Minerva assistant settings |
| `POST` | `/api/minerva/respond` | Bearer JWT | Ask the Minerva AI assistant a question or request a draft flashcard |
| `POST` | `/api/flashcards` | Bearer JWT | Create a flashcard |
| `GET` | `/api/flashcards` | Bearer JWT | List the authenticated account's flashcards |
| `GET` | `/api/flashcards/due` | Bearer JWT | List flashcards due for review |
| `PUT` | `/api/flashcards/{card_id}` | Bearer JWT | Update an owned flashcard |
| `DELETE` | `/api/flashcards/{card_id}` | Bearer JWT | Delete an owned flashcard |
| `POST` | `/api/flashcards/{card_id}/reviews` | Bearer JWT | Record a recall rating (Again/Hard/Good/Easy) and reschedule the card |
| `POST` | `/api/nutrition/analyze` | Bearer JWT | Analyze a meal without saving it |
| `POST` | `/api/nutrition/recommend` | Bearer JWT | Recommend meals for the rest of the day |
| `POST` | `/api/nutrition/entries` | Bearer JWT | Save a reviewed nutrition entry |
| `GET` | `/api/nutrition/entries` | Bearer JWT | List entries, optionally filtered by date |
| `PUT` | `/api/nutrition/entries/{entry_id}` | Bearer JWT | Replace an owned entry and recalculate totals |
| `DELETE` | `/api/nutrition/entries/{entry_id}` | Bearer JWT | Delete an owned entry |
| `POST` | `/api/workouts/analyze` | Bearer JWT | Structure a natural-language workout without saving it |
| `GET` | `/api/workouts` | Bearer JWT | List the authenticated account's workout history |
| `PUT` | `/api/workouts/{entry_id}` | Bearer JWT | Create or replace an owned workout history entry |
| `DELETE` | `/api/workouts/{entry_id}` | Bearer JWT | Delete an owned workout history entry |
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

Existing users without saved AI settings default to OpenAI and `gpt-5.6-sol`. Selecting a provider does not delete any other provider's key. Meal analysis, workout analysis, and recommendation requests never fall back silently: when the selected provider has no stored key, the API returns `409 provider_key_required`.

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

```text
.
├── core/
│   ├── auth_service.py          # Password hashing and JWT handling
│   ├── nutrition_service.py     # Nutrition-entry validation
│   ├── workout_service.py       # Workout-entry validation
│   ├── flashcard_service.py     # Flashcard validation and spaced-repetition scheduling
│   └── push_service.py          # Web Push settings/subscription validation
├── services/
│   ├── firebase/                # Firestore persistence by data type
│   ├── credential_service.py    # Cloud KMS encryption and decryption
│   ├── ai_catalog.py            # Allowlisted providers and models
│   ├── ai_contract.py           # Shared prompts and structured response schemas, including Minerva's
│   ├── ai_service.py            # Provider-neutral request dispatch
│   ├── ai_errors.py             # Shared AI error mapping
│   ├── ai_validation.py         # Shared AI response validation
│   ├── anthropic_service.py      # Anthropic key verification and meal/workout/Minerva analysis
│   ├── logging_service.py       # Console logging
│   ├── mistral_service.py       # Mistral key verification and meal/workout/Minerva analysis
│   ├── openai_service.py        # OpenAI key verification and meal/workout/Minerva analysis
│   └── web_push_service.py      # VAPID signing and Web Push dispatch
├── tests/                       # Unit and API tests
├── app.py                       # Flask application and routes
├── Dockerfile
└── requirements.txt
```

## Related projects

- [Aether](https://github.com/DonalGeraghty/aether) — React frontend for workout tracking
- [Minerva](https://github.com/DonalGeraghty/minerva) — React frontend for AI-assisted flashcards
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
- Each frontend calls the Janus API endpoints relevant to it (Aether → `/api/workouts/*`, Nyx → `/api/nutrition/*`, Minerva → `/api/minerva/*` and `/api/flashcards/*`) plus the shared `/api/auth/*` and `/api/user/*` endpoints for account and AI-credential management.
- Two pieces of infrastructure still carry pre-rename names from when this service only served Nyx: the KMS keyring `janus-gate` (kept because existing encrypted credentials are bound to its resource name) and the Cloud Scheduler job `nyx-push-reminders` (renaming it has no functional benefit, since it now dispatches reminders for every app's users).
