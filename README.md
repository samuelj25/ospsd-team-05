# Google Calendar Client
## Team Name
Team 5

### Team Members
- **Samuel Jimenez Canizal** (`sj3906`)
- **Luis Lazo** (`ll4955`)
- **Jonathan Meneses Barraza** (`jem9707`)
- **Dhruv Topiwala** (`dmt9779`)
- **Vijay Gottipati** (`vg2571`)

## Project Description
This repository contains a modular, type-safe Python client for Google Calendar and Tasks.

The project demonstrates **Dependency Injection (DI)** by strictly separating the API contracts (`calendar_client_api`) from the concrete Google implementation (`google_calendar_client_impl`). This architecture ensures the client is easily testable and adaptable to other calendar providers in the future.

### Components Breakdown

This project is separated into two primary python packages:

1. **`calendar_client_api`**:
   The `calendar_client_api` acts as the interface over calendar operations. It dictates the `events` and `tasks` operations, providing strictly-typed abstract Object representations (e.g., `calendar_client_api.Event` and `calendar_client_api.Task`). It enforces Dependency Injection by utilizing a factory (`get_client()`) that must be overridden by implementations.

2. **`google_calendar_client_impl`**:
   The `google_calendar_client_impl` is the concrete implementation. It utilizes Google's Python SDK (`google-api-python-client`) and OAuth 2.0 flow via `InstalledAppFlow` (`google-auth-oauthlib`).
   
   * **Authentication (`auth.py`)**: Fetches or refreshes cacheable tokens (`token.json`), relying on OAuth user-consent in the browser if no session exists.
   * **Events (`event_impl.py`)**: Parsers translating UTC datetimes and Google's specific REST event models back into the expected API representation.
   * **Tasks (`task_impl.py`)**: Parsers working around Google's RFC 3339 strict timestamps and parsing task status (needsAction/completed) constraints.

### Quality and Testing Strategy

This project employs professional software development lifecycles focusing heavily on Mock testing, Static Analysis, and documentation:
* **Testing (`pytest` / `pytest-mock`)**: 
  The test suites strictly isolate unit boundaries. By patching `googleapiclient.discovery.build`, tests do not make real network calls but assert that appropriate JSON formats are passed down, validating the parsing logic and logic constraints (e.g. testing missing 'id' errors).
* **Static Analysis**: 
  Code quality is strictly enforced utilizing `mypy` for typing safety and `ruff` for linting/formatting.
* **Documentation (`mkdocs`)**: 
  Documentation is built continuously utilizing `mkdocs` with `mkdocstrings`, pulling heavily from docstrings and Markdown components located in the `/docs` folder.

This project is managed utilizing `uv` for lightning-fast deterministic dependency syncing, building, and running.