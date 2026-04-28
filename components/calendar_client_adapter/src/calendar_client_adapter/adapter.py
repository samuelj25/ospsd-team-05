"""Service adapter implementation mapping API calls to the OpenAPI client."""

import json
from collections.abc import Iterator
from datetime import datetime
from typing import Any

import calendar_client_api
from calendar_client_api import CalendarOperationError, EventNotFoundError, TaskNotFoundError
from calendar_client_api.client import Client as ApiClient
from calendar_client_api.task import Task
from calendar_client_service_api_client.api.events import (
    create_event_events_post,
    delete_event_events_event_id_delete,
    get_event_events_event_id_get,
    list_events_events_get,
    update_event_events_event_id_put,
)
from calendar_client_service_api_client.api.tasks import (
    complete_task_tasks_task_id_complete_post,
    create_task_tasks_post,
    delete_task_tasks_task_id_delete,
    get_task_tasks_task_id_get,
    list_tasks_tasks_get,
    update_task_tasks_task_id_put,
)
from calendar_client_service_api_client.client import AuthenticatedClient
from calendar_client_service_api_client.errors import UnexpectedStatus
from calendar_client_service_api_client.models import (
    EventCreate,
    EventResponse,
    EventUpdate,
    HTTPValidationError,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from ospsd_calendar_api.models import Event


def _event_response_to_event(resp: EventResponse) -> Event:
    """Convert an auto-generated ``EventResponse`` model into an ``Event`` dataclass."""
    return Event(
        id=resp.id,
        title=resp.title,
        start_time=resp.start_time,
        end_time=resp.end_time,
        location=getattr(resp, "location", None),
        description=getattr(resp, "description", None),
    )


class AdapterTask(Task):
    def __init__(self, response: TaskResponse) -> None:
        self._response = response

    @property
    def id(self) -> str:
        return self._response.id

    @property
    def title(self) -> str:
        return self._response.title

    @property
    def start_time(self) -> datetime:
        return self._response.start_time

    @property
    def end_time(self) -> datetime:
        return self._response.end_time

    @property
    def is_completed(self) -> bool:
        return self._response.is_completed

    @property
    def description(self) -> str | None:
        return getattr(self._response, "description", None)


class ServiceAdapterClient(ApiClient):
    def __init__(
        self, base_url: str, session_id: str, httpx_args: dict[str, Any] | None = None
    ) -> None:
        super().__init__()
        self.base_url = base_url
        self.session_id = session_id

        kwargs: dict[str, Any] = {
            "base_url": base_url,
            "token": "cookie-auth-only",  # Not used; auth is handled via session cookies
            "cookies": {"session_id": session_id},
        }
        if httpx_args:
            kwargs["httpx_args"] = httpx_args

        self._client = AuthenticatedClient(**kwargs)

    def _handle_error(self, exc: Exception, not_found_cls: type[Exception]) -> None:
        if isinstance(exc, (CalendarOperationError, EventNotFoundError, TaskNotFoundError)):
            raise exc
        if isinstance(exc, UnexpectedStatus):
            if exc.status_code == 404:  # noqa: PLR2004
                raise not_found_cls("Resource not found.") from exc
            raise CalendarOperationError(f"HTTP Error: {exc.status_code}") from exc
        raise CalendarOperationError(str(exc)) from exc

    # ------------------------------------------------------------------
    # Events — implements ospsd_calendar_api.CalendarClient interface
    # ------------------------------------------------------------------

    def get_event(self, event_id: str) -> Event:
        try:
            resp = get_event_events_event_id_get.sync(client=self._client, event_id=event_id)
            if not resp or isinstance(resp, HTTPValidationError):
                raise EventNotFoundError(f"Event {event_id} not found")
            return _event_response_to_event(resp)
        except Exception as e:
            self._handle_error(e, EventNotFoundError)
            raise

    def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        description: str = "",
        location: str | None = None,
    ) -> Event:
        try:
            payload = EventCreate(
                title=title,
                start_time=start,
                end_time=end,
                location=location,
                description=description or None,
            )

            resp = create_event_events_post.sync(client=self._client, body=payload)
            if not resp or isinstance(resp, HTTPValidationError):
                raise CalendarOperationError("Failed to create event")
            return _event_response_to_event(resp)
        except Exception as e:
            self._handle_error(e, CalendarOperationError)
            raise

    def update_event(self, event_id: str, **kwargs: Any) -> Event:  # noqa: ANN401  # type: ignore[override]
        try:
            payload = EventUpdate(
                id=event_id,
                title=kwargs.get("title", ""),
                start_time=kwargs["start_time"],
                end_time=kwargs["end_time"],
                location=kwargs.get("location"),
                description=kwargs.get("description"),
            )

            resp = update_event_events_event_id_put.sync(
                client=self._client, event_id=event_id, body=payload
            )
            if not resp or isinstance(resp, HTTPValidationError):
                raise EventNotFoundError(f"Event {event_id} not found")
            return _event_response_to_event(resp)
        except Exception as e:
            self._handle_error(e, EventNotFoundError)
            raise

    def delete_event(self, event_id: str) -> None:
        try:
            delete_event_events_event_id_delete.sync(client=self._client, event_id=event_id)
        except Exception as e:
            self._handle_error(e, EventNotFoundError)

    def list_events(self, start: datetime, end: datetime) -> list[Event]:
        try:
            resp = list_events_events_get.sync(client=self._client, start_time=start, end_time=end)
            if resp and not isinstance(resp, HTTPValidationError):
                return [_event_response_to_event(r) for r in resp]
            return []  # noqa: TRY300
        except Exception as e:
            self._handle_error(e, CalendarOperationError)
            raise

    def from_raw_data(self, raw_data: str) -> Event:
        data = json.loads(raw_data)
        return _event_response_to_event(EventResponse.from_dict(data))

    # ------------------------------------------------------------------
    # Tasks — Team-05 private extension
    # ------------------------------------------------------------------

    def get_task(self, task_id: str) -> Task:
        try:
            resp = get_task_tasks_task_id_get.sync(client=self._client, task_id=task_id)
            if not resp or isinstance(resp, HTTPValidationError):
                raise TaskNotFoundError(f"Task {task_id} not found")
            return AdapterTask(resp)
        except Exception as e:
            self._handle_error(e, TaskNotFoundError)
            raise

    def create_task(self, title: str, due: datetime, description: str = "") -> Task:
        try:
            payload = TaskCreate(
                title=title,
                end_time=due,
                description=description,
            )

            resp = create_task_tasks_post.sync(client=self._client, body=payload)
            if not resp or isinstance(resp, HTTPValidationError):
                raise CalendarOperationError("Failed to create task")
            return AdapterTask(resp)
        except Exception as e:
            self._handle_error(e, CalendarOperationError)
            raise

    def update_task(
        self,
        task_id: str,
        title: str,
        due: datetime,
        *,
        is_completed: bool,
        description: str = "",
    ) -> Task:
        try:
            payload = TaskUpdate(
                id=task_id,
                title=title,
                end_time=due,
                is_completed=is_completed,
                description=description,
            )

            resp = update_task_tasks_task_id_put.sync(
                client=self._client, task_id=task_id, body=payload
            )
            if not resp or isinstance(resp, HTTPValidationError):
                raise TaskNotFoundError(f"Task {task_id} not found")
            return AdapterTask(resp)
        except Exception as e:
            self._handle_error(e, TaskNotFoundError)
            raise

    def delete_task(self, task_id: str) -> None:
        try:
            delete_task_tasks_task_id_delete.sync(client=self._client, task_id=task_id)
        except Exception as e:
            self._handle_error(e, TaskNotFoundError)

    def get_tasks(self, start_time: datetime, end_time: datetime) -> Iterator[Task]:
        try:
            resp = list_tasks_tasks_get.sync(
                client=self._client, start_time=start_time, end_time=end_time
            )
            if resp and not isinstance(resp, HTTPValidationError):
                for r in resp:
                    yield AdapterTask(r)
        except Exception as e:
            self._handle_error(e, CalendarOperationError)
            raise

    def mark_task_completed(self, task_id: str) -> None:
        try:
            complete_task_tasks_task_id_complete_post.sync(client=self._client, task_id=task_id)
        except Exception as e:
            self._handle_error(e, TaskNotFoundError)


def get_client_impl(base_url: str = "http://127.0.0.1:8000", session_id: str = "") -> ApiClient:
    return ServiceAdapterClient(base_url, session_id)


def register(base_url: str = "http://127.0.0.1:8000", session_id: str = "") -> None:
    calendar_client_api.get_client = lambda: get_client_impl(base_url, session_id)
