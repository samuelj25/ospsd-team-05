"""Google Calendar Client implementation."""

import json
import os
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import calendar_client_api
from googleapiclient.discovery import build

from google_calendar_client_impl.auth import get_credentials
from google_calendar_client_impl.event_impl import GoogleCalendarEvent
from google_calendar_client_impl.task_impl import GoogleCalendarTask

_NOT_CONNECTED_MSG = "Client is not connected. Call connect() first."


class GoogleCalendarClient(calendar_client_api.Client):
    """Concrete implementation of the Client abstraction using Google Calendar API."""

    def __init__(
        self,
        calendar_id: str = "primary",
        tasklist_id: str = "@default",
        credentials_path: str | None = None,
        token_path: str | None = None,
    ) -> None:
        """
        Initialize the Google Calendar client.

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
        """Authenticate via OAuth 2.0 and build API service objects."""
        env_calendar_id = os.environ.get("GOOGLE_CALENDAR_ID")
        if env_calendar_id and self.calendar_id == "primary":
            self.calendar_id = env_calendar_id

        creds = get_credentials(
            credentials_path=self._credentials_path,
            token_path=self._token_path,
        )
        self._service = build("calendar", "v3", credentials=creds)
        self._tasks_service = build("tasks", "v1", credentials=creds)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def get_event(self, event_id: str) -> calendar_client_api.Event:
        """Return an event by ID from the configured calendar."""
        svc = self._require_calendar_service()
        response = svc.events().get(
            calendarId=self.calendar_id,
            eventId=event_id,
        ).execute()
        return GoogleCalendarEvent(response)

    def _format_datetime(self, dt: datetime) -> dict[str, str]:
        """Format datetime to Google Calendar API compatible format."""
        tz_name = dt.tzinfo.tzname(None) if dt.tzinfo else "UTC"
        return {
            "dateTime": dt.isoformat(),
            "timeZone": tz_name or "UTC",
        }

    def _event_to_dict(
        self, event: calendar_client_api.Event,
    ) -> dict[str, str | dict[str, str]]:
        """Convert a standard Event to Google Calendar dictionary format."""
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
        self, event: calendar_client_api.Event,
    ) -> calendar_client_api.Event:
        """Create a new event in the configured calendar."""
        svc = self._require_calendar_service()
        body = self._event_to_dict(event)
        response = svc.events().insert(
            calendarId=self.calendar_id,
            body=body,
        ).execute()
        return GoogleCalendarEvent(response)

    def update_event(
        self, event: calendar_client_api.Event,
    ) -> calendar_client_api.Event:
        """Update an existing event in the configured calendar."""
        svc = self._require_calendar_service()
        body = self._event_to_dict(event)
        response = svc.events().update(
            calendarId=self.calendar_id,
            eventId=event.id,
            body=body,
        ).execute()
        return GoogleCalendarEvent(response)

    def delete_event(self, event_id: str) -> None:
        """Delete an event by ID from the configured calendar."""
        svc = self._require_calendar_service()
        svc.events().delete(
            calendarId=self.calendar_id,
            eventId=event_id,
        ).execute()

    def get_events(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> Iterator[calendar_client_api.Event]:
        """Yield events in the provided time window from the configured calendar."""
        svc = self._require_calendar_service()
        page_token = None
        while True:
            events_result = svc.events().list(
                calendarId=self.calendar_id,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                pageToken=page_token,
            ).execute()

            for event in events_result.get("items", []):
                yield GoogleCalendarEvent(event)

            page_token = events_result.get("nextPageToken")
            if not page_token:
                break

    def from_raw_data(self, raw_data: str) -> calendar_client_api.Event:
        """Construct an Event object from raw JSON data."""
        data = json.loads(raw_data)
        return GoogleCalendarEvent(data)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    def get_task(self, task_id: str) -> calendar_client_api.Task:
        """Return a task by ID."""
        svc = self._require_tasks_service()
        response = svc.tasks().get(
            tasklist=self.tasklist_id,
            task=task_id,
        ).execute()
        return GoogleCalendarTask(response)

    def _task_to_dict(self, task: calendar_client_api.Task) -> dict[str, str]:
        """Convert standard Task to Google Tasks dict format."""
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
        """Create a new task."""
        svc = self._require_tasks_service()
        body = self._task_to_dict(task)
        response = svc.tasks().insert(
            tasklist=self.tasklist_id,
            body=body,
        ).execute()
        return GoogleCalendarTask(response)

    def update_task(self, task: calendar_client_api.Task) -> calendar_client_api.Task:
        """Update an existing task."""
        svc = self._require_tasks_service()
        body = self._task_to_dict(task)
        body["id"] = task.id
        response = svc.tasks().update(
            tasklist=self.tasklist_id,
            task=task.id,
            body=body,
        ).execute()
        return GoogleCalendarTask(response)

    def delete_task(self, task_id: str) -> None:
        """Delete a task by ID."""
        svc = self._require_tasks_service()
        svc.tasks().delete(
            tasklist=self.tasklist_id,
            task=task_id,
        ).execute()

    def get_tasks(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> Iterator[calendar_client_api.Task]:
        """Yield tasks in the provided time window."""
        svc = self._require_tasks_service()
        page_token = None
        while True:
            tasks_result = svc.tasks().list(
                tasklist=self.tasklist_id,
                dueMin=start_time.isoformat() + "Z",
                dueMax=end_time.isoformat() + "Z",
                showCompleted=True,
                pageToken=page_token,
            ).execute()

            for task in tasks_result.get("items", []):
                yield GoogleCalendarTask(task)

            page_token = tasks_result.get("nextPageToken")
            if not page_token:
                break

    def mark_task_completed(self, task_id: str) -> None:
        """Mark a task as completed."""
        svc = self._require_tasks_service()
        # Get existing properties first to avoid un-setting title, etc.
        existing = svc.tasks().get(
            tasklist=self.tasklist_id, task=task_id,
        ).execute()

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
    """Register the Google Calendar client implementation."""
    calendar_client_api.get_client = get_client_impl
