# calendar_client_service

FastAPI microservice that exposes `google_calendar_client_impl` over HTTP, extended in HW3 with a Gemini-powered AI assistant, Slack integration, and OpenTelemetry observability.

## Overview

This component wraps `GoogleCalendarClient` in a REST API, enabling remote access through the Adapter Pattern. It is the only component that ever imports or instantiates `GoogleCalendarClient` directly. All other consumers interact with calendar functionality through this service over HTTP.

The service is deployed to Google Cloud Run and accessible at `https://calendar-client-service-iozhebgpyq-uc.a.run.app`.

## Structure

```
src/calendar_client_service/
├── app.py            # FastAPI app factory + TelemetryMiddleware
├── dependencies.py   # DI: get_calendar_client, get_chat_client
├── models.py         # Pydantic request/response schemas
├── auth_routes.py    # OAuth 2.0 endpoints
├── event_routes.py   # Event CRUD endpoints
├── task_routes.py    # Task CRUD endpoints
├── slack_routes.py   # /slack/events webhook (Slack + Gemini AI)
└── ai_tools.py       # Gemini tool definitions + dispatch logic
```

## Running Locally

```bash
uv run uvicorn calendar_client_service.app:app --reload --port 8000 --env-file .env
```

## Environment Variables

| Variable | Description |
|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` | OAuth client ID from GCP Console |
| `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth client secret |
| `OAUTH_REDIRECT_URI` | OAuth callback URL (default: `http://localhost:8000/auth/callback`) |
| `GEMINI_API_KEY` | Gemini / Google AI Studio API key |
| `SLACK_BOT_TOKEN` | Slack Bot OAuth token (`xoxb-…`) |
| `SLACK_SIGNING_SECRET` | Slack app signing secret |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID (enables Cloud Monitoring/Trace export) |
| `CHAT_BACKEND` | Chat backend selector (default: `"slack"`) |

## OAuth Flow

1. `GET /auth/login` — redirects user to Google consent page
2. User grants access → Google redirects to `GET /auth/callback?code=...`
3. Service exchanges code for tokens, stores session, returns `session_id` cookie
4. Subsequent requests include `session_id` cookie for authentication

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service liveness check |
| `GET` | `/auth/login` | Redirect to Google OAuth consent page |
| `GET` | `/auth/callback` | Exchange auth code for tokens, set session cookie |
| `GET` | `/auth/status` | Check if current session is authenticated |
| `POST` | `/auth/logout` | Revoke session and clear session cookie |
| `GET` | `/events` | List events in a time range |
| `GET` | `/events/{event_id}` | Fetch a single event by ID |
| `POST` | `/events` | Create a new event |
| `PUT` | `/events/{event_id}` | Replace an existing event |
| `DELETE` | `/events/{event_id}` | Delete an event |
| `GET` | `/tasks` | List tasks in a time range |
| `GET` | `/tasks/{task_id}` | Fetch a single task by ID |
| `POST` | `/tasks` | Create a new task |
| `PUT` | `/tasks/{task_id}` | Replace an existing task |
| `DELETE` | `/tasks/{task_id}` | Delete a task |
| `POST` | `/tasks/{task_id}/complete` | Mark a task as completed |
| `POST` | `/slack/events` | Slack event webhook; handles Gemini AI tool dispatch |

## Observability

The `TelemetryMiddleware` in `app.py` records two OpenTelemetry instruments per request:

| Instrument | Metric Name | Unit |
|---|---|---|
| Counter | `custom.googleapis.com/http/request_count` | `1` |
| Histogram | `custom.googleapis.com/http/request_latency` | `ms` |

Both instruments carry `route`, `method`, `status_code`, and `status_category` labels. Metrics are exported to Google Cloud Monitoring when `GOOGLE_CLOUD_PROJECT` is set; console exporters are used in local development.