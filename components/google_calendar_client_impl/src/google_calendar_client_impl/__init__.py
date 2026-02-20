"""Public exports for the Google Calendar client implementation package."""

from google_calendar_client_impl.google_calendar_impl import (
    GoogleCalendarClient as GoogleCalendarClient,
)
from google_calendar_client_impl.google_calendar_impl import get_client_impl as get_client_impl
from google_calendar_client_impl.google_calendar_impl import register as _register_client


def register() -> None:
    """Register the Google Calendar Client implementation."""
    _register_client()

register()

