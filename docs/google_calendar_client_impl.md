# Google Calendar Implementation

This component provides the concrete logic to interact with the Google Calendar API. It satisfies the `CalendarClient` interface.

## Authentication & Configuration

This client uses Google OAuth 2.0 for authentication via an `InstalledAppFlow`. It requires the following environment variables to be set:

* `GOOGLE_OAUTH_CREDENTIALS_PATH`: (Optional) Path to your Google Cloud OAuth `credentials.json` file. Defaults to `"credentials.json"` in the working directory.
* `GOOGLE_OAUTH_TOKEN_PATH`: (Optional) Path to cache the generated OAuth token. Defaults to `"token.json"`.
* `GOOGLE_CALENDAR_ID`: (Optional) The Google Calendar ID to operate on. If set, overrides the default `"primary"`.

## Implementation Details

### Authentication Module (`auth.py`)

This module handles the full OAuth 2.0 lifecycle, managing user consent, token caching, and automated token refreshes.

* `get_credentials(credentials_path: str | None = None, token_path: str | None = None) -> Credentials`
  **Detailed Behavior:** This function acts as the primary authentication boundary for the Google API. 
  1. It first attempts to load cached, authorized user credentials from the specified `token_path` (defaulting to `token.json`) using `Credentials.from_authorized_user_file`.
  2. If the loaded token exists but has expired, and a `refresh_token` is present, it silently contacts Google's authorization servers via `creds.refresh(Request())` to obtain a new access token without user intervention.
  3. If no cached token exists (e.g., on the very first run of the application), it reads the client secrets from `credentials_path` (defaulting to `credentials.json`) and launches a local web server to handle the interactive OAuth 2.0 consent flow via `InstalledAppFlow.from_client_secrets_file`. The user must click "Allow" in their browser.
  4. Finally, it persists the resulting `google.oauth2.credentials.Credentials` object back securely to the `token_path` as strictly formatted JSON. This ensures subsequent application runs are fully headless.

### Google Calendar Client (`google_calendar_impl.py`)

This module houses the `GoogleCalendarClient` which inherits from and fully implements the `calendar_client_api.Client` abstract base class. It essentially acts as a Translator and Gateway pattern between our abstract domain models and Google's specific REST structures.

#### Connection

* `__init__(calendar_id: str = "primary", tasklist_id: str = "@default", credentials_path: str | None = None, token_path: str | None = None) -> None`
  **Detailed Behavior:** Initializes the client state. Crucially, it does *not* connect to the Google APIs immediately upon instantiation. This allows the client to be safely injected and configured before any network I/O or authentication flows are triggered.
* `connect() -> None`
  **Detailed Behavior:** This is the explicit initialization step. It first overrides the target `calendar_id` if the `GOOGLE_CALENDAR_ID` environment variable is detected. It then invokes `get_credentials()` to secure a valid OAuth token. Finally, it uses the `googleapiclient.discovery.build` factory to dynamically construct and cache the actual `Resource` objects for both the Calendar (`v3`) and Tasks (`v1`) APIs. All subsequent CRUD operations route through these cached `_service` and `_tasks_service` objects.

#### Event Methods

* `get_event(event_id: str) -> calendar_client_api.Event`
  **Detailed Behavior:** Executes a `GET` request to the `events().get()` endpoint. The raw JSON response from Google, which contains deeply nested dictionaries for timestamps and metadata, is passed directly into the `GoogleCalendarEvent` constructor where it is parsed and flattened into our strictly-typed `Event` interface.
* `create_event(event: calendar_client_api.Event) -> calendar_client_api.Event`
  **Detailed Behavior:** Takes our domain `Event` object and executes the `_event_to_dict()` helper. This helper performs the inverse translation: it unwraps the Python `datetime` objects back into Google's required ISO 8601 string structure wrapped inside `{"dateTime": ..., "timeZone": ...}` dictionaries. It then issues a `POST` request via `events().insert()`.
* `update_event(event: calendar_client_api.Event) -> calendar_client_api.Event`
  **Detailed Behavior:** Acts similarly to `create_event`, but issues a `PUT` request via `events().update()`, targeting the specific `event.id`. The entire event body is replaced with the new dictionary payload.
* `delete_event(event_id: str) -> None`
  **Detailed Behavior:** Issues a `DELETE` request via `events().delete()`. Returns nothing on success; the underlying Google SDK will raise an HttpError if the event does not exist or the user lacks permissions.
* `get_events(start_time: datetime, end_time: datetime) -> Iterator[calendar_client_api.Event]`
  **Detailed Behavior:** Queries the `events().list()` endpoint, bounding the query using the `timeMin` and `timeMax` parameters formatted as ISO strings. Critically, it implements automatic pagination mapping. It enters a `while True` loop, yielding constructed `GoogleCalendarEvent` objects one by one as a Python Generator (`Iterator`), and automatically fetching the next page of results if a `nextPageToken` is present in the response payload.
* `from_raw_data(raw_data: str) -> calendar_client_api.Event`
  **Detailed Behavior:** A utility method that bypasses the network layer entirely. It takes raw JSON text (e.g., from a database cache or webhook payload) and uses the standard library `json.loads` to construct a `GoogleCalendarEvent` object directly in memory.

#### Task Methods

* `get_task(task_id: str) -> calendar_client_api.Task`
  **Detailed Behavior:** Executes a `GET` request to the `tasks().get()` endpoint on the configured `tasklist`. The response is wrapped in a `GoogleCalendarTask` object, which specifically handles translating Google's `"needsAction"` and `"completed"` string statuses into our standard boolean `is_completed` flag.
* `create_task(task: calendar_client_api.Task) -> calendar_client_api.Task`
  **Detailed Behavior:** Google Tasks has strictly different timestamp requirements than Google Calendar. The `_task_to_dict()` helper explicitly checks for Python timezone awareness, converts the time to absolute UTC, strips the timezone info, and forces the strict strictly-compliant RFC 3339 format ending in `.000Z` before issuing the `POST` via `tasks().insert()`.
* `update_task(task: calendar_client_api.Task) -> calendar_client_api.Task`
  **Detailed Behavior:** Translates the standard `Task` model back into the RFC 3339 format, specifically injecting the `task.id` back into the request body, and issues a `PUT` request via `tasks().update()`.
* `delete_task(task_id: str) -> None`
  **Detailed Behavior:** Issues a `DELETE` request via `tasks().delete()`. 
* `get_tasks(start_time: datetime, end_time: datetime) -> Iterator[calendar_client_api.Task]`
  **Detailed Behavior:** Queries the `tasks().list()` endpoint using the `dueMin` and `dueMax` parameters (ensuring the manually appended `"Z"` suffix for UTC). Like `get_events`, this provides an automatic `Iterator` that transparently handles pagination via `nextPageToken`.
* `mark_task_completed(task_id: str) -> None`
  **Detailed Behavior:** Implements a distinct "Patch" style workflow. Because the Google Tasks `update()` method requires the *entire* task body (and will overwrite omitting fields with nulls), this method first executes a `GET` request to fetch the existing task properties. It modifies only the `"status"` property to `"completed"` in the resulting dictionary, and then sends the full modified dictionary back via `tasks().update()`.

#### Registration

* `get_client_impl() -> calendar_client_api.Client`
  **Detailed Behavior:** A module-level factory function. It instantiates and returns the `GoogleCalendarClient`.
* `register() -> None`
  **Detailed Behavior:** The core Dependency Injection hook. When the wider application imports this package, calling `register()` mutates the abstract `calendar_client_api` package by forcefully overwriting its `get_client` reference to point to this module's `get_client_impl`. Ensures true decoupling.