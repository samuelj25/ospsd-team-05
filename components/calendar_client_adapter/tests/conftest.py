"""
Root-level conftest for calendar_client_adapter tests.

``test_integration.py`` imports ``calendar_client_service.app.app``, which
triggers ``create_app()`` at module scope.  ``create_app()`` raises
``RuntimeError`` if required environment variables are missing.

This conftest uses ``pytest_configure`` — which fires before any test
module is imported — to set minimal stub values so that collection
succeeds without a real deployment environment.
"""

import os


def pytest_configure(config: object) -> None:  # noqa: ARG001
    """Set required env vars before any test module is imported."""
    os.environ.setdefault("SLACK_SIGNING_SECRET", "test-signing-secret")
    os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test-token")
    os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
    os.environ.setdefault("ENV", "test")
