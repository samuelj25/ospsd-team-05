"""
Google Calendar Client implementation.

Acts as a Translator and Gateway between the abstract ``calendar_client_api`` domain models and
Google's specific REST structures for both the Calendar and Tasks APIs.
"""

import json
import os
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import calendar_client_api
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from google_calendar_client_impl.auth import get_credentials
from google_calendar_client_impl.event_impl import GoogleCalendarEvent
from google_calendar_client_impl.task_impl import GoogleCalendarTask

_NOT_CONNECTED_MSG = "Client is not connected. Call connect() first."


class GoogleCalendarClient(calendar_client_api.Client):
    """
    Concrete implementation of the Client abstraction using Google Calendar API.

    This client does **not** connect to Google APIs on instantiation.
    Call :meth:`connect` explicitly after construction to authenticate and build the API service
    objects. All CRUD methods raise ``CalendarOperationError`` if called before ``connect()``.
    """

    def __init__(
        self,
        calendar_id: str = "primary",
        tasklist_id: str = "@default",
        credentials_path: str | None = None,
        token_path: str | None = None,
    ) -> None:
        """
        Initialize the Google Calendar client.

        Stores configuration only — no network I/O or authentication occurs here, allowing the
        client to be safely injected and configured before any side effects are triggered.

        Args:
            calendar_id: The Google Calendar ID to operate on.
                         Defaults to ``"primary"``.
            tasklist_id: The Google Tasks list ID to operate on.
                         Defaults to ``"@default"``.
            credentials_path: Path to the OAuth client-secrets file.
            token_path: Path to the cached OAuth token file.

        """
        super().__init__()
        self.calendar_id = calendar_id
        self.tasklist_id = tasklist_id
        self._credentials_path = credentials_path
        self._token_path = token_path
        self._service: Any | None = None
        self._tasks_service: Any | None = None

    def _require_calendar_service(self) -> Any:  # noqa: ANN401
        """Return the Calendar service or raise if not connected."""
        if not self._service:
            raise calendar_client_api.CalendarOperationError(_NOT_CONNECTED_MSG)
        return self._service

    def _require_tasks_service(self) -> Any:  # noqa: ANN401
        """Return the Tasks service or raise if not connected."""
        if not self._tasks_service:
            raise calendar_client_api.CalendarOperationError(_NOT_CONNECTED_MSG)
        return self._tasks_service

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """
        Authenticate via OAuth 2.0 and build API service objects.

        Overrides ``calendar_id`` with the ``GOOGLE_CALENDAR_ID`` environment variable if the
        current ID is still the default ``"primary"``. Uses ``googleapiclient.discovery.build``
        to construct and cache ``Resource`` objects for both the Calendar (v3) and Tasks (v1) APIs.
        """
        env_calendar_id = os.environ.get("GOOGLE_CALENDAR_ID")
        if env_calendar_id and self.calendar_id == "primary":
            self.calendar_id = env_calendar_id

        creds = get_credentials(
            credentials_path=self._credentials_path,
            token_path=self._token_path,
        )
        self._service = build("calendar", "v3", credentials=creds)
        self._tasks_service = build("tasks", "v1", credentials=creds)

    def connect_with_credentials(self, creds: Any) -> None:  # noqa: ANN401
        """
        Build API service objects from externally supplied credentials.

        Use this method in the FastAPI service to inject per-user credentials
        obtained from the OAuth 2.0 web flow (via ``WebOAuthManager``) rather
        than loading them from a local ``token.json`` file.

        Args:
            creds: A ``google.oauth2.credentials.Credentials`` instance
                   previously obtained from ``WebOAuthManager.handle_callback``
                   or ``WebOAuthManager.get_credentials``.

        """
        env_calendar_id = os.environ.get("GOOGLE_CALENDAR_ID")
        if env_calendar_id and self.calendar_id == "primary":
            self.calendar_id = env_calendar_id

        self._service = build("calendar", "v3", credentials=creds)
        self._tasks_service = build("tasks", "v1", credentials=creds)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def get_event(self, event_id: str) -> calendar_client_api.Event:
        """
        Return an event by ID from the configured calendar.

        The raw JSON response from Google is passed directly into the ``GoogleCalendarEvent``
        constructor where it is parsed and flattened into the ``Event`` interface.
        """
        svc = self._require_calendar_service()
        try:
            response = (
                svc.events()
                .get(
                    calendarId=self.calendar_id,
                    eventId=event_id,
                )
                .execute()
            )
        except HttpError as e:
            status = getattr(e, "status_code", e.resp.status if hasattr(e, "resp") else None)
            if status in (404, 410):
                msg = f"Event {event_id} not found."
                raise calendar_client_api.EventNotFoundError(msg) from e
            msg = f"HTTP Error {status}: {e}"
            raise calendar_client_api.CalendarOperationError(msg) from e

        if response.get("status") == "cancelled":
            msg = f"Event {event_id} not found (cancelled)."
            raise calendar_client_api.EventNotFoundError(msg)

        return GoogleCalendarEvent(response)

    def _format_datetime(self, dt: datetime) -> dict[str, str]:
        """
        Format a datetime into a Google Calendar API time block.

        Unwraps Python ``datetime`` objects into Google's required structure:
        ``{"dateTime": "<ISO 8601>", "timeZone": "<tz name>"}``.
        """
        tz_name = dt.tzinfo.tzname(None) if dt.tzinfo else "UTC"
        return {
            "dateTime": dt.isoformat(),
            "timeZone": tz_name or "UTC",
        }

    def _event_to_dict(
        self,
        event: calendar_client_api.Event,
    ) -> dict[str, str | dict[str, str]]:
        """
        Convert a standard Event to a Google Calendar request body.

        Performs the inverse translation of ``GoogleCalendarEvent``: unwraps typed properties
        back into the nested dictionary structure that the Google Calendar API expects.
        """
        body: dict[str, str | dict[str, str]] = {
            "summary": event.title,
            "start": self._format_datetime(event.start_time),
            "end": self._format_datetime(event.end_time),
        }
        if event.location is not None:
            body["location"] = event.location
        if event.description is not None:
            body["description"] = event.description
        return body

    def create_event(
        self,
        event: calendar_client_api.Event,
    ) -> calendar_client_api.Event:
        """
        Create a new event in the configured calendar.

        Translates the domain ``Event`` into a Google API request body via ``_event_to_dict``
        and issues a POST via ``events().insert()``.
        """
        svc = self._require_calendar_service()
        body = self._event_to_dict(event)
        response = (
            svc.events()
            .insert(
                calendarId=self.calendar_id,
                body=body,
            )
            .execute()
        )
        return GoogleCalendarEvent(response)

    def update_event(
        self,
        event: calendar_client_api.Event,
    ) -> calendar_client_api.Event:
        """
        Update an existing event in the configured calendar.

        Issues a PUT via ``events().update()``, replacing the entire event body with the new
        payload derived from ``_event_to_dict``.
        """
        svc = self._require_calendar_service()
        body = self._event_to_dict(event)
        response = (
            svc.events()
            .update(
                calendarId=self.calendar_id,
                eventId=event.id,
                body=body,
            )
            .execute()
        )
        return GoogleCalendarEvent(response)

    def delete_event(self, event_id: str) -> None:
        """
        Delete an event by ID from the configured calendar.

        Issues a DELETE via ``events().delete()``. The underlying Google SDK raises ``HttpError``
        if the event does not exist or the user lacks permissions.
        """
        svc = self._require_calendar_service()
        try:
            svc.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
            ).execute()
        except HttpError as e:
            status = getattr(e, "status_code", e.resp.status if hasattr(e, "resp") else None)
            if status in (404, 410):
                msg = f"Event {event_id} not found."
                raise calendar_client_api.EventNotFoundError(msg) from e
            msg = f"HTTP Error {status}: {e}"
            raise calendar_client_api.CalendarOperationError(msg) from e

    def get_events(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> Iterator[calendar_client_api.Event]:
        """
        Yield events in the provided time window from the configured calendar.

        Queries ``events().list()`` with ``timeMin``/``timeMax`` bounds.
        Implements automatic pagination: enters a loop yielding ``GoogleCalendarEvent`` objects one
        by one as a generator, and fetches the next page if ``nextPageToken`` is present.
        """
        svc = self._require_calendar_service()
        page_token = None
        while True:
            events_result = (
                svc.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=start_time.isoformat(),
                    timeMax=end_time.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                    pageToken=page_token,
                )
                .execute()
            )

            for event in events_result.get("items", []):
                yield GoogleCalendarEvent(event)

            page_token = events_result.get("nextPageToken")
            if not page_token:
                break

    def from_raw_data(self, raw_data: str) -> calendar_client_api.Event:
        """
        Construct an Event from raw JSON without making an API call.

        Useful for reconstructing events from a database cache or webhook payload.
        """
        data = json.loads(raw_data)
        return GoogleCalendarEvent(data)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    def get_task(self, task_id: str) -> calendar_client_api.Task:
        """
        Return a task by ID.

        The raw response is wrapped in ``GoogleCalendarTask``, which translates Google's
        ``"needsAction"``/``"completed"`` string statuses into the boolean ``is_completed``
        property.
        """
        svc = self._require_tasks_service()
        try:
            response = (
                svc.tasks()
                .get(
                    tasklist=self.tasklist_id,
                    task=task_id,
                )
                .execute()
            )
        except HttpError as e:
            status = getattr(e, "status_code", e.resp.status if hasattr(e, "resp") else None)
            if status in (404, 410):
                msg = f"Task {task_id} not found."
                raise calendar_client_api.TaskNotFoundError(msg) from e
            msg = f"HTTP Error {status}: {e}"
            raise calendar_client_api.CalendarOperationError(msg) from e

        if response.get("deleted") is True or response.get("hidden") is True:
            msg = f"Task {task_id} not found (deleted/hidden)."
            raise calendar_client_api.TaskNotFoundError(msg)

        return GoogleCalendarTask(response)

    def _task_to_dict(self, task: calendar_client_api.Task) -> dict[str, str]:
        """
        Convert a standard Task to a Google Tasks request body.

        Google Tasks requires RFC 3339 timestamps ending in ``.000Z`` (UTC). This helper converts
        the ``end_time`` to UTC, strips timezone info, and formats with the required suffix.
        """
        # Google Tasks API requires RFC 3339 with trailing Z (UTC).
        # Convert to UTC, strip tzinfo, then format with .000Z suffix.
        due_dt = task.end_time
        if due_dt.tzinfo is not None:
            due_dt = due_dt.astimezone(tz=UTC).replace(tzinfo=None)
        body: dict[str, str] = {
            "title": task.title,
            "due": due_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "status": "completed" if task.is_completed else "needsAction",
        }
        if task.description is not None:
            body["notes"] = task.description
        return body

    def create_task(self, task: calendar_client_api.Task) -> calendar_client_api.Task:
        """
        Create a new task.

        Translates the domain ``Task`` into RFC 3339 format via ``_task_to_dict`` and issues a POST
        via ``tasks().insert()``.
        """
        svc = self._require_tasks_service()
        body = self._task_to_dict(task)
        response = (
            svc.tasks()
            .insert(
                tasklist=self.tasklist_id,
                body=body,
            )
            .execute()
        )
        return GoogleCalendarTask(response)

    def update_task(self, task: calendar_client_api.Task) -> calendar_client_api.Task:
        """
        Update an existing task.

        Injects ``task.id`` back into the request body and issues a PUT via ``tasks().update()``.
        """
        svc = self._require_tasks_service()
        body = self._task_to_dict(task)
        body["id"] = task.id
        response = (
            svc.tasks()
            .update(
                tasklist=self.tasklist_id,
                task=task.id,
                body=body,
            )
            .execute()
        )
        return GoogleCalendarTask(response)

    def delete_task(self, task_id: str) -> None:
        """Delete a task by ID."""
        svc = self._require_tasks_service()
        try:
            svc.tasks().delete(
                tasklist=self.tasklist_id,
                task=task_id,
            ).execute()
        except HttpError as e:
            status = getattr(e, "status_code", e.resp.status if hasattr(e, "resp") else None)
            if status in (404, 410):
                msg = f"Task {task_id} not found."
                raise calendar_client_api.TaskNotFoundError(msg) from e
            msg = f"HTTP Error {status}: {e}"
            raise calendar_client_api.CalendarOperationError(msg) from e

    def get_tasks(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> Iterator[calendar_client_api.Task]:
        """
        Yield tasks in the provided time window.

        Queries ``tasks().list()`` with ``dueMin``/``dueMax`` bounds (with manually appended
        ``"Z"`` suffix for UTC). Handles pagination transparently via ``nextPageToken``.
        """
        svc = self._require_tasks_service()
        page_token = None
        while True:
            tasks_result = (
                svc.tasks()
                .list(
                    tasklist=self.tasklist_id,
                    dueMin=start_time.isoformat(),
                    dueMax=end_time.isoformat(),
                    showCompleted=True,
                    pageToken=page_token,
                )
                .execute()
            )

            for task in tasks_result.get("items", []):
                yield GoogleCalendarTask(task)

            page_token = tasks_result.get("nextPageToken")
            if not page_token:
                break

    def mark_task_completed(self, task_id: str) -> None:
        """
        Mark a task as completed.

        Uses a read-modify-write pattern: fetches the existing task first to preserve all
        properties (title, due date, etc.), sets ``"status"`` to ``"completed"``, and sends the
        full modified body back via ``tasks().update()``. This avoids the Google Tasks API
        overwriting omitted fields with nulls.
        """
        svc = self._require_tasks_service()
        # Get existing properties first to avoid un-setting title, etc.
        existing = (
            svc.tasks()
            .get(
                tasklist=self.tasklist_id,
                task=task_id,
            )
            .execute()
        )

        existing["status"] = "completed"

        svc.tasks().update(
            tasklist=self.tasklist_id,
            task=task_id,
            body=existing,
        ).execute()


def get_client_impl() -> calendar_client_api.Client:
    """Return a configured GoogleCalendarClient instance."""
    return GoogleCalendarClient()


def register() -> None:
    """
    Register the Google Calendar client implementation.

    Overwrites ``calendar_client_api.get_client`` to point to this module's
    ``get_client_impl``, enabling dependency injection.
    """
    calendar_client_api.get_client = get_client_impl
