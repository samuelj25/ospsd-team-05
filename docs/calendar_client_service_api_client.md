# Service API Client

This component is a typed Python HTTP client auto-generated from the `calendar_client_service` OpenAPI spec using `openapi-python-client`. It provides typed functions and Pydantic models for every endpoint in the service, so consumers never need to write raw `httpx` or `requests` calls.

## Key Behaviors

- Every endpoint becomes a Python module with four callable functions: `sync`, `sync_detailed`, `asyncio`, and `asyncio_detailed`.
- All path/query parameters and request bodies become typed function arguments.
- All responses are deserialized into typed Pydantic model objects.
- The client is generated from `openapi.json` at the repo root and should not be edited manually.

## Usage

```python
from calendar_client_service_api_client import AuthenticatedClient
from calendar_client_service_api_client.api.events import get_event_events_event_id_get

client = AuthenticatedClient(
    base_url="https://ospsd-team-05.onrender.com",
    token="",
    cookies={"session_id": "<your-session-id>"},
)

event = get_event_events_event_id_get.sync(client=client, event_id="abc123")
print(event.title)
```

## Regenerating the Client

If the service's API changes, regenerate this client from the updated OpenAPI spec:

```bash
openapi-python-client update --path openapi.json
```