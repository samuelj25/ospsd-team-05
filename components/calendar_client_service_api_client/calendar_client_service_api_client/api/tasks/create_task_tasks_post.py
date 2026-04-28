from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.task_create import TaskCreate
from ...models.task_response import TaskResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: TaskCreate,
    session_id: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    cookies = {}
    if session_id is not UNSET:
        cookies["session_id"] = session_id

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/tasks",
        "cookies": cookies,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TaskResponse | None:
    if response.status_code == 201:
        response_201 = TaskResponse.from_dict(response.json())

        return response_201

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
    *,
    client: AuthenticatedClient | Client,
    body: TaskCreate,
    session_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | TaskResponse]:
    """Create a task

     Create a new task from ``payload``.

    Args:
        session_id (None | str | Unset):
        body (TaskCreate): Payload for creating a new task.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TaskResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        session_id=session_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: TaskCreate,
    session_id: None | str | Unset = UNSET,
) -> HTTPValidationError | TaskResponse | None:
    """Create a task

     Create a new task from ``payload``.

    Args:
        session_id (None | str | Unset):
        body (TaskCreate): Payload for creating a new task.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TaskResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        session_id=session_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TaskCreate,
    session_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | TaskResponse]:
    """Create a task

     Create a new task from ``payload``.

    Args:
        session_id (None | str | Unset):
        body (TaskCreate): Payload for creating a new task.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TaskResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        session_id=session_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: TaskCreate,
    session_id: None | str | Unset = UNSET,
) -> HTTPValidationError | TaskResponse | None:
    """Create a task

     Create a new task from ``payload``.

    Args:
        session_id (None | str | Unset):
        body (TaskCreate): Payload for creating a new task.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TaskResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            session_id=session_id,
        )
    ).parsed
