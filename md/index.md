# Google Calendar Client

**A modular, type-safe Python library for Google Calendar and Tasks integration.**

This library provides a robust abstraction layer over the Google Calendar API and Google Tasks API, designed specifically for applications that require **Dependency Injection (DI)** and strict architectural separation. By decoupling the interface from the implementation, it enables developers to write testable, maintainable code without hard dependencies on external providers.

### Key Features
* **Zero-Dependency Interface:** Core logic relies only on abstract base classes (`calendar_client_api`).
* **Fully Implemented Provider:** Includes a concrete Google implementation (`google_calendar_client_impl`) supporting both Calendar Events and Google Tasks.
* **OAuth 2.0 Authentication:** Built-in interactive and refresh-capable OAuth flow.
* **Type-Safe:** Fully typed with modern Python hints (mypy strict compliance).
* **Injectable:** Seamlessly integrates with dependency injection patterns.

## Installation

This project is managed using `uv`. To set up the environment:

```bash
# 1. Sync dependencies
uv sync

# 2. Run tests
uv run pytest
```