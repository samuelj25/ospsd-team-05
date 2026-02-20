"""Test verifies client implementation properly registers with API via dependency injection."""

import calendar_client_api
import google_calendar_client_impl  # type: ignore # pylint: disable=unused-import # noqa: F401


def test_dependency_injection_works() -> None:
    """Verify that importing the implementation package automatically registers it with the API."""
    # 1. Ask the API for a client
    client = calendar_client_api.get_client()

    # 2. Verify we got the Google version, not a generic one
    assert type(client).__name__ == "GoogleCalendarClient"
