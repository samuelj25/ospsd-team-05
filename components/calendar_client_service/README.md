# calendar_client_service

FastAPI microservice that exposes the `google_calendar_client_impl` over HTTP.

## Overview

This component wraps the `GoogleCalendarClient` in a REST API, enabling remote
access through the Adapter Pattern described in HW2.

## Structure

```
src/calendar_client_service/
├── app.py            # FastAPI app factory
├── dependencies.py   # DI: session-aware GoogleCalendarClient
├── models.py         # Pydantic request/response schemas
├── auth_routes.py    # OAuth 2.0 endpoints (IMPLEMENTED)
├── event_routes.py   # Event CRUD endpoints (placeholder)
└── task_routes.py    # Task CRUD endpoints (placeholder)
```

## Running Locally

```bash
uv run uvicorn calendar_client_service.app:app --reload --port 8000
```

## Environment Variables

| Variable | Description |
|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` | OAuth client ID from GCP Console |
| `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth client secret |
| `OAUTH_REDIRECT_URI` | OAuth callback URL (default: `http://localhost:8000/auth/callback`) |
| `GOOGLE_CALENDAR_ID` | Calendar ID to operate on (default: `primary`) |

## OAuth Flow

1. `GET /auth/login` — redirects user to Google consent page
2. User grants access → Google redirects to `GET /auth/callback?code=...`
3. Service exchanges code for tokens, stores session, returns `session_id` cookie
4. Subsequent requests include `session_id` cookie for authentication

## Endpoints

| Method | Path | Status |
|---|---|---|
| `GET` | `/health` | ✅ Implemented |
| `GET` | `/auth/login` | ✅ Implemented |
| `GET` | `/auth/callback` | ✅ Implemented |
| `GET` | `/auth/status` | ✅ Implemented |
| `GET/POST/PUT/DELETE` | `/events/*` | 🔲 Placeholder |
| `GET/POST/PUT/DELETE` | `/tasks/*` | 🔲 Placeholder |
