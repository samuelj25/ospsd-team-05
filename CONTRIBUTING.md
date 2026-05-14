# Contributing Guide

Thank you for your interest in contributing to the Google Calendar Client project. This guide covers everything you need to get started.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- `uv` package manager ([install instructions](https://docs.astral.sh/uv/getting-started/installation/))
- A Google Cloud project with the Calendar API and Tasks API enabled
- OAuth 2.0 credentials (Client ID and Client Secret) from the Google Cloud Console
- A Slack app with a Bot token and signing secret (for AI/Slack features)
- A Gemini API key from Google AI Studio (for AI features)

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
   Export your credentials as environment variables or place them in a `.env` file. Never commit secrets to version control.
   ```bash
   export GOOGLE_OAUTH_CLIENT_ID=your-client-id
   export GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
   export OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback
   export GEMINI_API_KEY=your-gemini-api-key
   export SLACK_BOT_TOKEN=xoxb-your-bot-token
   export SLACK_SIGNING_SECRET=your-signing-secret
   ```

4. **Run the service locally:**
   ```bash
   uv run uvicorn calendar_client_service.app:app --reload --port 8000 --env-file .env
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
│   ├── calendar_client_api/              # Abstract interface (aligned to shared API)
│   │   ├── src/calendar_client_api/      # Source code
│   │   └── tests/                        # Unit tests
│   ├── google_calendar_client_impl/      # Concrete Google Calendar implementation
│   │   ├── src/google_calendar_client_impl/  # Source code
│   │   └── tests/                        # Unit tests
│   ├── calendar_client_service/          # FastAPI HTTP service (events, tasks, Slack/AI, auth)
│   │   ├── src/calendar_client_service/  # Source code
│   │   └── tests/                        # Unit tests
│   ├── calendar_client_service_api_client/  # Auto-generated HTTP client
│   │   ├── calendar_client_service_api_client/  # Source code
│   │   └── tests/                        # Smoke tests
│   ├── calendar_client_adapter/          # Adapter: Client interface → HTTP client
│   │   ├── src/calendar_client_adapter/  # Source code
│   │   └── tests/                        # Unit and integration tests
│   ├── slack_chat_adapter/              # HW3: ChatClient interface → Slack Web API
│   ├── ai_client_api/                   # HW3: Abstract AI client interface
│   └── gemini_ai_client_impl/           # HW3: Gemini-backed AI client implementation
├── infra/                                # Terraform IaC (Cloud Run, Secret Manager, IAM)
├── tests/                                # Cross-component tests
│   ├── integration/                      # Component integration tests (incl. VCR cassettes)
│   └── e2e/                              # End-to-end tests against live Google APIs
├── docs/                                 # MkDocs documentation source
├── Dockerfile                            # Container definition for Cloud Run deployment
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
- **Integration tests** (`tests/integration/`): Verify dependency injection and component interaction. HTTP interactions with AI APIs are recorded via VCR cassettes and replayed in CI.
- **End-to-end tests** (`tests/e2e/`): Run against the live deployed service and real Google APIs with test credentials. Marked with `@pytest.mark.e2e`.

### Writing Tests

- Place unit tests in the relevant component's `tests/` directory.
- Do not add `__init__.py` to test directories.
- Use `pytest` fixtures for shared setup.
- Mock external dependencies — unit tests must not make real API calls.
- For AI tool dispatch tests, use VCR cassettes (`--record-mode=new_episodes` to re-record).
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
| `GEMINI_API_KEY` | Gemini / Google AI Studio API key | — |
| `SLACK_BOT_TOKEN` | Slack Bot OAuth token (`xoxb-…`) | — |
| `SLACK_SIGNING_SECRET` | Slack app signing secret | — |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID (enables Cloud Monitoring/Trace export) | — |
| `GCP_CREDENTIALS_JSON_BASE64` | Base64-encoded `credentials.json` | — |
| `GCP_TOKEN_JSON_BASE64` | Base64-encoded `token.json` | — |
| `CHAT_BACKEND` | Chat backend selector | `"slack"` |

Credentials must never be hardcoded. Use environment variables or Google Secret Manager for all secrets, especially in CI.
