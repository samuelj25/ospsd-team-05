# DESIGN.md — Calendar Client Service (HW2)

## Architecture Overview

### Components

This project transforms the HW1 library-based Google Calendar client into a service-oriented architecture made up of five distinct components:

**1. `calendar_client_api` (The Interface Contract)**
The abstract base classes (`Client`, `Event`, `Task`) and exception types (`EventNotFoundError`, `TaskNotFoundError`, `CalendarOperationError`) that define the shared contract all implementations must satisfy. Nothing in this layer knows about Google, HTTP, or any concrete technology — it is purely definitional.

**2. `google_calendar_client_impl` (The Original Library Implementation)**
The concrete `GoogleCalendarClient` that implements `Client` by talking directly to the Google Calendar and Tasks REST APIs via OAuth 2.0. This component is unchanged from HW1 and is now consumed exclusively by the service layer — users never import it directly.

**3. `calendar_client_service` (The FastAPI Service)**
A FastAPI application that wraps `google_calendar_client_impl` and exposes its functionality over HTTP. It handles OAuth session management via `WebOAuthManager`, provides REST endpoints for events and tasks, and translates Python exceptions into appropriate HTTP status codes. It is the only component that ever imports or instantiates `GoogleCalendarClient`.

**4. `calendar_client_service_api_client` (The Auto-Generated HTTP Client)**
A Python client library auto-generated from the service's OpenAPI spec using `openapi-python-client`. It provides typed Python functions and models for every endpoint in the service. Consumers use this to talk to the service over HTTP without writing raw `httpx` / `requests` calls themselves.

**5. `calendar_client_adapter` (The Adapter / Shim)**
A thin adapter layer (`ServiceAdapterClient`) that implements the `calendar_client_api.Client` interface but, instead of calling Google APIs directly, delegates every method call to the auto-generated HTTP client. This is the "shim" that makes service usage look identical to library usage from the caller's perspective.

---

### Component Interaction Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              User Code                              │
│              client = get_client()                                  │
│              client.get_event("abc")                                │
└─────────────────────────────┬──────────────────────────────────────────────┘
                            │ calendar_client_api.Client interface
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   calendar_client_adapter                            │
│              ServiceAdapterClient (implements Client)                │
│  Translates Client method calls → typed HTTP client calls            │
└─────────────────────────────┬───────────────────────────────────────────────┘
                            │ HTTP (openapi-generated typed functions)
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│             calendar_client_service_api_client                       │
│         Auto-generated typed Python functions + Pydantic models      │
└─────────────────────────────┬───────────────────────────────────────────────┘
                            │ HTTP/JSON over the network
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   calendar_client_service (FastAPI)                  │
│   /events, /tasks, /auth routes  ──  WebOAuthManager  ──  session cookies │
└─────────────────────────────┬───────────────────────────────────────────────┘
                            │ Python method calls (no network)
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              google_calendar_client_impl (GoogleCalendarClient)      │
│                Google Calendar API + Google Tasks API                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Request Flow

Below is a complete trace of a `get_event("abc")` call from user code through all layers and back:

1. **User code** calls `client.get_event("abc")` on a `ServiceAdapterClient` instance (registered via `calendar_client_adapter.register()`).

2. **Adapter** (`ServiceAdapterClient.get_event`) calls the auto-generated function:
   ```python
   resp = get_event_events_event_id_get.sync(client=self._client, event_id="abc")
   ```

3. **Auto-generated client** constructs an HTTP `GET /events/abc` request with the `session_id` cookie attached and sends it to the service.

4. **FastAPI service** (`event_routes.get_event`) receives the request. The `get_calendar_client` dependency reads the `session_id` cookie, retrieves stored OAuth credentials from `WebOAuthManager`, and constructs a `GoogleCalendarClient` connected with those credentials.

5. **`GoogleCalendarClient.get_event("abc")`** is called. It issues an authenticated request to the Google Calendar REST API and returns a `GoogleCalendarEvent` object.

6. **FastAPI route** converts the `GoogleCalendarEvent` into a Pydantic `EventResponse` model and returns it as JSON with HTTP 200.

7. **Auto-generated client** deserialises the JSON into a typed `EventResponse` model object and returns it.

8. **Adapter** wraps the `EventResponse` in an `AdapterEvent` (which implements `calendar_client_api.Event`) and returns it to the caller.

9. **User code** receives an `Event` object — identical in interface to the `GoogleCalendarEvent` it received in HW1.

---

### Sample API Response

`GET /events/abc123xyz`

```json
{
  "id": "abc123xyz",
  "title": "Team Standup",
  "start_time": "2025-06-01T09:00:00+00:00",
  "end_time": "2025-06-01T09:30:00+00:00",
  "location": "Room 101",
  "description": "Daily sync"
}
```

`GET /tasks/task456`

```json
{
  "id": "task456",
  "title": "Review PR #42",
  "start_time": "2025-06-01T09:00:00+00:00",
  "end_time": "2025-06-02T00:00:00+00:00",
  "description": "Check the adapter implementation",
  "is_completed": false
}
```

`GET /auth/status` (authenticated)

```json
{
  "authenticated": true,
  "session_id": "a3f8c2d1-9b4e-4f77-832a-7e1d5a006bca"
}
```

`GET /health`

```json
{
  "status": "ok"
}
```

---

## API Design

### Endpoints

#### Health

| Method | Path      | Description            | Response               |
|--------|-----------|------------------------|------------------------|
| GET    | `/health` | Service liveness check | `200 {"status": "ok"}` |

#### Auth

| Method | Path             | Description                                         | Response                 |
|--------|------------------|-----------------------------------------------------|--------------------------|
| GET    | `/auth/login`    | Redirects browser to Google OAuth 2.0 consent page | `302` redirect to Google |
| GET    | `/auth/callback` | Exchanges auth code for tokens, sets session cookie | `200 AuthStatusResponse` |
| GET    | `/auth/status`   | Reports whether the current session is authenticated | `200 AuthStatusResponse` |
| POST   | `/auth/logout`   | Revokes session and clears session cookie           | `200 AuthStatusResponse` |

#### Events

| Method | Path                  | Description                  | Request Body                           | Response                  |
|--------|-----------------------|------------------------------|----------------------------------------|---------------------------|
| GET    | `/events`             | List events in a time range  | Query params: `start_time`, `end_time` | `200 List[EventResponse]` |
| GET    | `/events/{event_id}`  | Fetch a single event by ID   | —                                      | `200 EventResponse`       |
| POST   | `/events`             | Create a new event           | `EventCreate`                          | `201 EventResponse`       |
| PUT    | `/events/{event_id}`  | Replace an existing event    | `EventUpdate`                          | `200 EventResponse`       |
| DELETE | `/events/{event_id}`  | Remove an event              | —                                      | `204 No Content`          |

**EventCreate body:**
```json
{
  "title": "string (required)",
  "start_time": "datetime (required)",
  "end_time": "datetime (required)",
  "location": "string (optional)",
  "description": "string (optional)"
}
```

**EventUpdate body:**
```json
{
  "id": "string (required)",
  "title": "string (required)",
  "start_time": "datetime (required)",
  "end_time": "datetime (required)",
  "location": "string (optional)",
  "description": "string (optional)"
}
```

#### Tasks

| Method | Path                        | Description                  | Request Body                           | Response                 |
|--------|-----------------------------|------------------------------|----------------------------------------|--------------------------|
| GET    | `/tasks`                    | List tasks in a time range   | Query params: `start_time`, `end_time` | `200 List[TaskResponse]` |
| GET    | `/tasks/{task_id}`          | Fetch a single task by ID    | —                                      | `200 TaskResponse`       |
| POST   | `/tasks`                    | Create a new task            | `TaskCreate`                           | `201 TaskResponse`       |
| PUT    | `/tasks/{task_id}`          | Replace an existing task     | `TaskUpdate`                           | `200 TaskResponse`       |
| DELETE | `/tasks/{task_id}`          | Remove a task                | —                                      | `204 No Content`         |
| POST   | `/tasks/{task_id}/complete` | Mark a task as completed     | —                                      | `200 TaskResponse`       |

**TaskCreate body:**
```json
{
  "title": "string (required)",
  "end_time": "datetime (required)",
  "description": "string (optional)"
}
```

---

### Error Handling

The service translates errors from three sources into HTTP responses:

**FastAPI Validation Errors (422 Unprocessable Entity)**
FastAPI automatically returns 422 when a required request body field or query parameter is missing or has the wrong type. The response body is a standard `HTTPValidationError` Pydantic model listing all validation failures.

**Authentication Errors (401 Unauthorized)**
The `get_calendar_client` dependency in `dependencies.py` raises `HTTPException(401)` in two cases: no `session_id` cookie is present on the request, or the session ID is not recognized by `WebOAuthManager`. Example response:
```json
{"detail": "Not authenticated. Visit /auth/login to start the OAuth flow."}
```

**OAuth Callback Errors (400 Bad Request)**
The `/auth/callback` route wraps the token exchange in a try/except and raises `HTTPException(400)` if the code exchange fails (e.g. code already used, expired, or mismatched redirect URI):
```json
{"detail": "OAuth code exchange failed: <error from Google>"}
```

**Google API Errors**
Errors raised by `GoogleCalendarClient` (which may wrap `googleapiclient.errors.HttpError` as `CalendarOperationError`, `EventNotFoundError`, or `TaskNotFoundError`) are not explicitly caught by the route handlers. This means they currently surface as unhandled 500 responses from FastAPI — a known limitation of the current implementation. On the client side, the adapter's `_handle_error` method maps `UnexpectedStatus(404)` back to `EventNotFoundError` or `TaskNotFoundError`, and any other `UnexpectedStatus` to `CalendarOperationError`, preserving the interface's exception contract for callers.

---

## The Adapter Pattern

### Why It's Needed

The auto-generated client (`calendar_client_service_api_client`) does not implement the `calendar_client_api.Client` abstract interface. It is a collection of standalone module-level functions (e.g. `get_event_events_event_id_get.sync(...)`) and Pydantic models (`EventResponse`, `TaskResponse`, etc.) generated mechanically from the OpenAPI spec. There is no `Client` subclass anywhere in it.

Without the adapter, user code would have to change entirely when switching from the library to the service:
- It would need to import and call the generated module-level functions directly.
- It would receive Pydantic `EventResponse` objects instead of `calendar_client_api.Event` objects.
- It could not be passed to any code expecting a `Client` instance.

The adapter bridges this gap by implementing `calendar_client_api.Client` while internally delegating to the generated HTTP functions. This means the user's code is completely unchanged.

### How It Works

**Library usage (HW1):**
```python
from google_calendar_client_impl.google_calendar_impl import GoogleCalendarClient

client = GoogleCalendarClient()
client.connect()
event = client.get_event("abc")
print(event.title)  # GoogleCalendarEvent, satisfies Event interface
```

**Service usage via adapter (HW2) — identical call site:**
```python
from calendar_client_adapter.adapter import register

register(base_url="http://localhost:8000", session_id="<your-session-id>")

import calendar_client_api
client = calendar_client_api.get_client()  # returns ServiceAdapterClient
event = client.get_event("abc")
print(event.title)  # AdapterEvent, satisfies Event interface
```

Internally, `ServiceAdapterClient.get_event` does this:
```python
def get_event(self, event_id: str) -> Event:
    resp = get_event_events_event_id_get.sync(client=self._client, event_id=event_id)
    if not resp or isinstance(resp, HTTPValidationError):
        raise EventNotFoundError(f"Event {event_id} not found")
    return AdapterEvent(resp)  # wraps EventResponse in the Event interface
```

`AdapterEvent` wraps the Pydantic `EventResponse` and satisfies the `calendar_client_api.Event` abstract interface by delegating each property:
```python
class AdapterEvent(Event):
    def __init__(self, response: EventResponse) -> None:
        self._response = response

    @property
    def id(self) -> str:
        return self._response.id

    @property
    def title(self) -> str:
        return self._response.title
    # ... start_time, end_time, location, description
```

The `register()` helper patches `calendar_client_api.get_client` so that any code already using the factory function gets the service-backed client transparently:
```python
def register(base_url: str = "http://127.0.0.1:8000", session_id: str = "") -> None:
    calendar_client_api.get_client = lambda: get_client_impl(base_url, session_id)
```

---

## Testing Strategy

### What We Tested and Why

Testing was focused on verifying each layer in isolation and then verifying that the layers compose correctly. All five components have their own test suites, and there are additional cross-cutting integration and E2E tests at the repository root.

### Test Types

**Unit tests** (`components/*/tests/`)

- `calendar_client_service/tests/` — Route-level unit tests for the FastAPI service. Every endpoint (events, tasks, auth) is exercised against a `TestClient` with the `get_calendar_client` and `get_oauth_manager` dependencies overridden by `MagicMock` instances. These tests verify correct HTTP status codes, response shapes, and that the right client methods are called with the right arguments — without ever touching Google's API.

- `calendar_client_adapter/tests/test_adapter.py` — Unit tests for `ServiceAdapterClient`. The auto-generated sync functions (e.g. `get_event_events_event_id_get.sync`) are patched with `unittest.mock.patch` and return pre-built `EventResponse` / `TaskResponse` fixtures. This isolates the adapter logic (wrapping, error mapping, `AdapterEvent` / `AdapterTask` construction) from both the service and the network.

- `calendar_client_service_api_client/tests/test_smoke.py` — Smoke tests for the auto-generated client. They patch `httpx.Client.request` directly and verify that the generated endpoint functions (`health_health_get.sync`, `auth_status_auth_status_get.sync`) are importable, callable, and correctly deserialise a mocked HTTP response — confirming the generated code is structurally sound without requiring a running service.

- `google_calendar_client_impl/tests/` — Unit tests for the Google Calendar implementation. `test_google_calendar_impl.py` patches `get_credentials` and `googleapiclient.discovery.build` to verify that `connect()` and `connect_with_credentials()` construct the right service objects. `test_event_impl.py` and `test_task_impl.py` verify that `GoogleCalendarEvent` and `GoogleCalendarTask` correctly parse raw Google API dict payloads into the abstract domain model properties.

- `calendar_client_api/tests/` — Contract demonstration tests for the abstract interface. `test_calendar_client_api.py` uses `Mock(spec=Client)` / `Mock(spec=Event)` / `Mock(spec=Task)` to demonstrate and verify the expected API contracts (e.g. that `get_events` returns an iterator of `Event` objects). These serve as living documentation of what any conforming implementation must provide.

**Integration tests** (`components/calendar_client_adapter/tests/test_integration.py`, `tests/integration/`)

- `test_integration.py` (adapter) — Wires `ServiceAdapterClient` against a real in-process FastAPI `TestClient` using `httpx`'s transport injection, with `get_calendar_client` overridden to return a `MagicMock`. This validates the full adapter → HTTP → route → mock client chain without requiring a running server or live Google credentials.

- `tests/integration/test_client_integration.py` — Integration tests against the live Google APIs using real credentials (`token.json` / `credentials.json`). These verify that `GoogleCalendarClient` correctly round-trips events and tasks through the actual Google Calendar and Tasks APIs. If no credential files are found, the tests fail with an explicit message rather than being silently skipped.

- `tests/integration/test_injection.py` — Verifies that simply importing `google_calendar_client_impl` causes `GoogleCalendarClient` to register itself with `calendar_client_api.get_client()`, confirming that the dependency injection mechanism from HW1 still works correctly alongside the new service architecture.

**End-to-End tests** (`tests/e2e/`)

Full lifecycle tests marked with `@pytest.mark.e2e` that run against a live `GoogleCalendarClient` with real credentials. Each test creates a resource, verifies it, modifies it, and deletes it — confirming cleanup by asserting the resource is either a 404 `HttpError` or marked `cancelled` / `deleted` in the raw Google API response. Like the integration tests, these fail explicitly if no credentials are present on disk.

### Mocking Strategy

| Component | What Was Mocked | Why |
|---|---|---|
| Service route tests | `get_calendar_client` dependency (→ `MagicMock`) | Isolates HTTP routing and serialization logic from Google API calls; no credentials or network needed |
| Service auth route tests | `get_oauth_manager` dependency (→ `MagicMock`) | Isolates OAuth flow from real Google OAuth; avoids browser redirects in CI |
| Adapter unit tests | `get_event_events_event_id_get.sync` and other generated functions | Isolates adapter mapping logic from the HTTP client and service; fast and deterministic |
| Adapter integration tests | `get_calendar_client` dependency (→ `MagicMock`), real FastAPI `TestClient` transport | Tests the full adapter ↔ service path without a running server or real Google credentials |
| Generated client smoke tests | `httpx.Client.request` (→ `MagicMock`) | Verifies generated functions are importable and callable without a running service |
| `google_calendar_client_impl` unit tests | `get_credentials`, `googleapiclient.discovery.build` | Verifies service construction logic without real OAuth credentials or network calls |

**What was tested with real implementations:** The `tests/integration/` and `tests/e2e/` suites both use live Google API credentials and make real network calls to Google's Calendar and Tasks APIs. The E2E tests are additionally gated behind a `@pytest.mark.e2e` pytest mark so they can be selectively excluded from fast CI runs; the integration tests have no such mark and will fail explicitly if credentials are absent.

### Interface Compliance

The adapter's compliance with the `calendar_client_api.Client` interface is enforced at two levels:

**Static enforcement:** `ServiceAdapterClient` extends `calendar_client_api.client.Client` (which is an `ABC`). Python raises `TypeError` at instantiation time if any abstract method is not implemented, so it is impossible to ship an incomplete adapter without a test (or even an import) catching it immediately.

**Test-level enforcement:** The adapter integration test (`test_integration.py`) constructs a `ServiceAdapterClient`, calls `get_event` and `get_task` on it, and asserts that the returned objects satisfy the interface's property contract (`id`, `title`, `is_completed`, etc.). The unit tests in `test_adapter.py` similarly assert property values on the returned `AdapterEvent` and `AdapterTask` objects, confirming that wrapping an `EventResponse` / `TaskResponse` correctly exposes the expected interface properties. Together, these two layers — ABC instantiation and property-level assertions — ensure that `ServiceAdapterClient` is both structurally and behaviourally compliant with the `Client` contract.