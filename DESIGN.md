# DESIGN.md — Calendar Client Service (HW3)

## Architecture Overview

### Components

This project transforms the HW1 library-based Google Calendar client into a service-oriented architecture made up of five distinct components, extended in HW3 with AI integration, Slack support, cross-vertical chat, and full observability:

**1. `calendar_client_api` (The Interface Contract)**
The abstract base classes (`Client`, `Event`, `Task`) and exception types (`EventNotFoundError`, `TaskNotFoundError`, `CalendarOperationError`) that define the shared contract all implementations must satisfy. In HW3, `Client` now subclasses `ospsd_calendar_api.CalendarClient` from the cross-team shared API, aligning event method signatures and the `Event` dataclass across all calendar verticals. `Task`-related methods are retained as a private extension since Google Tasks is not part of the shared contract. Nothing in this layer knows about Google, HTTP, or any concrete technology — it is purely definitional.

**2. `google_calendar_client_impl` (The Original Library Implementation)**
The concrete `GoogleCalendarClient` that implements `Client` by talking directly to the Google Calendar and Tasks REST APIs via OAuth 2.0. Updated in HW3 to match the shared interface signatures (`create_event(title, start, end, description="", location=None)`, `update_event(event_id, **kwargs)`, `list_events(start, end)`). `GoogleCalendarEvent` is replaced by a `google_dict_to_event()` function returning the shared `Event` dataclass directly. This component is consumed exclusively by the service layer — users never import it directly.

**3. `calendar_client_service` (The FastAPI Service)**
A FastAPI application that wraps `google_calendar_client_impl` and exposes its functionality over HTTP. It handles OAuth session management via `WebOAuthManager`, provides REST endpoints for events and tasks, and translates Python exceptions into appropriate HTTP status codes. Extended in HW3 with `ai_tools.py` (Gemini tool definitions and dispatch logic), `slack_routes.py` (the `/slack/events` endpoint), and `TelemetryMiddleware` in `app.py` for OpenTelemetry instrumentation. It is the only component that ever imports or instantiates `GoogleCalendarClient`.

**4. `calendar_client_service_api_client` (The Auto-Generated HTTP Client)**
A Python client library auto-generated from the service's OpenAPI spec using `openapi-python-client`. It provides typed Python functions and models for every endpoint in the service. Consumers use this to talk to the service over HTTP without writing raw `httpx` / `requests` calls themselves.

**5. `calendar_client_adapter` (The Adapter / Shim)**
A thin adapter layer (`ServiceAdapterClient`) that implements the `calendar_client_api.Client` interface but, instead of calling Google APIs directly, delegates every method call to the auto-generated HTTP client. Updated in HW3: `AdapterEvent` is replaced by a function constructing the shared `Event` dataclass from `EventResponse`. This is the "shim" that makes service usage look identical to library usage from the caller's perspective.

**6. `slack_chat_adapter` (HW3 — Cross-Vertical Chat Adapter)**
A thin adapter layer (`SlackChatAdapter`) that implements the `ChatClient` ABC from `chat-client-api` (the Chat vertical's shared interface), delegating to the Slack Web API. Provides `send_message`, `get_channels`, `get_messages`, `get_message`, and `delete_message`.

---

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Slack User Message                               │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │ HTTP POST
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│            calendar_client_service  /slack/events                           │
│     Verifies Slack signature → passes text to Gemini AI agent               │
└──────────────┬──────────────────────────────────┬───────────────────────────┘
               │ Gemini tool call                  │ send_message(channel, text)
               ▼                                   ▼
┌──────────────────────────────┐   ┌───────────────────────────────────────────┐
│  ai_tools.py dispatcher      │   │       slack_chat_adapter                  │
│  (Pydantic arg validation    │   │  SlackChatAdapter → Slack Web API         │
│   → GoogleCalendarClient)    │   └───────────────────────────────────────────┘
└──────────────┬───────────────┘
               │ Python method calls
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│          google_calendar_client_impl  (GoogleCalendarClient)                │
│               Google Calendar API + Google Tasks API                        │
└─────────────────────────────────────────────────────────────────────────────┘

Consumer code path (adapter → service):

┌────────────────────────────────────────────────────────────────────────────┐
│                              User Code                                     │
│              client = get_client()                                         │
│              client.get_event("abc")                                       │
└─────────────────────────────┬──────────────────────────────────────────────┘
                              │ calendar_client_api.Client interface
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   calendar_client_adapter                                   │
│              ServiceAdapterClient (implements Client)                       │
│  Translates Client method calls → typed HTTP client calls                   │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │ HTTP (openapi-generated typed functions)
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│             calendar_client_service_api_client                              │
│         Auto-generated typed Python functions + Pydantic models             │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │ HTTP/JSON over the network
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   calendar_client_service (FastAPI)                         │
│   /events, /tasks, /auth routes  ──  WebOAuthManager  ──  session cookies  │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │ Python method calls (no network)
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              google_calendar_client_impl (GoogleCalendarClient)             │
│                Google Calendar API + Google Tasks API                       │
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

8. **Adapter** wraps the `EventResponse` in the shared `Event` dataclass (which implements `calendar_client_api.Event`) and returns it to the caller.

9. **User code** receives an `Event` object — identical in interface to the `GoogleCalendarEvent` it received in HW1.

---

### State Management

The service uses **Firestore** as a shared external data store for persistent state, resolving limitations associated with multi-instance scaling in Cloud Run.

**Session and Authentication Storage**
OAuth 2.0 sessions, OAuth state tokens, and Slack user mappings are stored in Firestore collections (`oauth_sessions`, `oauth_states`, and `slack_users`). This ensures that:
- User authentication and Slack sessions are preserved across container cold-starts and restarts.
- Multiple Cloud Run instances share a consistent view of active sessions.
- As an additional security measure, all OAuth credentials stored in Firestore are **encrypted at rest** using Google Cloud KMS (`KMS_KEY_NAME`), preventing plaintext tokens from being exposed in the database.

**In-Memory Fallbacks and Limitations**
- **Conversation History:** The service currently stores AI chat context (`_conversation_history`) in a module-level in-memory dictionary. While sessions are durable, a user's conversation history may still disappear if their next request is routed to a different Cloud Run instance or if the instance restarts. A future enhancement could move this context to Firestore as well.
- **Local Development:** When `GOOGLE_CLOUD_PROJECT` or GCP credentials are not present, the service gracefully falls back to using in-memory dictionaries for sessions and state, keeping local development seamless without requiring a live GCP database connection.

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

| Method | Path             | Description                                          | Response                 |
|--------|------------------|------------------------------------------------------|--------------------------|
| GET    | `/auth/login`    | Redirects browser to Google OAuth 2.0 consent page  | `302` redirect to Google |
| GET    | `/auth/callback` | Exchanges auth code for tokens, sets session cookie  | `200 AuthStatusResponse` |
| GET    | `/auth/status`   | Reports whether the current session is authenticated | `200 AuthStatusResponse` |
| POST   | `/auth/logout`   | Revokes session and clears session cookie            | `200 AuthStatusResponse` |

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

#### Slack / AI (HW3)

| Method | Path            | Description                                   | Response |
|--------|-----------------|-----------------------------------------------|----------|
| POST   | `/slack/events` | Slack event webhook; handles AI tool dispatch | `200`    |

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

**Service usage via adapter (HW2/HW3) — identical call site:**
```python
from calendar_client_adapter.adapter import register

register(base_url="http://localhost:8000", session_id="<your-session-id>")

import calendar_client_api
client = calendar_client_api.get_client()  # returns ServiceAdapterClient
event = client.get_event("abc")
print(event.title)  # shared Event dataclass, satisfies Event interface
```

Internally, `ServiceAdapterClient.get_event` does this:
```python
def get_event(self, event_id: str) -> Event:
    resp = get_event_events_event_id_get.sync(client=self._client, event_id=event_id)
    if not resp or isinstance(resp, HTTPValidationError):
        raise EventNotFoundError(f"Event {event_id} not found")
    return event_from_response(resp)  # constructs shared Event dataclass
```

The `register()` helper patches `calendar_client_api.get_client` so that any code already using the factory function gets the service-backed client transparently:
```python
def register(base_url: str = "http://127.0.0.1:8000", session_id: str = "") -> None:
    calendar_client_api.get_client = lambda: get_client_impl(base_url, session_id)
```

---

## Shared Vertical Contract

### Calendar Shared API

Our `calendar_client_api` aligns to the cross-team shared calendar interface agreed upon by Teams 5, 11, and 12 (April 2026) and published at `github.com/DeMoliT1on/ospsd-calendar-api`. This is declared as a `uv` git dependency:

```toml
# pyproject.toml
[tool.uv.sources]
ospsd-calendar-api = { git = "https://github.com/DeMoliT1on/ospsd-calendar-api" }
```

### Design Decisions and Rationale

The shared API was designed to be the lowest common denominator across Google Calendar (Team 5) and Outlook (Teams 11, 12). Each decision below was the result of deliberate cross-team analysis, not simply accepting defaults.

**Event fields included:**

| Field | Type | Rationale |
|---|---|---|
| `id` | `str` | Both Google and Outlook assign unique string event IDs. |
| `title` | `str` | Universal across all calendar providers. |
| `start_time` | `datetime` (tz-aware) | Both providers use timezone-aware timestamps; naive datetimes cause subtle DST bugs that are hard to detect in CI. Enforced at the model layer. |
| `end_time` | `datetime` (tz-aware) | Same rationale as `start_time`. |
| `description` | `str \| None` | Supported by both providers as optional free text. |
| `location` | `str \| None` | Supported by both providers as an optional field. |

**Fields deliberately excluded:**

- **`attendees`:** Google represents attendees as a list of email addresses with RSVP status; Outlook distinguishes between required and optional attendees with a different schema. A shared `attendees` field would have required either a lowest-common-denominator model that loses information on both sides, or a provider-specific union type that defeats the purpose of a shared interface. Exclusion keeps the contract clean and avoids silent data loss.
- **`tasks`:** Google Tasks is a separate API from Google Calendar; Outlook has no direct equivalent in its Calendar API. Forcing a shared task model would require one team to implement a no-op stub or a fundamentally different data source. Tasks are therefore a private extension of Team 5's implementation only.

**Core methods and their signatures:**

- `list_events(start, end)` — A time-range query is the only retrieval pattern supported identically by both Google Calendar and Outlook Calendar APIs without provider-specific filtering.
- `create_event(title, start, end, description="", location=None)` — Positional required fields match both APIs' minimum required payload. Optional fields use keyword arguments with safe defaults.
- `update_event(event_id, **kwargs)` — The `**kwargs` approach was chosen to allow partial updates (PATCH semantics) without requiring all fields on every call, since both Google and Outlook support partial event updates. Valid kwargs are: `title`, `start_time`, `end_time`, `description`, `location`.
- `get_event(event_id)` / `delete_event(event_id)` — Single-resource operations by ID are supported identically on both platforms.

**Known limitation — `update_event` type safety:**

The `**kwargs: Any` signature is not mypy-strict-compatible. A type-safe alternative would be a `TypedDict` or an explicit `UpdateEventParams` dataclass:

```python
class UpdateEventParams(TypedDict, total=False):
    title: str
    start_time: datetime
    end_time: datetime
    description: str | None
    location: str | None

def update_event(self, event_id: str, **kwargs: Unpack[UpdateEventParams]) -> Event: ...
```

This is a known gap in the current shared contract. For our implementation, `update_event` calls are validated at the route layer via Pydantic before reaching the client, which partially compensates. A follow-up PR to the shared API repo to introduce `Unpack[UpdateEventParams]` would fully resolve this.

**Exceptions:**

| Exception | Meaning |
|---|---|
| `CalendarError` | Base class for all calendar errors |
| `EventNotFoundError` | Event ID does not exist |
| `CalendarOperationError` | Other failures (auth, network, provider errors) |

A flat, shallow exception hierarchy was chosen deliberately: deep hierarchies encourage callers to catch too-specific exceptions and miss new subtypes. Two concrete subclasses cover all observable failure modes without over-engineering.

### Changes Made to Our Implementation

- `Client` ABC now subclasses `ospsd_calendar_api.CalendarClient` instead of defining its own event methods.
- `GoogleCalendarClient` updated to the shared method signatures.
- `GoogleCalendarEvent` replaced by `google_dict_to_event()` returning `ospsd_calendar_api.models.Event` directly.
- `AdapterEvent` replaced by a function constructing the shared `Event` dataclass from `EventResponse`.
- Shared exceptions re-exported from `ospsd_calendar_api.exceptions`.
- `Task`-related methods retained as a private extension (not part of the shared contract).

---

## Testing Strategy

### What We Tested and Why

Testing was focused on verifying each layer in isolation and then verifying that the layers compose correctly. All five components have their own test suites, and there are additional cross-cutting integration and E2E tests at the repository root.

### Test Types

**Unit tests** (`components/*/tests/`)

- `calendar_client_service/tests/` — Route-level unit tests for the FastAPI service. Every endpoint (events, tasks, auth) is exercised against a `TestClient` with the `get_calendar_client` and `get_oauth_manager` dependencies overridden by `MagicMock` instances. These tests verify correct HTTP status codes, response shapes, and that the right client methods are called with the right arguments — without ever touching Google's API.

- `calendar_client_adapter/tests/test_adapter.py` — Unit tests for `ServiceAdapterClient`. The auto-generated sync functions (e.g. `get_event_events_event_id_get.sync`) are patched with `unittest.mock.patch` and return pre-built `EventResponse` / `TaskResponse` fixtures. This isolates the adapter logic (wrapping, error mapping, shared `Event` / `Task` dataclass construction) from both the service and the network.

- `calendar_client_service_api_client/tests/test_smoke.py` — Smoke tests for the auto-generated client. They patch `httpx.Client.request` directly and verify that the generated endpoint functions (`health_health_get.sync`, `auth_status_auth_status_get.sync`) are importable, callable, and correctly deserialise a mocked HTTP response — confirming the generated code is structurally sound without requiring a running service.

- `google_calendar_client_impl/tests/` — Unit tests for the Google Calendar implementation. `test_google_calendar_impl.py` patches `get_credentials` and `googleapiclient.discovery.build` to verify that `connect()` and `connect_with_credentials()` construct the right service objects. `test_event_impl.py` and `test_task_impl.py` verify that `google_dict_to_event()` and `GoogleCalendarTask` correctly parse raw Google API dict payloads into the shared domain model properties.

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

**Test-level enforcement:** The adapter integration test (`test_integration.py`) constructs a `ServiceAdapterClient`, calls `get_event` and `get_task` on it, and asserts that the returned objects satisfy the interface's property contract (`id`, `title`, `is_completed`, etc.). The unit tests in `test_adapter.py` similarly assert property values on the returned shared `Event` and `Task` dataclass objects, confirming that wrapping an `EventResponse` / `TaskResponse` correctly exposes the expected interface properties. Together, these two layers — ABC instantiation and property-level assertions — ensure that `ServiceAdapterClient` is both structurally and behaviourally compliant with the `Client` contract.

### AI Tool Dispatch Integration Tests (VCR Cassettes)

`tests/integration/test_ai_tool_dispatch.py` exercises every calendar tool end-to-end
against a **real `GoogleCalendarClient`** backed by live Google Calendar APIs.
HTTP interactions are recorded as VCRpy cassette YAML files the first time
(`--record-mode=new_episodes`) and replayed on every subsequent run — including in CI.

Committed cassettes live in `tests/integration/cassettes/test_ai_tool_dispatch/`:

| Cassette | Covers |
|---|---|
| `TestListEvents.test_returns_serialised_event_list.yaml` | `list_events` — create + list + verify id |
| `TestListEvents.test_far_future_range_returns_empty_list.yaml` | `list_events` — empty range |
| `TestCreateEvent.test_returns_id_and_title.yaml` | `create_event` — title/id in response |
| `TestCreateEvent.test_description_defaults_to_empty_string.yaml` | `create_event` — description default |
| `TestGetEvent.test_returns_correct_fields.yaml` | `get_event` — field round-trip |
| `TestGetEvent.test_nonexistent_event_returns_not_found.yaml` | `get_event` — `not_found` error category |
| `TestDeleteEvent.test_confirms_removal_and_event_is_gone.yaml` | `delete_event` — removal + verification |

To re-record cassettes with fresh credentials:
```bash
uv run pytest tests/integration/test_ai_tool_dispatch.py --record-mode=new_episodes
```

### Tool Argument Validation (Pydantic Schemas)

Each AI tool's argument payload is validated at the dispatch boundary using Pydantic
`BaseModel` schemas defined in `ai_tools.py` (e.g. `_ListEventsArgs`, `_CreateEventArgs`).
`model_validate(args)` is called before any field access so that:

- **Required fields** that are absent produce a `ValidationError` → `{"error_category": "invalid_argument"}` `ToolResult` rather than a bare `KeyError`
- **Type coercion** (e.g. ISO 8601 string → `datetime`) happens inside Pydantic rather than via raw `datetime.fromisoformat` calls, providing standardised error messages
- **Optional fields** (e.g. `description`, `location`) have explicit defaults, avoiding `None` surprises downstream

---

## Cross-Vertical Integration

### Chat Vertical Shared API

This project consumes the Chat vertical's published shared API (`chat-client-api`) as
a declared dependency. The dependency is a **git source** pointing to the other team's
shared API repository:

```toml
# components/slack_chat_adapter/pyproject.toml
[project]
dependencies = ["chat-client-api", "slack-sdk>=3.27.0"]

[tool.uv.sources]
chat-client-api = { git = "https://github.com/HarshithKoriRaj/Shared-API" }
```

`SlackChatAdapter` implements the `ChatClient` ABC exported by `chat-client-api`,
providing `send_message`, `get_channels`, `get_messages`, `get_message`, and
`delete_message` over the Slack Web API.

### Chat Backend Swappability

The calendar service is designed so that the chat backend (Slack, Discord, etc.) can be
swapped **without changing any route code**. The `get_chat_client()` factory in
`calendar_client_service/dependencies.py` selects the backend at startup via the
`CHAT_BACKEND` environment variable (default: `"slack"`):

```python
def get_chat_client() -> ChatClient:
    backend = os.environ.get("CHAT_BACKEND", "slack")
    if backend == "slack":
        return SlackChatAdapter()
    msg = f"Unknown CHAT_BACKEND: {backend!r}"
    raise RuntimeError(msg)
```

All route handlers (`slack_routes.py`) depend on `get_chat_client` via FastAPI DI and
only ever call `chat_client.send_message(channel_id, text)` through the abstract
`ChatClient` interface. To add a Discord backend, only this factory needs to change —
no route code is touched.

---

## Observability

### OpenTelemetry → GCP Cloud Monitoring

The service is instrumented with OpenTelemetry and exports metrics to Google Cloud
Monitoring (and traces to Cloud Trace) when `GOOGLE_CLOUD_PROJECT` is set.
Console exporters are used in local development.

The `TelemetryMiddleware` in `app.py` records two instruments per request:

| Instrument | Name | Unit |
|---|---|---|
| Counter | `custom.googleapis.com/http/request_count` | `1` |
| Histogram | `custom.googleapis.com/http/request_latency` | `ms` |

### Metric Labels

Both instruments carry the following labels on every data point:

| Label | Values | Purpose |
|---|---|---|
| `route` | `/events`, `/tasks`, `/slack/events`, `/health`, … | Per-endpoint breakdown |
| `method` | `GET`, `POST`, `PUT`, `DELETE` | HTTP verb breakdown |
| `status_code` | `200`, `404`, `500`, … | Exact HTTP status |
| `status_category` | `success`, `domain_error`, `infra_error` | Error tier breakdown |

### Error Category Breakdown

`status_category` uses three tiers to separate business-logic errors from
infrastructure failures — matching the rubric's requirement:

| Category | HTTP Range | Meaning |
|---|---|---|
| `success` | 1xx – 3xx | Request handled correctly |
| `domain_error` | 4xx | Expected business-logic error (not found, bad request, unauthorised) |
| `infra_error` | 5xx | Unexpected server-side failure |

This split allows dashboards and alerts to distinguish between user-facing errors
(should be handled gracefully) and infrastructure problems (require on-call attention).

### IAM Roles (provisioned via Terraform)

| Role | Purpose |
|---|---|
| `roles/cloudtrace.agent` | Write traces to Cloud Trace |
| `roles/monitoring.metricWriter` | Write custom metrics to Cloud Monitoring |
