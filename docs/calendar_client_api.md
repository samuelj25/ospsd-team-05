# Calendar Client API

This component defines the **abstract contract** for calendar operations. It contains no implementation logic and no dependencies on specific providers (like Google or Outlook).

## Key Behaviors

- Defines a single `Client` ABC covering full CRUD for both events and tasks.
- Provides `Event` and `Task` ABCs as strictly-typed, read-only data contracts.
- Exposes a `get_client()` factory function that implementations override via dependency injection.
- Ships a custom exception hierarchy for provider-agnostic error handling.

## The Client Interface

::: calendar_client_api.client
    options:
      show_root_heading: true
      show_source: true

## Data Models

::: calendar_client_api.event.Event
    options:
      show_root_heading: true
      show_source: true

::: calendar_client_api.task.Task
    options:
      show_root_heading: true
      show_source: true

## Exceptions

::: calendar_client_api.exceptions
    options:
      show_root_heading: true
      show_source: true