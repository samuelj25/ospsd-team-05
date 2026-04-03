# Google Calendar Client

**A modular, type-safe Python system for Google Calendar and Tasks integration, delivered as a deployed HTTP service.**

This project provides a robust, service-oriented abstraction over the Google Calendar API and Google Tasks API. It is designed around strict architectural separation, dependency injection, and an adapter pattern that allows consumer code to remain completely unchanged whether it is talking to a local library or a remote service.

### Architecture Overview

The system is composed of five components working together:

* **`calendar_client_api`** — The abstract interface. Defines `Client`, `Event`, and `Task` base classes and a `get_client()` factory. Contains no concrete logic or provider-specific dependencies.
* **`google_calendar_client_impl`** — The concrete Google Calendar implementation. Handles OAuth 2.0 authentication, Google API communication, and JSON parsing. Consumed exclusively by the service layer.
* **`calendar_client_service`** — A FastAPI service deployed to Render that wraps `google_calendar_client_impl` and exposes its functionality over HTTP. Handles OAuth session management via session cookies.
* **`calendar_client_service_api_client`** — A typed Python HTTP client auto-generated from the service's OpenAPI spec. Provides typed functions and Pydantic models for every endpoint.
* **`calendar_client_adapter`** — A thin adapter that implements the `calendar_client_api.Client` interface by delegating to the auto-generated HTTP client. Allows callers to use the service as if it were the local library.

### Key Features

* **Zero-Dependency Interface:** Core logic relies only on abstract base classes (`calendar_client_api`).
* **Type-Safe:** Fully typed with modern Python hints (mypy strict compliance).
* **Service-Oriented:** Google Calendar functionality is exposed over HTTP via a deployed FastAPI service, decoupling consumers from the implementation entirely.
* **Adapter Pattern:** `ServiceAdapterClient` bridges the HTTP client and the abstract `Client` interface, so consumer code requires no changes when moving from library to service.
* **Injectable:** Seamlessly integrates with dependency injection patterns via the `get_client()` factory.

### Live Service

* **Base URL:** `https://ospsd-team-05.onrender.com`
* **Health Check:** `https://ospsd-team-05.onrender.com/health`
* **OpenAPI Spec:** `https://ospsd-team-05.onrender.com/openapi.json`

## Quick Start

This project is managed using `uv`. To set up the environment:

```bash
# 1. Sync dependencies
uv sync --all-packages

# 2. Run the service locally
uv run uvicorn calendar_client_service.app:app --reload --port 8000

# 3. Run tests
uv run pytest
```