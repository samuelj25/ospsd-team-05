# Google Calendar Client: A Component-Based Calendar Integration

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A modular, type-safe Python library for interacting with Google Calendar and Google Tasks. Built with a strict separation of concerns, dependency injection, and a comprehensive automated toolchain.

## Team

**Team 5**

- **Samuel Jimenez Canizal** (`sj3906`)
- **Luis Lazo** (`ll4955`)
- **Jonathan Meneses Barraza** (`jem9707`)
- **Dhruv Topiwala** (`dmt9779`)
- **Vijay Gottipati** (`vg2571`)

## Architectural Philosophy

This project follows a component-based architecture that separates interfaces from implementations to combat complexity and ensure the system is maintainable and evolvable.

- **Interface-Implementation Separation**: Every operation is defined by an abstract contract (ABC) and fulfilled by a concrete implementation. Consumers depend only on the stable interface, never on volatile implementation details.
- **Dependency Injection**: The implementation registers itself at import time, replacing the interface's factory function. Code that uses the client never needs to know it's talking to Google Calendar specifically.
- **Component-Based Design**: Each component is a self-contained, installable Python package that can be developed, tested, and versioned independently.

## Core Components

The project is a `uv` workspace containing two primary packages:

1. **`calendar_client_api`**: Defines the abstract `Client`, `Event`, and `Task` base classes. This is the contract for what actions a calendar client can perform. Contains no concrete logic or provider-specific dependencies.
2. **`google_calendar_client_impl`**: Provides `GoogleCalendarClient`, a concrete implementation backed by the Google Calendar API and Google Tasks API. Handles OAuth2 authentication, raw JSON parsing, and automatic dependency injection.

## Project Structure

```
ospsd-team-05/
├── components/
│   ├── calendar_client_api/        # Abstract calendar client interface (ABC)
│   │   ├── src/calendar_client_api/
│   │   │   ├── client.py           # Client ABC with event & task operations
│   │   │   ├── event.py            # Event ABC
│   │   │   ├── task.py             # Task ABC
│   │   │   └── exceptions.py       # Custom exception hierarchy
│   │   └── tests/                  # Unit tests for the interface
│   └── google_calendar_client_impl/ # Google Calendar implementation
│       ├── src/google_calendar_client_impl/
│       │   ├── google_calendar_impl.py  # Client implementation
│       │   ├── event_impl.py            # Event JSON parser
│       │   ├── task_impl.py             # Task JSON parser
│       │   └── auth.py                  # OAuth 2.0 authentication
│       └── tests/                       # Unit tests
├── tests/                          # Cross-component tests
│   ├── integration/                # Component integration tests
│   └── e2e/                        # End-to-end tests
├── docs/                           # MkDocs documentation source
├── pyproject.toml                  # Root workspace configuration
└── mkdocs.yml                      # Documentation configuration
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
   - Download your OAuth 2.0 credentials and save as `credentials.json` in the project root.
   - **Important:** Credential files contain secrets and must not be committed to version control.

4. **Create and Sync the Virtual Environment:**
   ```bash
   uv sync --all-packages
   ```

5. **Perform Initial Authentication:**
   Run the application once to complete the interactive OAuth flow. This opens a browser window for consent and creates a `token.json` file for subsequent runs.

### 3. Environment Variables

| Variable | Description |
|---|---|
| `GOOGLE_OAUTH_CREDENTIALS_PATH` | Path to `credentials.json` (default: `./credentials.json`) |
| `GOOGLE_OAUTH_TOKEN_PATH` | Path to `token.json` (default: `./token.json`) |
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
- **OpenAPI Client Base URL:** `https://ospsd-team-05.onrender.com/openapi.json`
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