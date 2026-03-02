# Google Calendar Client

**A modular, type-safe Python library for Google Calendar and Tasks integration.**

This library provides a robust abstraction layer over the Google Calendar API and Google Tasks API, designed specifically for applications that require **Dependency Injection (DI)** and strict architectural separation. By decoupling the interface from the implementation, it enables developers to write testable, maintainable code without hard dependencies on external providers.

### Key Features
* **Zero-Dependency Interface:** Core logic relies only on abstract base classes (`calendar_client_api`).
* **Type-Safe:** Fully typed with modern Python hints (mypy strict compliance).
* **Injectable:** Seamlessly integrates with dependency injection patterns.

### Included Implementation (`google_calendar_client_impl`)
* **OAuth 2.0 Authentication (`auth.py`):** Built-in interactive and refresh-capable OAuth flow via `InstalledAppFlow`. It manages token generation, securely caching them locally (`token.json`), and silently refreshing them when expired.
* **Event Management (`event_impl.py`):** Robust parser for Google Calendar API payload converting complex nested JSON to a simple standard interface consisting of Start/End datetimes (UTC), Titles, Descriptions and Locations.
* **Task Management (`task_impl.py`):** Fully integrated `Google Tasks API` parser capable of coercing Google's strict constraint of RFC 3339 timestamps into the standard DateTime formats and managing Completion statuses.

## Installation

This project is managed using `uv`. To set up the environment:

```bash
# 1. Sync dependencies
uv sync

# 2. Run tests
uv run pytest
```