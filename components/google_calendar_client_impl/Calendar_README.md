# Google Calendar Client Implementation

This package (`google-calendar-client-impl`) provides the complete, production-ready, concrete Google Calendar and Google Tasks implementation satisfying the abstract `calendar-client-api` interface contract. 

### Architecture & Design Philosophy

The primary architectural goal of this component is **Strict Decoupling via Dependency Injection**. 
* The rest of the application should *never* import or instantiate `googleapiclient` classes, nor should it see Google-specific JSON structures or authentication logic. 
* By importing this package and executing its `register()` function at startup, this component binds the `GoogleCalendarClient` into the abstract factory. The broader application only programs against the generic `Event` and `Task` interfaces, making it highly testable and agnostic to the backend calendar provider.

### Core Responsibilities

This implementation manages three distinct boundaries:
1. **Authentication (`auth.py`)**: Seamlessly manages the OAuth 2.0 InstalledAppFlow, token generation, isolated disk caching (`token.json`), and automatic background token refreshes without user intervention.
2. **REST Translation (`google_calendar_impl.py`)**: Responsible for routing simple, standardized pythonic CRUD calls into the deeply nested Google Calendar `v3` and Google Tasks `v1` API endpoints utilizing `googleapiclient.discovery.build` service proxies.
3. **Data Translation (`event_impl.py`, `task_impl.py`)**: Handles the complex edge cases of Google's specific REST schemas. This includes standardizing erratic timestamp formats (like enforcing RFC 3339 for tasks or `date` vs `dateTime` all-day objects) securely back into timezone-aware UTC Python `datetime` objects.

## Dependencies

This implementation strictly isolates the following heavy Google Python SDKs (as defined in `pyproject.toml`):
* `google-api-python-client` (>=2.177.0): Handles the low-level HTTP routing and REST interface building mapping to Google Services.
* `google-auth` (>=2.40.3): Provides the core `Credentials` objects.
* `google-auth-oauthlib` (>=1.2.2): Provides the `InstalledAppFlow` enabling the browser-based interactive consent dialog.

It explicitly maps to the abstract interface from:
* `calendar-client-api` (Local Workspace Dependency)

## Development and Testing

This component uses `pytest` and `pytest-mock` for testing. 

You can run the tests using `uv` from the component root or the workspace root:

```bash
uv run pytest components/google_calendar_client_impl/
```

### Test Coverage & Strategy

The testing strategy is built on `pytest` and `pytest-mock` utilizing rigorous `unittest.mock.patch` boundaries to perfectly isolate logic execution natively, preventing real network calls or UI browser popups during CI/CD execution.

#### 1. Authentication (`test_auth.py`)
Provides isolation for the complete OAuth 2.0 flow securely using the local filesystem:
* **Cached Valid Tokens**: Validates that reading `token.json` successfully returns valid proxy mocked `google.oauth2.credentials.Credentials`.
* **Expired Token Refresh Flow**: Specifically mocks `creds.refresh` to test the background-silent-refresh mechanism triggered when tokens expire but refresh tokens persist.
* **First-Time Sign In (`InstalledAppFlow`)**: Stubs out the `run_local_server` blocking call to verify that the initial browser consent flow correctly writes the resulting token payload to the disk safely.
* **Environment Fallbacks**: Patches `os.environ` to prove `get_credentials` overrides `token.json` defaults intelligently.

#### 2. Event Models (`test_event_impl.py`)
Mocks exact, deeply-nested Google API JSON Dictionary representations to validate the data parsing logic inside `GoogleCalendarEvent`:
* **Model Property Safety**: Validates all strictly typed properties (`id`, `title`, `start_time`, `end_time`) accurately map, and validates optional data handles nulls cleanly (`location`, `description`).
* **All-Day Events (`date` versus `dateTime`)**: Injects mock events featuring only `date` fields instead of `dateTime` to ensure the timezone is explicitly aligned to `UTC` with `time.min`.
* **Input Validation Constraints**: Confirms that missing strict constraints (like missing `id` or missing `start` block) adequately raise `TypeError` and strictly reject corrupted formatting.

#### 3. Task Models (`test_task_impl.py`)
Mocks the strict RFC 3339 requirements for Google Tasks:
* **Task Constraints**: Proves tasks are successfully initialized whether loaded directly from memory via string formats or dictionaries.
* **Standard Date Matching (`updated` versus `due`)**: Tracks Google's divergence of formats by testing fallbacks from missing `updated` fields strictly onto standard `due` timestamps.
* **Status Mappings**: Confirms string mappings `needsAction` translates directly to standard interface parameter `is_completed=False` and `completed` mapped to `True`.

#### 4. Calendar Client Logic (`test_google_calendar_impl.py`)
Tests the actual core translation layer by deeply patching the `googleapiclient.discovery.Resource` methods and `googleapiclient.discovery.build` factories:
* **Initialization (`connect()`)**: Stubs the dynamic build requests to ensure connections appropriately assign custom IDs (`CUSTOM_GROUP@calendar...`).
* **CRUD Service Boundaries (Events & Tasks)**: Hooks the `execute()` response of mocked nested service definitions (`mock_service.events.insert.return_value.execute.return_value`) returning fake Google-like payload dictionaries dictating whether translation occurs precisely for `.list()`, `.update()`, `.insert()`.
* **Patch Logic (`mark_task_completed()`)**: Proves that the update logic explicitly issues a `.get()` to pull dependencies first, manipulates only `status='completed'`, then accurately injects full JSON back into the `.update()` network boundary.

#### 5. Integration Validation (`integration/test_injection.py`)
This tiny runtime integration test confirms that explicitly importing `google_calendar_client_impl` appropriately invokes the module's target `register()` script automatically, successfully overriding the abstract `calendar_client_api.get_client()` factory with the class footprint of `GoogleCalendarClient` proving dependency injection behaves perfectly.

Code coverage is strictly enforced (`fail_under = 80`), with a current threshold configured in `[tool.coverage.report]` within `pyproject.toml`.

## Code Quality

This component enforce strict type hinting with `mypy` and linting with `ruff` to ensure high code quality and consistency.
