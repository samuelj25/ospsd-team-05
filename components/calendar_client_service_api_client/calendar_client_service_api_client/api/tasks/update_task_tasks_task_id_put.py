from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.task_response import TaskResponse
from ...models.task_update import TaskUpdate
from ...types import UNSET, Response, Unset


def _get_kwargs(
    task_id: str,
    *,
    body: TaskUpdate,
    session_id: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    cookies = {}
    if session_id is not UNSET:
        cookies["session_id"] = session_id

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/tasks/{task_id}".format(
            task_id=quote(str(task_id), safe=""),
        ),
        "cookies": cookies,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TaskResponse | None:
    if response.status_code == 200:
        response_200 = TaskResponse.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | TaskResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    task_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TaskUpdate,
    session_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | TaskResponse]:
    """Update a task

     Update the task identified by ``task_id`` with data from ``payload``.

    Args:
        task_id (str):
        session_id (None | str | Unset):
        body (TaskUpdate): Payload for updating an existing task.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TaskResponse]
    """

    kwargs = _get_kwargs(
        task_id=task_id,
        body=body,
        session_id=session_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    task_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TaskUpdate,
    session_id: None | str | Unset = UNSET,
) -> HTTPValidationError | TaskResponse | None:
    """Update a task

     Update the task identified by ``task_id`` with data from ``payload``.

    Args:
        task_id (str):
        session_id (None | str | Unset):
        body (TaskUpdate): Payload for updating an existing task.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TaskResponse
    """

    return sync_detailed(
        task_id=task_id,
        client=client,
        body=body,
        session_id=session_id,
    ).parsed


async def asyncio_detailed(
    task_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TaskUpdate,
    session_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | TaskResponse]:
    """Update a task

     Update the task identified by ``task_id`` with data from ``payload``.

    Args:
        task_id (str):
        session_id (None | str | Unset):
        body (TaskUpdate): Payload for updating an existing task.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TaskResponse]
    """

    kwargs = _get_kwargs(
        task_id=task_id,
        body=body,
        session_id=session_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    task_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TaskUpdate,
    session_id: None | str | Unset = UNSET,
) -> HTTPValidationError | TaskResponse | None:
    """Update a task

     Update the task identified by ``task_id`` with data from ``payload``.

    Args:
        task_id (str):
        session_id (None | str | Unset):
        body (TaskUpdate): Payload for updating an existing task.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TaskResponse
    """

    return (
        await asyncio_detailed(
            task_id=task_id,
            client=client,
            body=body,
            session_id=session_id,
        )
    ).parsed
