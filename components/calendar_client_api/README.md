# Calendar Client API

## Overview

`calendar_client_api` defines the `Client` abstract base class that every calendar client must implement. The package contains the abstractions for events, tasks, and exceptions, a factory hook, and no concrete logic.

## Purpose

- Document the operations available to consumers.
- Provide a single factory (`get_client`) that implementations can override.
- Keep type dependencies explicit through the `calendar_client_api.event` and `calendar_client_api.task` modules.

## Architecture

### Component Design

The package exposes one abstract base class focused on calendar operations—event CRUD, task CRUD, and task completion. It depends only on the `Event` and `Task` abstractions.

### API Integration

```python
from calendar_client_api import Client, get_client
from calendar_client_api.event import Event
from calendar_client_api.task import Task

client: Client = get_client()

for event in client.get_events(start_time=start, end_time=end):
    title: str = event.title

for task in client.get_tasks(start_time=start, end_time=end):
    completed: bool = task.is_completed
```

### Dependency Injection

Implementation packages (for example `google_calendar_client_impl`) replace the factory at import time:

```python
import google_calendar_client_impl  # rebinds calendar_client_api.get_client

from calendar_client_api import get_client

client = get_client()
```

## API Reference

### Client Abstract Base Class

```python
class Client(ABC):
    ...
```

#### Event Methods

- `get_event(event_id: str) -> Event`: Fetch a single event by ID.
- `create_event(event: Event) -> Event`: Create a new event.
- `update_event(event: Event) -> Event`: Update an existing event.
- `delete_event(event_id: str) -> None`: Delete an event by ID.
- `get_events(start_time: datetime, end_time: datetime) -> Iterator[Event]`: Yield events within a time range.
- `from_raw_data(raw_data: str) -> Event`: Construct an Event from raw JSON data.

#### Task Methods

- `get_task(task_id: str) -> Task`: Fetch a single task by ID.
- `create_task(task: Task) -> Task`: Create a new task.
- `update_task(task: Task) -> Task`: Update an existing task.
- `delete_task(task_id: str) -> None`: Delete a task by ID.
- `get_tasks(start_time: datetime, end_time: datetime) -> Iterator[Task]`: Yield tasks within a time range.
- `mark_task_completed(task_id: str) -> None`: Mark a task as completed.

### Event Abstract Base Class

```python
class Event(ABC):
    ...
```

#### Properties

- `id -> str`: Unique identifier for the event.
- `title -> str`: Title of the event.
- `start_time -> datetime`: Start time of the event.
- `end_time -> datetime`: End time of the event.
- `location -> str | None`: Location of the event.
- `description -> str | None`: Description of the event.

### Task Abstract Base Class

```python
class Task(ABC):
    ...
```

#### Properties

- `id -> str`: Unique identifier for the task.
- `title -> str`: Title of the task.
- `start_time -> datetime`: Start time of the task.
- `end_time -> datetime`: End time of the task.
- `description -> str | None`: Description of the task.
- `is_completed -> bool`: Whether the task is completed.

### Exceptions

- `CalendarError`: Base exception for all calendar client errors.
- `EventNotFoundError`: Raised when an event is not found.
- `TaskNotFoundError`: Raised when a task is not found.
- `CalendarOperationError`: Raised when a calendar operation fails.

### Factory Function

`get_client() -> Client`: Returns the bound implementation or raises `NotImplementedError` if none registered.

## Usage Examples

### Event Operations

```python
from calendar_client_api import get_client

client = get_client()

event = client.get_event("event_123")
print(f"{event.title} at {event.location}")

for event in client.get_events(start_time=start, end_time=end):
    print(f"{event.id}: {event.title}")
```

### Task Operations

```python
from calendar_client_api import get_client

client = get_client()

task = client.get_task("task_456")
if not task.is_completed:
    client.mark_task_completed(task.id)
```

## Implementation Checklist

1. Implement every method in the `Client` abstract base class.
2. Return objects compatible with `calendar_client_api.event.Event` and `calendar_client_api.task.Task`.
3. Publish a factory (`get_client_impl`) and assign it to `calendar_client_api.get_client`.
4. Raise exceptions from `calendar_client_api.exceptions` where appropriate.

## Testing

```bash
uv run pytest components/calendar_client_api/tests/ -q
uv run pytest components/calendar_client_api/tests/ --cov=calendar_client_api --cov-report=term-missing
```