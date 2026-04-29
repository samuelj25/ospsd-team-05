# Calendar Client Service

This component is a FastAPI application that wraps `google_calendar_client_impl` and exposes its functionality over HTTP. It is the only component that ever imports or instantiates `GoogleCalendarClient` directly. All other consumers interact with calendar functionality through this service.

The service is deployed to Render at `https://ospsd-team-05.onrender.com`.

## Key Behaviors

- Manages OAuth 2.0 sessions via `WebOAuthManager` and session cookies.
- Provides full REST endpoints for events and tasks.
- Translates Python exceptions from `GoogleCalendarClient` into appropriate HTTP status codes.
- Exposes an OpenAPI spec at `/openapi.json` used to generate the typed API client.

## Configuration

| Environment Variable | Description | Default |
|---|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` | OAuth 2.0 Client ID from GCP Console | — |
| `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth 2.0 Client Secret from GCP Console | — |
| `OAUTH_REDIRECT_URI` | OAuth callback URL | `http://localhost:8000/auth/callback` |
| `GOOGLE_CALENDAR_ID` | Calendar ID to operate on | `primary` |

## API Reference

::: calendar_client_service.app
    options:
      show_root_heading: true
      show_source: true

::: calendar_client_service.auth_routes
    options:
      show_root_heading: true
      show_source: true

::: calendar_client_service.event_routes
    options:
      show_root_heading: true
      show_source: true

::: calendar_client_service.task_routes
    options:
      show_root_heading: true
      show_source: true

::: calendar_client_service.dependencies
    options:
      show_root_heading: true
      show_source: true

::: calendar_client_service.models
    options:
      show_root_heading: true
      show_source: true