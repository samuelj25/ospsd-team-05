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

### Capabilities:
- **Events API:** Create, read, update, delete, and list calendar events.
- **Tasks API:** Manage Google Tasks directly through the same interface.
- **OAuth 2.0 Auth:** Securely handles user consent and token refreshes.

This project is built using `uv` for dependency management, strictly types checked via `mypy`, and formatted using `ruff`. Tests are included for the functionality and documentation is compiled through MkDocs.