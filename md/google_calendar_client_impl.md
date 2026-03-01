# Google Calendar Implementation

This component provides the concrete logic to interact with the Google Calendar API. It satisfies the `CalendarClient` interface.

## Authentication & Configuration

This client uses Google OAuth 2.0 for authentication via an `InstalledAppFlow`. It requires the following environment variables to be set:

* `GOOGLE_OAUTH_CREDENTIALS_PATH`: (Optional) Path to your Google Cloud OAuth `credentials.json` file. Defaults to `"credentials.json"` in the working directory.
* `GOOGLE_OAUTH_TOKEN_PATH`: (Optional) Path to cache the generated OAuth token. Defaults to `"token.json"`.
* `GOOGLE_CALENDAR_ID`: (Optional) The Google Calendar ID to operate on. If set, overrides the default `"primary"`.

## Implementation Details

### Google Calendar Client
::: google_calendar_client_impl.google_calendar_impl
    options:
      show_root_heading: true
      show_source: true

### Authentication Module
::: google_calendar_client_impl.auth
    options:
      show_root_heading: true
      show_source: true

### Event Implementation
::: google_calendar_client_impl.event_impl
    options:
      show_root_heading: true
      show_source: true

### Task Implementation
::: google_calendar_client_impl.task_impl
    options:
      show_root_heading: true
      show_source: true