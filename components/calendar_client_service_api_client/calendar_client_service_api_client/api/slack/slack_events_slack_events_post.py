from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.slack_events_slack_events_post_response_slack_events_slack_events_post import (
    SlackEventsSlackEventsPostResponseSlackEventsSlackEventsPost,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/slack/events",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> SlackEventsSlackEventsPostResponseSlackEventsSlackEventsPost | None:
    if response.status_code == 200:
        response_200 = SlackEventsSlackEventsPostResponseSlackEventsSlackEventsPost.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[SlackEventsSlackEventsPostResponseSlackEventsSlackEventsPost]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[SlackEventsSlackEventsPostResponseSlackEventsSlackEventsPost]:
    r"""Slack Event API webhook

     Handle incoming Slack Events API payloads.

    Supports:
    - ``url_verification`` challenges (one-time setup).
    - ``message`` events: dispatches AI + calendar tool loop in the background
      and posts the reply to Slack.

    Returns HTTP 200 immediately to satisfy Slack's 3-second timeout.

    Args:
        request: The incoming FastAPI request.
        background_tasks: FastAPI background task queue.
        oauth_manager: The OAuth manager for credential lookup.
        ai_client: GeminiAIClient (injected).
        chat_client: SlackChatAdapter (injected).

    Returns:
        Empty dict ``{}`` for message events, or ``{\"challenge\": \"...\"}`` for
        url_verification.

    Raises:
        HTTPException(403): If the Slack request signature is invalid.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[SlackEventsSlackEventsPostResponseSlackEventsSlackEventsPost]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> SlackEventsSlackEventsPostResponseSlackEventsSlackEventsPost | None:
    r"""Slack Event API webhook

     Handle incoming Slack Events API payloads.

    Supports:
    - ``url_verification`` challenges (one-time setup).
    - ``message`` events: dispatches AI + calendar tool loop in the background
      and posts the reply to Slack.

    Returns HTTP 200 immediately to satisfy Slack's 3-second timeout.

    Args:
        request: The incoming FastAPI request.
        background_tasks: FastAPI background task queue.
        oauth_manager: The OAuth manager for credential lookup.
        ai_client: GeminiAIClient (injected).
        chat_client: SlackChatAdapter (injected).

    Returns:
        Empty dict ``{}`` for message events, or ``{\"challenge\": \"...\"}`` for
        url_verification.

    Raises:
        HTTPException(403): If the Slack request signature is invalid.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        SlackEventsSlackEventsPostResponseSlackEventsSlackEventsPost
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[SlackEventsSlackEventsPostResponseSlackEventsSlackEventsPost]:
    r"""Slack Event API webhook

     Handle incoming Slack Events API payloads.

    Supports:
    - ``url_verification`` challenges (one-time setup).
    - ``message`` events: dispatches AI + calendar tool loop in the background
      and posts the reply to Slack.

    Returns HTTP 200 immediately to satisfy Slack's 3-second timeout.

    Args:
        request: The incoming FastAPI request.
        background_tasks: FastAPI background task queue.
        oauth_manager: The OAuth manager for credential lookup.
        ai_client: GeminiAIClient (injected).
        chat_client: SlackChatAdapter (injected).

    Returns:
        Empty dict ``{}`` for message events, or ``{\"challenge\": \"...\"}`` for
        url_verification.

    Raises:
        HTTPException(403): If the Slack request signature is invalid.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[SlackEventsSlackEventsPostResponseSlackEventsSlackEventsPost]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> SlackEventsSlackEventsPostResponseSlackEventsSlackEventsPost | None:
    r"""Slack Event API webhook

     Handle incoming Slack Events API payloads.

    Supports:
    - ``url_verification`` challenges (one-time setup).
    - ``message`` events: dispatches AI + calendar tool loop in the background
      and posts the reply to Slack.

    Returns HTTP 200 immediately to satisfy Slack's 3-second timeout.

    Args:
        request: The incoming FastAPI request.
        background_tasks: FastAPI background task queue.
        oauth_manager: The OAuth manager for credential lookup.
        ai_client: GeminiAIClient (injected).
        chat_client: SlackChatAdapter (injected).

    Returns:
        Empty dict ``{}`` for message events, or ``{\"challenge\": \"...\"}`` for
        url_verification.

    Raises:
        HTTPException(403): If the Slack request signature is invalid.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        SlackEventsSlackEventsPostResponseSlackEventsSlackEventsPost
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
