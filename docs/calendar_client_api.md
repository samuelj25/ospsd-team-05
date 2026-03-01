# Calendar Client API

This component defines the **abstract contract** for calendar operations. It contains no implementation logic and no dependencies on specific providers (like Google or Outlook).

## The Client Interface

::: calendar_client_api.client
    options:
      show_root_heading: true
      show_source: true

## Data Models

### Event (`event_impl.py` and `event.py`)

A standard representation of a calendar event, abstracting away provider-specific formats. The `GoogleCalendarEvent` implementation parses raw Google Calendar API JSON data into these strictly-typed properties.

* `id: str`: The unique identifier for the event.
* `title: str`: The summary/title of the event. Defaults to `"(No Title)"` if missing.
* `start_time: datetime`: The start time of the event, parsed as a timezone-aware `datetime` object (UTC).
* `end_time: datetime`: The end time of the event, parsed as a timezone-aware `datetime` object (UTC).
* `location: str | None`: The optional location string of the event.
* `description: str | None`: The optional detailed description of the event.
  options:
      show_root_heading: true
      show_source: true

### Task (`task_impl.py` and `task.py`)

A standard representation of a calendar task/to-do item. The `GoogleCalendarTask` implementation parses raw Google Tasks API JSON data into these strictly-typed properties, handling Google's RFC 3339 timestamp requirements.

* `id: str`: The unique identifier for the task.
* `title: str`: The title of the task.
* `start_time: datetime`: The creation/updated time of the task.
* `end_time: datetime`: The due date/time of the task, parsed as a timezone-aware `datetime` object.
* `description: str | None`: Optional notes or detailed description attached to the task.
* `is_completed: bool`: Boolean flag indicating if the task status is `"completed"` or `"needsAction"`.
  options:
      show_root_heading: true
      show_source: true