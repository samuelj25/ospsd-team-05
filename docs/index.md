# Google Calendar Client

**A modular, type-safe Python system for Google Calendar and Tasks integration, delivered as a deployed HTTP service with AI assistant and Slack support.**

This project provides a robust, service-oriented abstraction over the Google Calendar API and Google Tasks API. It is designed around strict architectural separation, dependency injection, and an adapter pattern that allows consumer code to remain completely unchanged whether it is talking to a local library or a remote service.

HW3 extends the architecture with a Gemini-powered conversational AI agent, Slack integration, cross-vertical chat support, and full observability via OpenTelemetry and Google Cloud Monitoring.

## Architecture Overview

The system is composed of the following components:

* **`calendar_client_api`** — The abstract interface. Defines `Client`, `Event`, and `Task` base classes and a `get_client()` factory. Now aligned to the cross-team shared API (`ospsd_calendar_api.CalendarClient`) agreed upon by Teams 5, 11, and 12. Contains no concrete logic or provider-specific dependencies.
* **`google_calendar_client_impl`** — The concrete Google Calendar implementation. Handles OAuth 2.0 authentication, Google API communication, and JSON parsing. Updated in HW3 to use shared `Event` dataclass and method signatures. Consumed exclusively by the service layer.
* **`calendar_client_service`** — A FastAPI service deployed to Google Cloud Run that wraps `google_calendar_client_impl` and exposes its functionality over HTTP. Extended in HW3 with the Gemini AI agent (`ai_tools.py`), Slack webhook endpoint (`slack_routes.py`), and `TelemetryMiddleware` for OpenTelemetry instrumentation.
* **`calendar_client_service_api_client`** — A typed Python HTTP client auto-generated from the service's OpenAPI spec. Provides typed functions and Pydantic models for every endpoint.
* **`calendar_client_adapter`** — A thin adapter that implements the `calendar_client_api.Client` interface by delegating to the auto-generated HTTP client. Allows callers to use the service as if it were the local library.
* **`slack_chat_adapter`** *(HW3)* — Implements the shared `ChatClient` interface from the Chat vertical's `chat-client-api`, delegating to the Slack Web API.
* **`ai_client_api`** *(HW3)* — Abstract interface for AI assistant clients.
* **`gemini_ai_client_impl`** *(HW3)* — Concrete Gemini-backed implementation of `AIClient`.

## Key Features

* **Zero-Dependency Interface:** Core logic relies only on abstract base classes (`calendar_client_api`).
* **Type-Safe:** Fully typed with modern Python hints (mypy strict compliance).
* **Service-Oriented:** Google Calendar functionality is exposed over HTTP via a deployed FastAPI service, decoupling consumers from the implementation entirely.
* **Adapter Pattern:** `ServiceAdapterClient` bridges the HTTP client and the abstract `Client` interface, so consumer code requires no changes when moving from library to service.
* **AI-Powered:** A Gemini conversational agent answers natural-language questions about a user's calendar via Slack, dispatching structured tool calls to the existing `GoogleCalendarClient` methods.
* **Cross-Vertical Integration:** The chat backend is swappable at runtime via `CHAT_BACKEND` without changing route code. The calendar interface aligns to a shared cross-team API contract.
* **Observable:** Every HTTP request is instrumented with OpenTelemetry, exporting request count and latency metrics to Google Cloud Monitoring and traces to Cloud Trace.
* **Injectable:** Seamlessly integrates with dependency injection patterns via the `get_client()` factory.

## Live Service

| Endpoint | URL |
|---|---|
| **Base URL** | `https://calendar-client-service-iozhebgpyq-uc.a.run.app` |
| **Health Check** | `https://calendar-client-service-iozhebgpyq-uc.a.run.app/health` |
| **OpenAPI Spec** | `https://calendar-client-service-iozhebgpyq-uc.a.run.app/openapi.json` |
| **Slack events** | `https://calendar-client-service-iozhebgpyq-uc.a.run.app/slack/events` |

## Quick Start

This project is managed using `uv`. To set up the environment:

```bash
# 1. Sync dependencies
uv sync --all-packages

# 2. Run the service locally
uv run uvicorn calendar_client_service.app:app --reload --port 8000 --env-file .env

# 3. Run tests
uv run pytest
```

See the [README](https://github.com/samuelj25/ospsd-team-05) and `CONTRIBUTING.md` for full setup instructions including required environment variables.