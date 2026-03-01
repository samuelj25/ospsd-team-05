# Google Calendar Client Implementation

This package (`google-calendar-client-impl`) provides the concrete Google Calendar and Google Tasks implementation of the `calendar-client-api` interface. 

It is designed to be injected into an application, removing explicit dependencies on Google's APIs from the core application logic.

## Dependencies

This implementation relies on the following Google SDKs (as defined in `pyproject.toml`):
* `google-api-python-client` (>=2.177.0)
* `google-auth` (>=2.40.3)
* `google-auth-oauthlib` (>=1.2.2)

It also relies on the abstract interface from:
* `calendar-client-api`

## Development and Testing

This component uses `pytest` and `pytest-mock` for testing. 

You can run the tests using `uv` from the component root or the workspace root:

```bash
uv run pytest components/google_calendar_client_impl/
```

Code coverage is strictly enforced (`fail_under = 80`), with a current threshold configured in `pyproject.toml`.

## Code Quality

This component enforce strict type hinting with `mypy` and linting with `ruff` to ensure high code quality and consistency.
