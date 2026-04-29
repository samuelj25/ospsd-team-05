# Google Calendar Client: A Component-Based Calendar Integration

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A modular, type-safe Python system for interacting with Google Calendar and Google Tasks. Built with a strict separation of concerns, dependency injection, a deployed HTTP service, and a comprehensive automated toolchain.

## Team

**Team 5**

- **Samuel Jimenez Canizal** (`sj3906`)
- **Luis Lazo** (`ll4955`)
- **Jonathan Meneses Barraza** (`jem9707`)
- **Dhruv Topiwala** (`dmt9779`)
- **Vijay Gottipati** (`vg2571`)

## Architectural Philosophy

This project follows a component-based, service-oriented architecture that separates interfaces from implementations to combat complexity and ensure the system is maintainable and evolvable.

- **Interface-Implementation Separation**: Every operation is defined by an abstract contract (ABC) and fulfilled by a concrete implementation. Consumers depend only on the stable interface, never on volatile implementation details.
- **Service-Oriented**: The Google Calendar implementation is wrapped in a deployed FastAPI service. Consumers interact with it over HTTP rather than importing the library directly.
- **Adapter Pattern**: A thin adapter implements the abstract `Client` interface while delegating all calls to the auto-generated HTTP client, making service usage look identical to library usage from the caller's perspective.
- **Component-Based Design**: Each component is a self-contained, installable Python package that can be developed, tested, and versioned independently.

## Core Components

The project is a `uv` workspace containing five packages:

1. **`calendar_client_api`**: Defines the abstract `Client`, `Event`, and `Task` base classes. This is the contract for what actions a calendar client can perform. Contains no concrete logic or provider-specific dependencies.
2. **`google_calendar_client_impl`**: Provides `GoogleCalendarClient`, a concrete implementation backed by the Google Calendar API and Google Tasks API. Handles OAuth2 authentication, raw JSON parsing, and automatic dependency injection. Consumed exclusively by the service layer.
3. **`calendar_client_service`**: A FastAPI application that wraps `google_calendar_client_impl` and exposes its functionality over HTTP. Handles OAuth session management, provides REST endpoints for events and tasks, and is deployed to Render.
4. **`calendar_client_service_api_client`**: A typed Python client library auto-generated from the service's OpenAPI spec. Provides typed functions and models for every endpoint without requiring raw HTTP calls.
5. **`calendar_client_adapter`**: A thin adapter (`ServiceAdapterClient`) that implements the `calendar_client_api.Client` interface by delegating to the auto-generated HTTP client. Allows consumer code to remain unchanged when switching from direct library use to the deployed service.

## Project Structure

```
ospsd-team-05/
├── components/
│   ├── calendar_client_api/              # Abstract calendar client interface (ABC)
│   │   ├── src/calendar_client_api/
│   │   │   ├── client.py                 # Client ABC with event & task operations
│   │   │   ├── event.py                  # Event ABC
│   │   │   ├── task.py                   # Task ABC
│   │   │   └── exceptions.py             # Custom exception hierarchy
│   │   └── tests/                        # Unit tests for the interface
│   ├── google_calendar_client_impl/      # Google Calendar implementation
│   │   ├── src/google_calendar_client_impl/
│   │   │   ├── google_calendar_impl.py   # Client implementation
│   │   │   ├── event_impl.py             # Event JSON parser
│   │   │   ├── task_impl.py              # Task JSON parser
│   │   │   └── auth.py                   # OAuth 2.0 authentication
│   │   └── tests/                        # Unit tests
│   ├── calendar_client_service/          # FastAPI HTTP service
│   │   ├── src/calendar_client_service/
│   │   │   ├── app.py                    # FastAPI app factory
│   │   │   ├── dependencies.py           # DI: session-aware GoogleCalendarClient
│   │   │   ├── models.py                 # Pydantic request/response schemas
│   │   │   ├── auth_routes.py            # OAuth 2.0 endpoints
│   │   │   ├── event_routes.py           # Event CRUD endpoints
│   │   │   └── task_routes.py            # Task CRUD endpoints
│   │   └── tests/                        # Unit tests
│   ├── calendar_client_service_api_client/  # Auto-generated HTTP client
│   │   ├── calendar_client_service_api_client/
│   │   │   ├── api/                      # Generated endpoint functions
│   │   │   └── models/                   # Generated Pydantic models
│   │   └── tests/                        # Smoke tests
│   └── calendar_client_adapter/          # Adapter: Client interface → HTTP client
│       ├── src/calendar_client_adapter/
│       │   └── adapter.py                # ServiceAdapterClient implementation
│       └── tests/                        # Unit and integration tests
├── tests/                                # Cross-component tests
│   ├── integration/                      # Component integration tests
│   └── e2e/                              # End-to-end tests against live APIs
├── docs/                                 # MkDocs documentation source
├── Dockerfile                            # Container definition for Render deployment
├── pyproject.toml                        # Root workspace configuration
└── mkdocs.yml                            # Documentation configuration
```

## Project Setup

### 1. Prerequisites

- Python 3.11 or higher
- `uv` – A fast, all-in-one Python package manager.

### 2. Initial Setup

1. **Install `uv`:**
   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the Repository:**
   ```bash
   git clone https://github.com/samuelj25/ospsd-team-05.git
   cd ospsd-team-05
   ```

3. **Set Up Google Credentials:**
   - Follow the [Google Cloud instructions](https://developers.google.com/calendar/api/quickstart/python) to enable the Google Calendar API and Google Tasks API.
   - Create an OAuth 2.0 Client ID in the Google Cloud Console and note your Client ID, Client Secret, and Redirect URI.
   - **Important:** Credentials must never be committed to version control. Set them as environment variables locally (see below) or via your deployment platform.

4. **Create and Sync the Virtual Environment:**
   ```bash
   uv sync --all-packages
   ```

5. **Run the Service Locally:**
   ```bash
   uv run uvicorn calendar_client_service.app:app --reload --port 8000
   ```
   Navigate to `http://localhost:8000/auth/login` to complete the OAuth flow and obtain a session cookie.

### 3. Environment Variables

| Variable | Description |
|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` | OAuth 2.0 Client ID from GCP Console |
| `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth 2.0 Client Secret from GCP Console |
| `OAUTH_REDIRECT_URI` | OAuth callback URL (default: `http://localhost:8000/auth/callback`) |
| `GOOGLE_CALENDAR_ID` | Calendar ID to operate on (default: `primary`) |

## Development Workflow

All commands should be run from the project root.

### Running the Toolchain

- **Linting & Formatting (Ruff):**
  ```bash
  uv run ruff check .
  ```

- **Static Type Checking (MyPy):**
  ```bash
  uv run mypy --strict .
  ```

- **Testing (Pytest):**
  ```bash
  uv run pytest
  ```

- **Documentation (MkDocs):**
  ```bash
  uv run mkdocs serve
  ```
  Open `http://127.0.0.1:8000` to view the documentation site.

## Testing

The project implements a layered testing strategy:

- **Unit Tests** (`components/*/tests/`): Fast, isolated tests with mocked dependencies. No real API calls.
- **Integration Tests** (`tests/integration/`): Verify that dependency injection works and components integrate correctly.
- **End-to-End Tests** (`tests/e2e/`): Full workflow tests against real Google APIs using test credentials.

Coverage thresholds are enforced in CI, and test results are reported to the CircleCI dashboard.

```bash
# Run all tests with coverage
uv run pytest
```

## Continuous Integration

The project uses CircleCI for automated builds. The pipeline runs static analysis (ruff, mypy), all test suites, stores test results, and reports code coverage. See `.circleci/config.yml` for the full configuration.

## Deployment

The service is configured to be automatically deployed to **Render** using a `Dockerfile`. The automated deployment is triggered via a CircleCI workflow webhook.

### 1. Platform and CI/CD Pipeline
- **Platform:** Render (Docker Web Service)
- **CI/CD Integration:** CircleCI triggers the deployment via a Render Deploy Hook URL but **only** on the `hw2` branch and **only** after all unit, integration, and E2E tests have passed.
- **Base Image:** `ghcr.io/astral-sh/uv:python3.11-bookworm-slim`

### 2. Live URLs
- **Base URL:** `https://ospsd-team-05.onrender.com`
- **OpenAPI Spec:** `https://ospsd-team-05.onrender.com/openapi.json`
- **Health Check Endpoint:** `https://ospsd-team-05.onrender.com/health` (Returns HTTP 200 OK)

### 3. Required Environment Variables (Production)
The deployed instance securely manages its configurations using Render Environment variables:

| Variable | Description |
|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` | External Provider OAuth 2.0 Client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | External Provider OAuth 2.0 Client Secret |
| `OAUTH_REDIRECT_URI` | External Provider OAuth 2.0 Redirect URI |
| `GOOGLE_CALENDAR_ID` | Calendar ID to operate on (default: `primary`) |

_Note: Secrets are never stored in version control and are only managed securely via the Render Dashboard._