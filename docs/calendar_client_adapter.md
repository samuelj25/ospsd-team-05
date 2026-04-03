# Calendar Client Adapter

This component provides `ServiceAdapterClient`, a thin adapter that implements the `calendar_client_api.Client` abstract interface while delegating every method call to the auto-generated HTTP client (`calendar_client_service_api_client`). It is the bridge that makes service usage look identical to direct library usage from the caller's perspective.

## Key Behaviors

- Implements every method of `calendar_client_api.Client` — no abstract method is left unimplemented.
- Wraps `EventResponse` and `TaskResponse` Pydantic models in `AdapterEvent` and `AdapterTask` objects that satisfy the `Event` and `Task` abstract interfaces.
- Maps HTTP error responses (`UnexpectedStatus(404)`) back to the appropriate `calendar_client_api` exceptions (`EventNotFoundError`, `TaskNotFoundError`, `CalendarOperationError`), preserving the interface's exception contract for callers.
- Provides a `register()` helper that patches `calendar_client_api.get_client` so any code using the factory function transparently receives a service-backed client.

## Usage

```python
from calendar_client_adapter.adapter import register

register(base_url="https://ospsd-team-05.onrender.com", session_id="<your-session-id>")

import calendar_client_api
client = calendar_client_api.get_client()  # returns ServiceAdapterClient

event = client.get_event("abc123")
print(event.title)  # AdapterEvent, satisfies the Event interface
```

This call site is identical to the HW1 library usage — no consumer code changes are required when switching from direct library use to the deployed service.

## API Reference

::: calendar_client_adapter.adapter
    options:
      show_root_heading: true
      show_source: true