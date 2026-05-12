# Calendar Task API

## Overview

`calendar_task_api` is a **Team-05 private extension** — it is not part of the
shared vertical API contract defined in `ospsd_calendar_api`. It extends
`ospsd_calendar_api.CalendarClient` with Google Tasks-specific operations for
Team-05's internal use only.

The package contains:
- `Task` — abstract base class for a calendar task
- `Client` — extended `CalendarClient` ABC that adds task methods
- `TaskNotFoundError` — raised when a requested task does not exist
- `get_client` — factory hook that implementations override at runtime

## Why a Separate Package

The shared vertical contract (`ospsd_calendar_api`) covers calendar events
only. Google Tasks is a Team-05-specific feature that was not agreed upon
across verticals. Keeping task types here — rather than in `calendar_client_api`
— ensures the shared package stays clean and another team's calendar
implementation would not be required to implement task methods.

## Architecture

### Component Design

```
ospsd_calendar_api.CalendarClient  (shared vertical contract — events only)
        │
        └── calendar_task_api.Client  (Team-05 extension — adds task methods)
                │
                └── GoogleCalendarClient  (concrete impl in google_calendar_client_impl)
```

### Usage

```python
from calendar_task_api import Client, Task, TaskNotFoundError, get_client

client: Client = get_client()

# Task CRUD
task = client.get_task("task_123")
if not task.is_completed:
    client.mark_task_completed(task.id)

for task in client.get_tasks(start_time=start, end_time=end):
    print(f"{task.title} — completed: {task.is_completed}")
```

### Dependency Injection

`get_client` is patched at runtime by the concrete implementation's `register()` call:

```python
import google_calendar_client_impl  # rebinds calendar_task_api.get_client

from calendar_task_api import get_client

client = get_client()
```

## API Reference

### `Client` Abstract Base Class

Subclasses `ospsd_calendar_api.CalendarClient`. All five event methods are
inherited from the shared contract. The following task methods are added:

- `get_task(task_id: str) -> Task` — fetch a single task by ID
- `create_task(title, due, description) -> Task` — create a new task
- `update_task(task_id, *, title, due, description, is_completed) -> Task` — update a task
- `delete_task(task_id: str) -> None` — delete a task by ID
- `get_tasks(start_time, end_time) -> Iterator[Task]` — yield tasks within a time range
- `mark_task_completed(task_id: str) -> None` — mark a task as completed

### `Task` Abstract Base Class

#### Properties

- `id -> str` — unique identifier for the task
- `title -> str` — title of the task
- `start_time -> datetime | None` — start time of the task
- `end_time -> datetime | None` — due date/time of the task
- `description -> str | None` — notes for the task
- `is_completed -> bool` — whether the task is completed

### Exceptions

- `TaskNotFoundError` — raised when a requested task does not exist. Subclasses
  `ospsd_calendar_api.exceptions.CalendarError`.

## Implementation Checklist

1. Subclass `calendar_task_api.Client`.
2. Implement all six task methods listed above.
3. Also implement all five event methods inherited from `ospsd_calendar_api.CalendarClient`.
4. Return objects that satisfy the `Task` ABC for all task methods.
5. Raise `TaskNotFoundError` (from `calendar_task_api.exceptions`) when a task is not found.
6. Publish a factory and assign it to `calendar_task_api.get_client`.

## Testing

```bash
uv run pytest components/calendar_task_api/tests/ -q
uv run pytest components/calendar_task_api/tests/ --cov=calendar_task_api --cov-report=term-missing
```