# Google Calendar Implementation

This component provides the concrete logic to interact with the Google Calendar API and Google Tasks API. It implements the `calendar_client_api.Client` interface.

## Key Behaviors

- Requires an explicit `connect()` call before any API operations.
- Handles OAuth 2.0 authentication with automatic token caching and refresh.
- Supports full CRUD for both events and tasks.
- Handles pagination transparently via generators for `get_events()` and `get_tasks()`.
- Preserves existing task properties when marking tasks as completed.
- Registers itself via dependency injection on import.

## Configuration

| Environment Variable | Description | Default |
|---|---|---|
| `GOOGLE_OAUTH_CREDENTIALS_PATH` | Path to OAuth client-secrets file | `credentials.json` |
| `GOOGLE_OAUTH_TOKEN_PATH` | Path to cached token file | `token.json` |
| `GOOGLE_CALENDAR_ID` | Calendar ID to operate on | `primary` |

## API Reference

::: google_calendar_client_impl.google_calendar_impl.GoogleCalendarClient
    options:
      show_root_heading: true
      show_source: true

::: google_calendar_client_impl.auth.get_credentials
    options:
      show_root_heading: true
      show_source: true