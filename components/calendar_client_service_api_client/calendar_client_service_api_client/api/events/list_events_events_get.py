import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.event_response import EventResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    session_id: None | str | Unset = UNSET,
) -> dict[str, Any]:

    cookies = {}
    if session_id is not UNSET:
        cookies["session_id"] = session_id

    params: dict[str, Any] = {}

    json_start_time = start_time.isoformat()
    params["start_time"] = json_start_time

    json_end_time = end_time.isoformat()
    params["end_time"] = json_end_time

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/events",
        "params": params,
        "cookies": cookies,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[EventResponse] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = EventResponse.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[HTTPValidationError | list[EventResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    session_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | list[EventResponse]]:
    """List events in a time range

     Return all events between ``start_time`` and ``end_time``.

    TODO: Implement using ``client.get_events(start_time, end_time)``.

    Args:
        start_time (datetime.datetime):
        end_time (datetime.datetime):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[EventResponse]]
    """

    kwargs = _get_kwargs(
        start_time=start_time,
        end_time=end_time,
        session_id=session_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    session_id: None | str | Unset = UNSET,
) -> HTTPValidationError | list[EventResponse] | None:
    """List events in a time range

     Return all events between ``start_time`` and ``end_time``.

    TODO: Implement using ``client.get_events(start_time, end_time)``.

    Args:
        start_time (datetime.datetime):
        end_time (datetime.datetime):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[EventResponse]
    """

    return sync_detailed(
        client=client,
        start_time=start_time,
        end_time=end_time,
        session_id=session_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    session_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | list[EventResponse]]:
    """List events in a time range

     Return all events between ``start_time`` and ``end_time``.

    TODO: Implement using ``client.get_events(start_time, end_time)``.

    Args:
        start_time (datetime.datetime):
        end_time (datetime.datetime):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[EventResponse]]
    """

    kwargs = _get_kwargs(
        start_time=start_time,
        end_time=end_time,
        session_id=session_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    session_id: None | str | Unset = UNSET,
) -> HTTPValidationError | list[EventResponse] | None:
    """List events in a time range

     Return all events between ``start_time`` and ``end_time``.

    TODO: Implement using ``client.get_events(start_time, end_time)``.

    Args:
        start_time (datetime.datetime):
        end_time (datetime.datetime):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[EventResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            start_time=start_time,
            end_time=end_time,
            session_id=session_id,
        )
    ).parsed
