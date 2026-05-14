"""
Root-level conftest for calendar_client_service tests.

``create_app()`` is called at module scope in ``app.py`` and raises
``RuntimeError`` if required environment variables are not set.  This
conftest uses the ``pytest_configure`` hook — which fires before any
test module is imported — to inject minimal stub values so that
collection does not fail.

The stubs are safe to use in tests because:
- ``SLACK_SIGNING_SECRET`` is consumed only by ``_verify_slack_signature``,
  which is patched in every HTTP-level test.
- ``SLACK_BOT_TOKEN`` is consumed by ``SlackChatAdapter.__init__``, which
  is always injected as a mock via dependency overrides.
- ``GEMINI_API_KEY`` is consumed by ``GeminiAIClient.__init__``, which is
  likewise mocked.
- ``ENV=test`` enables the ``E2E_SESSION_ID`` fallback branch in
  ``slack_routes.py`` for end-to-end test scenarios.
"""

import os


def pytest_configure(config: object) -> None:  # noqa: ARG001
    """Set required env vars before any test module is imported."""
    os.environ.setdefault("SLACK_SIGNING_SECRET", "test-signing-secret")
    os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test-token")
    os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
    os.environ.setdefault("ENV", "test")
