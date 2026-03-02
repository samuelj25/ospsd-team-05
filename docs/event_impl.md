# Event Implementation

This module provides `GoogleCalendarEvent`, the concrete implementation of the `calendar_client_api.event.Event` abstract base class. It parses raw JSON responses from the Google Calendar API into typed, immutable event objects.

## Key Behaviors

- Accepts raw API responses as a `dict` or JSON string.
- Handles both **timed events** (`dateTime`) and **all-day events** (`date`).
- Falls back to `"(No Title)"` when the `summary` field is missing.
- Validates required fields (`id`, `start`, `end`) on construction.

## API Reference

::: google_calendar_client_impl.event_impl.GoogleCalendarEvent
    options:
      show_root_heading: true
      show_source: true