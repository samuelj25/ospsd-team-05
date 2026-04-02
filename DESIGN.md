# Design Document

## Overview

This document describes the architectural design of the Google Calendar Client project. The system provides a modular, type-safe Python library for interacting with Google Calendar and Google Tasks through a clean abstraction layer.

## Goals

- Provide a simple, minimal interface for calendar and task operations that hides provider-specific complexity.
- Enable swapping the underlying provider (Google Calendar) without changing consumer code.
- Ensure testability at every layer through dependency injection and mockable abstractions.
- Enforce strict type safety and code quality through automated tooling.

## Architectural Overview

```
┌─────────────────────────────────────────────────────┐
│                   Consumer Code                     │
│         (imports calendar_client_api only)          │
└──────────────────────┬──────────────────────────────┘
                       │ get_client()
                       ▼
┌─────────────────────────────────────────────────────┐
│              calendar_client_api                    │
│                                                     │
│  Client (ABC)    Event (ABC)    Task (ABC)          │
│  get_client()    Exceptions                         │
└──────────────────────┬──────────────────────────────┘
                       │ dependency injection
                       ▼
┌─────────────────────────────────────────────────────┐
│          google_calendar_client_impl                │
│                                                     │
│  GoogleCalendarClient    GoogleCalendarEvent        │
│  GoogleCalendarTask      auth (OAuth 2.0)           │
│  register()                                         │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / REST
                       ▼
┌─────────────────────────────────────────────────────┐
│          Google Calendar API / Tasks API            │
└─────────────────────────────────────────────────────┘
```

## Component Design

### 1. calendar_client_api (Interface)

This component defines the abstract contracts that all implementations must satisfy. It contains zero concrete logic and has no external dependencies.

**Modules:**

- **`client.py`** — The `Client` ABC defines twelve abstract methods covering event CRUD (`get_event`, `create_event`, `update_event`, `delete_event`, `get_events`, `from_raw_data`) and task CRUD (`get_task`, `create_task`, `update_task`, `delete_task`, `get_tasks`, `mark_task_completed`). A module-level `get_client()` factory function serves as the injection point.
- **`event.py`** — The `Event` ABC defines six read-only properties: `id`, `title`, `start_time`, `end_time`, `location`, and `description`.
- **`task.py`** — The `Task` ABC defines six read-only properties: `id`, `title`, `start_time`, `end_time`, `description`, and `is_completed`.
- **`exceptions.py`** — A hierarchy of custom exceptions: `CalendarError` (base), `EventNotFoundError`, `TaskNotFoundError`, and `CalendarOperationError`.

**Design decisions:**

- The interface is deliberately small. Consumers only need to understand these abstractions to use any calendar provider.
- `Event` and `Task` are separate ABCs rather than a single base class because they have fundamentally different semantics (events have location; tasks have completion status).
- The factory function `get_client()` raises `NotImplementedError` by default, which makes it immediately obvious if no implementation has been registered.

### 2. google_calendar_client_impl (Implementation)

This component provides the concrete Google Calendar and Google Tasks integration. It depends on `calendar_client_api` and the Google API client libraries.

**Modules:**

- **`google_calendar_impl.py`** — `GoogleCalendarClient` implements all twelve `Client` methods. It requires an explicit `connect()` call to authenticate and build API service objects. Event and task listing methods handle pagination automatically. All methods that require a connection raise `CalendarOperationError` if called before `connect()`.
- **`event_impl.py`** — `GoogleCalendarEvent` accepts raw Google Calendar API JSON (as a `dict` or JSON string) and parses it into the `Event` contract. It handles both timed events (`dateTime`) and all-day events (`date`), validates required fields (`id`, `start`, `end`), and defaults missing `summary` to `"(No Title)"`.
- **`task_impl.py`** — `GoogleCalendarTask` accepts raw Google Tasks API JSON and parses it into the `Task` contract. It uses `due` for end time, falls back to `due` for start time when `updated` is absent, maps `notes` to `description`, and derives completion status from the `status` field.
- **`auth.py`** — Manages the full OAuth 2.0 lifecycle: loading cached tokens, refreshing expired tokens, running the interactive consent flow, and persisting tokens. Paths are configurable via constructor arguments or environment variables.
- **`__init__.py`** — Imports and calls `register()`, which replaces `calendar_client_api.get_client` with the concrete factory. This means importing the package is sufficient to inject the implementation.

**Design decisions:**

- Raw JSON parsing lives in the data objects (`GoogleCalendarEvent`, `GoogleCalendarTask`) rather than in the client. This mirrors how the Google API returns structured JSON that needs provider-specific interpretation, and keeps the parsing logic colocated with the data it produces.
- The client requires an explicit `connect()` step rather than connecting in the constructor. This separates object creation from side effects (network I/O, OAuth flow) and makes the client easier to test and configure.

## Dependency Injection

The DI mechanism is intentionally simple — no framework, just function reassignment:

1. `calendar_client_api.client` defines `get_client()` as a function that raises `NotImplementedError`.
2. `google_calendar_client_impl.__init__` calls `register()`, which reassigns `calendar_client_api.get_client` to point to `get_client_impl()`.
3. Consumer code imports the implementation package once (triggering registration), then exclusively uses the interface.

```python
import google_calendar_client_impl  # registers itself

from calendar_client_api import get_client

client = get_client()
client.connect()
```

This approach was chosen over alternatives (like entry points or a service locator) for its simplicity and explicitness. The trade-off is that the consumer must import the implementation package at least once, but this makes the dependency visible rather than hidden.

## Data Flow

### Event Retrieval

```
Consumer calls client.get_event("event_123")
    → GoogleCalendarClient calls Google Calendar API
    → API returns JSON dict: {"id": "event_123", "summary": "Meeting", "start": {...}, ...}
    → GoogleCalendarEvent parses the dict, validates fields, converts datetimes
    → Consumer receives an Event object with typed properties
```

### Task Completion

```
Consumer calls client.mark_task_completed("task_456")
    → GoogleCalendarClient fetches existing task properties (preserves title, etc.)
    → Sets status to "completed"
    → Calls Google Tasks API update
```

## Authentication Flow

```
get_credentials() called
    ├── token.json exists and valid? → return cached credentials
    ├── token.json exists but expired? → refresh silently → persist → return
    └── no token.json? → launch browser OAuth flow → persist token.json → return
```

Credential resolution priority: environment variables → `token.json` → `credentials.json` (interactive fallback).

## Error Handling Strategy

- **Interface level**: Custom exceptions (`CalendarError` hierarchy) provide a provider-agnostic error contract.
- **Implementation level**: `CalendarOperationError` is raised when methods are called before `connect()`. Raw API errors from Google propagate naturally.
- **Data object level**: `TypeError` for missing required fields (`id`, `start`, `end`, `title`, `due`). `ValueError` for unparseable JSON or invalid datetime formats.

## Testing Strategy

The project uses a three-tier testing approach:

- **Unit tests** verify individual components in isolation. External APIs are mocked. These tests are fast, deterministic, and form the bulk of the test suite.
- **Integration tests** verify that dependency injection works correctly — importing the implementation package causes `get_client()` to return a `GoogleCalendarClient` instance.
- **End-to-end tests** run complete workflows against real Google APIs to validate that everything works in production conditions.

Coverage is enforced at 85% with `# pragma: no cover` for intentionally untestable lines (e.g., `raise NotImplementedError` in ABCs).

## Future Considerations

- Additional providers (Outlook, Apple Calendar) can be added as new implementation packages without modifying the interface or existing implementation.
- The `Client` ABC could be extended with batch operations or webhook support as requirements evolve.
- A service locator or entry-point-based discovery mechanism could replace manual import-based DI if the number of implementations grows.