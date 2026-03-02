# Task Implementation

This module provides `GoogleCalendarTask`, the concrete implementation of the `calendar_client_api.task.Task` abstract base class. It parses raw JSON responses from the Google Tasks API into typed, immutable task objects.

## Key Behaviors

- Accepts raw API responses as a `dict` or JSON string.
- Parses ISO 8601 datetime strings for `due` and `updated` fields.
- Falls back to `due` for `start_time` when `updated` is absent.
- Derives completion status from the `status` field (`"completed"` vs `"needsAction"`).
- Maps the `notes` field to `description`.

## API Reference

::: google_calendar_client_impl.task_impl.GoogleCalendarTask
    options:
      show_root_heading: true
      show_source: true