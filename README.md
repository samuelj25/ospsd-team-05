# Google Calendar Client: A Component-Based Calendar Integration

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A modular, type-safe Python system for interacting with Google Calendar and Google Tasks, extended in HW3 with a Gemini-powered AI assistant, Slack integration, cross-vertical chat support, and full observability via OpenTelemetry and Google Cloud Monitoring.

## Team

**Team 5**

- **Samuel Jimenez Canizal** (`sj3906`)
- **Luis Lazo** (`ll4955`)
- **Jonathan Meneses Barraza** (`jem9707`)
- **Dhruv Topiwala** (`dmt9779`)
- **Vijay Gottipati** (`vg2571`)

---

## HW3 Architecture Overview

HW3 extends the HW2 service-oriented calendar architecture with three major additions:

### 1. AI Integration (Gemini Tool-Calling Agent)

The service now embeds a Gemini-powered conversational AI agent that can answer natural-language questions about a user's calendar and tasks. The agent is exposed via a `/slack/events` endpoint and dispatches structured tool calls to the existing `GoogleCalendarClient` methods.

- **Model:** Gemini (via `GEMINI_API_KEY`)
- **Tool dispatch:** Each calendar operation (`list_events`, `create_event`, `get_event`, `delete_event`) is registered as a Gemini function-call tool. The agent selects the appropriate tool, the service validates arguments with Pydantic schemas, and results are serialised back to the model.
- **Conversation history:** Per-user conversation turns are stored in-process (see state management note in DESIGN.md).
- **Error handling:** Tool errors produce structured `ToolResult` responses with `error_category` fields (`invalid_argument`, `not_found`, `infra_error`) rather than bare exceptions.

### 2. Cross-Vertical Integration (Chat / Slack)

The calendar service integrates with the **Chat vertical's shared `chat-client-api`** interface, making the chat backend swappable at runtime.

- **Shared interface consumed:** `chat-client-api` from `github.com/HarshithKoriRaj/Shared-API`
- **Adapter implemented:** `SlackChatAdapter` implements the `ChatClient` ABC, delegating to the Slack Web API.
- **Swappability:** The `get_chat_client()` factory in `dependencies.py` selects the backend via the `CHAT_BACKEND` environment variable (default: `"slack"`). No route code changes when the backend is swapped.
- **Shared calendar interface:** Our `calendar_client_api` now subclasses `ospsd_calendar_api.CalendarClient` from the cross-team shared API at `github.com/DeMoliT1on/ospsd-calendar-api` (agreed upon by Teams 5, 11, 12). The contract covers the five core event methods and a minimal `Event` dataclass. Fields like `attendees` and `tasks` were deliberately excluded because Google and Outlook model them incompatibly — see DESIGN.md for the full rationale.

### 3. Observability (OpenTelemetry → GCP Cloud Monitoring)

Every HTTP request is instrumented via `TelemetryMiddleware` in `app.py`:

| Instrument | Metric Name | Unit |
|---|---|---|
| Counter | `custom.googleapis.com/http/request_count` | `1` |
| Histogram | `custom.googleapis.com/http/request_latency` | `ms` |

Labels on every data point: `route`, `method`, `status_code`, `status_category` (`success` / `domain_error` / `infra_error`).

Traces are exported to **Google Cloud Trace**. Console exporters are used in local development when `GOOGLE_CLOUD_PROJECT` is not set.

**Telemetry dashboard:** Google Cloud Monitoring — project `ospsd-team-05` → Metrics Explorer → filter by `custom.googleapis.com/http/`.

---

## Architectural Philosophy

- **Interface-Implementation Separation:** Every operation is defined by an abstract contract (ABC) and fulfilled by a concrete implementation.
- **Service-Oriented:** The Google Calendar implementation is wrapped in a deployed FastAPI service; consumers interact over HTTP.
- **Adapter Pattern:** Thin adapters implement abstract interfaces while delegating to concrete transports (HTTP client, Slack SDK).
- **Component-Based Design:** Each component is a self-contained, installable Python package.

---

## Core Components

The project is a `uv` workspace containing five packages plus the new HW3 additions:

1. **`calendar_client_api`** — Abstract `Client`, `Event`, and `Task` base classes (now aligned to `ospsd_calendar_api.CalendarClient`).
2. **`google_calendar_client_impl`** — `GoogleCalendarClient` backed by Google Calendar and Tasks REST APIs.
3. **`calendar_client_service`** — FastAPI service exposing events, tasks, Slack/AI, and auth endpoints.
4. **`calendar_client_service_api_client`** — Auto-generated typed Python HTTP client from the OpenAPI spec.
5. **`calendar_client_adapter`** — `ServiceAdapterClient` shim implementing `Client` over the HTTP client.
6. **`slack_chat_adapter`** *(HW3)* — `SlackChatAdapter` implementing the shared `ChatClient` interface.

---

## Project Structure

```
ospsd-team-05/
├── components/
│   ├── calendar_client_api/              # Abstract interface (aligned to shared API)
│   ├── google_calendar_client_impl/      # Google Calendar + Tasks implementation
│   ├── calendar_client_service/          # FastAPI service (events, tasks, Slack/AI, auth)
│   │   └── src/calendar_client_service/
│   │       ├── app.py                    # FastAPI app factory + TelemetryMiddleware
│   │       ├── ai_tools.py               # Gemini tool definitions + dispatch logic
│   │       ├── slack_routes.py           # /slack/events endpoint (Slack + AI)
│   │       ├── dependencies.py           # DI: get_calendar_client, get_chat_client
│   │       ├── event_routes.py           # Event CRUD
│   │       └── task_routes.py            # Task CRUD
│   ├── calendar_client_service_api_client/  # Auto-generated HTTP client
│   ├── calendar_client_adapter/          # Adapter: Client interface → HTTP client
│   └── slack_chat_adapter/              # Adapter: ChatClient interface → Slack SDK
├── infra/                                # Terraform IaC (Cloud Run, Secret Manager, IAM)
├── tests/
│   ├── integration/                      # Component integration tests (incl. VCR cassettes)
│   └── e2e/                              # End-to-end tests against live Google APIs
├── docs/                                 # MkDocs documentation source
├── Dockerfile                            # Container for Cloud Run deployment
├── pyproject.toml                        # Root workspace config
└── mkdocs.yml                            # Documentation config
```

---

## Live Service

| Endpoint | URL |
|---|---|
| **Base URL** | `https://calendar-client-service-iozhebgpyq-uc.a.run.app` |
| **Health check** | `https://calendar-client-service-iozhebgpyq-uc.a.run.app/health` |
| **OpenAPI spec** | `https://calendar-client-service-iozhebgpyq-uc.a.run.app/openapi.json` |
| **Slack events** | `https://calendar-client-service-iozhebgpyq-uc.a.run.app/slack/events` |

---

## Deployment & IaC

- **Platform:** Google Cloud Run (`us-central1`)
- **IaC:** Terraform (`infra/`). Provisions Cloud Run, a dedicated service account, Secret Manager secrets, and observability IAM roles (`roles/cloudtrace.agent`, `roles/monitoring.metricWriter`).
- **CI/CD:** CircleCI — lint → type-check → unit → integration → e2e → Docker build/push → Terraform deploy. Deploys automatically on the `hw3` branch.

### IaC Bootstrap

```bash
# Authenticate
gcloud auth application-default login

# Set your project
gcloud config set project <GCP_PROJECT_ID>

# Initialise and apply Terraform
terraform -chdir=infra init
terraform -chdir=infra apply \
  -var="project_id=<GCP_PROJECT_ID>" \
  -var="region=us-central1" \
  -var="service_name=calendar-client-service" \
  -var="image_url=<IMAGE_URL>" \
  -var="enable_service=true"
```

Secrets are managed exclusively through Google Secret Manager — never stored in version control.

---

## Project Setup

### Prerequisites

- Python 3.11+
- `uv` — fast Python package manager

### Local Setup

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone
git clone https://github.com/samuelj25/ospsd-team-05.git
cd ospsd-team-05

# 3. Sync all packages
uv sync --all-packages

# 4. Run locally
uv run uvicorn calendar_client_service.app:app --reload --port 8000 --env-file .env
```

### Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Gemini / Google AI Studio API key |
| `SLACK_BOT_TOKEN` | Slack Bot OAuth token (`xoxb-…`) |
| `SLACK_SIGNING_SECRET` | Slack signing secret |
| `GOOGLE_OAUTH_CLIENT_ID` | OAuth 2.0 Client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth 2.0 Client Secret |
| `OAUTH_REDIRECT_URI` | OAuth callback URL (default: `http://localhost:8000/auth/callback`) |
| `GCP_CREDENTIALS_JSON_BASE64` | Base64-encoded `credentials.json` |
| `GCP_TOKEN_JSON_BASE64` | Base64-encoded `token.json` |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID (enables Cloud Monitoring/Trace export) |
| `CHAT_BACKEND` | Chat backend selector (default: `"slack"`) |

---

## Development Workflow

```bash
# Lint & format
uv run ruff check .

# Type checking
uv run mypy --strict .

# All tests with coverage
uv run pytest

# Docs site (local preview)
uv run mkdocs serve
```

## Testing

- **Unit tests** (`components/*/tests/`): Fast, isolated, mocked dependencies.
- **Integration tests** (`tests/integration/`): Full adapter→service chain with VCR cassettes for AI tool dispatch.
- **E2E tests** (`tests/e2e/`): Full lifecycle against live Google APIs with real credentials.

Coverage thresholds are enforced in CI and results are reported to the CircleCI dashboard.

---

## Documentation

MkDocs documentation is configured in `mkdocs.yml` and covers all components including HW3 additions. Build and serve locally:

```bash
uv run mkdocs serve   # http://127.0.0.1:8000
uv run mkdocs build   # static site in site/
```
