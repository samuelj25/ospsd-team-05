# Contributing Guide

Thank you for your interest in contributing to the Google Calendar Client project. This guide covers everything you need to get started.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- `uv` package manager ([install instructions](https://docs.astral.sh/uv/getting-started/installation/))
- A Google Cloud project with the Calendar API and Tasks API enabled
- OAuth 2.0 credentials (Client ID and Client Secret) from the Google Cloud Console

### Setting Up Your Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/samuelj25/ospsd-team-05.git
   cd ospsd-team-05
   ```

2. **Install dependencies:**
   ```bash
   uv sync --all-packages
   ```

3. **Set up credentials:**
   Export your Google OAuth credentials as environment variables. Never commit secrets to version control.
   ```bash
   export GOOGLE_OAUTH_CLIENT_ID=your-client-id
   export GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
   export OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback
   ```

4. **Run the service locally:**
   ```bash
   uv run uvicorn calendar_client_service.app:app --reload --port 8000
   ```
   Navigate to `http://localhost:8000/auth/login` to complete the OAuth flow.

5. **Verify everything works:**
   ```bash
   uv run ruff check .
   uv run mypy --strict .
   uv run pytest
   ```

## Repository Structure

```
ospsd-team-05/
├── components/
│   ├── calendar_client_api/              # Abstract interface (ABC)
│   │   ├── src/calendar_client_api/      # Source code
│   │   └── tests/                        # Unit tests
│   ├── google_calendar_client_impl/      # Concrete Google Calendar implementation
│   │   ├── src/google_calendar_client_impl/  # Source code
│   │   └── tests/                        # Unit tests
│   ├── calendar_client_service/          # FastAPI HTTP service
│   │   ├── src/calendar_client_service/  # Source code
│   │   └── tests/                        # Unit tests
│   ├── calendar_client_service_api_client/  # Auto-generated HTTP client
│   │   ├── calendar_client_service_api_client/  # Source code
│   │   └── tests/                        # Smoke tests
│   └── calendar_client_adapter/          # Adapter: Client interface → HTTP client
│       ├── src/calendar_client_adapter/  # Source code
│       └── tests/                        # Unit and integration tests
├── tests/                                # Cross-component tests
│   ├── integration/
│   └── e2e/
├── docs/                                 # MkDocs documentation
├── Dockerfile                            # Container definition for Render deployment
├── pyproject.toml                        # Root workspace config
└── mkdocs.yml                            # Documentation config
```

## Development Workflow

### Branching Strategy

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes with meaningful, atomic commits.
3. Push your branch and open a Pull Request against `main`.
4. Address any review feedback by pushing additional commits.

### Commit Guidelines

- Write clear, concise commit messages that describe *what* changed and *why*.
- Keep commits atomic — each commit should represent a single logical change.
- Avoid large commits that bundle unrelated changes together.
- Squash work-in-progress commits before requesting review.

### Pull Request Process

1. Fill out the PR template completely, including a summary of changes and the type of change.
2. Ensure all CI checks pass (ruff, mypy, pytest, coverage threshold).
3. Request review from at least one team member.
4. Address all review feedback before merging.
5. Do not merge your own PR without approval.

## Code Quality Standards

### Static Analysis

All code must pass ruff and mypy with no exceptions before merging.

```bash
# Linting
uv run ruff check .

# Auto-fix lint issues
uv run ruff check . --fix

# Type checking
uv run mypy --strict .
```

- **Ruff**: All rules are enabled via `select = ["ALL"]` in the root `pyproject.toml`. A small set of rules are explicitly ignored with justification.
- **MyPy**: Strict mode is enforced. Do not use `type: ignore` unless you have a documented reason.
- **`noqa` comments**: Acceptable sparingly in test code for niche cases, but must include a justification. Source code should not be littered with ignored rules.

### Import Style

- Use **absolute imports only**, even within the same package.
- Do not use `__all__` in `__init__.py` files.
- Do not use `import *`.

### Coding Conventions

- All modules, classes, and public methods must have docstrings.
- Use type hints on all function signatures and return types.
- Keep interfaces small — low surface area, high functionality.
- Implementation details must not leak into interface packages. The `calendar_client_api` package must have zero dependencies on `google_calendar_client_impl`.

## Testing

### Running Tests

All tests are run from the project root:

```bash
uv run pytest
```

### Test Categories

- **Unit tests** (`components/*/tests/`): Fast, isolated, deterministic. Mock all external API calls. No test should depend on another.
- **Integration tests** (`tests/integration/`): Verify dependency injection and component interaction.
- **End-to-end tests** (`tests/e2e/`): Run against the live deployed service and real Google APIs with test credentials.

### Writing Tests

- Place unit tests in the relevant component's `tests/` directory.
- Do not add `__init__.py` to test directories.
- Use `pytest` fixtures for shared setup.
- Mock external dependencies — unit tests must not make real API calls.
- Mark intentionally untestable lines with `# pragma: no cover`.
- Aim to meet or exceed the 85% coverage threshold.

## Documentation

We use MkDocs with the Material theme. Documentation source lives in `docs/`.

```bash
# Preview locally
uv run mkdocs serve

# Verify build
uv run mkdocs build --strict
```

When adding or modifying a component, update the corresponding documentation in `docs/` and the component's `README.md`.

## Reporting Issues

- **Bugs**: Use the [bug report template](.github/bug_report.md). Include reproduction steps, expected behavior, and environment details.
- **Feature requests**: Use the [feature request template](.github/feature_request.md). Describe the problem, your proposed solution, and alternatives considered.

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` | OAuth 2.0 Client ID from GCP Console | — |
| `GOOGLE_OAUTH_CLIENT_SECRET` | OAuth 2.0 Client Secret from GCP Console | — |
| `OAUTH_REDIRECT_URI` | OAuth callback URL | `http://localhost:8000/auth/callback` |
| `GOOGLE_CALENDAR_ID` | Calendar ID to operate on | `primary` |

Credentials must never be hardcoded. Use environment variables for all secrets, especially in CI.