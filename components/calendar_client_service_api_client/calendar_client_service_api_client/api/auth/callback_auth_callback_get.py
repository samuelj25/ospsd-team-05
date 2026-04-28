from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.auth_status_response import AuthStatusResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    code: str,
    state: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["code"] = code

    json_state: None | str | Unset
    if isinstance(state, Unset):
        json_state = UNSET
    else:
        json_state = state
    params["state"] = json_state

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/auth/callback",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AuthStatusResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AuthStatusResponse.from_dict(response.json())

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
) -> Response[AuthStatusResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    code: str,
    state: None | str | Unset = UNSET,
) -> Response[AuthStatusResponse | HTTPValidationError]:
    """Handle OAuth 2.0 callback

     Exchange the authorization code for tokens and create a session.

    Google redirects the user here after they grant (or deny) access.  This
    endpoint exchanges the ``code`` for access and refresh tokens, stores them
    under a new session key, and sets a ``session_id`` cookie on the response.

    Args:
        code: The authorization code from the Google redirect.
        response: The FastAPI response object (used to set the session cookie).
        oauth_manager: The singleton OAuth manager (injected by FastAPI).
        state: Optional state parameter used to map the session back to a Slack user.

    Returns:
        An :class:`AuthStatusResponse` with ``authenticated=True`` and the new
        ``session_id``.

    Raises:
        HTTPException(400): If the code exchange fails (e.g. code already used,
            invalid, or mismatched redirect URI).

    Args:
        code (str):
        state (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthStatusResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        code=code,
        state=state,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    code: str,
    state: None | str | Unset = UNSET,
) -> AuthStatusResponse | HTTPValidationError | None:
    """Handle OAuth 2.0 callback

     Exchange the authorization code for tokens and create a session.

    Google redirects the user here after they grant (or deny) access.  This
    endpoint exchanges the ``code`` for access and refresh tokens, stores them
    under a new session key, and sets a ``session_id`` cookie on the response.

    Args:
        code: The authorization code from the Google redirect.
        response: The FastAPI response object (used to set the session cookie).
        oauth_manager: The singleton OAuth manager (injected by FastAPI).
        state: Optional state parameter used to map the session back to a Slack user.

    Returns:
        An :class:`AuthStatusResponse` with ``authenticated=True`` and the new
        ``session_id``.

    Raises:
        HTTPException(400): If the code exchange fails (e.g. code already used,
            invalid, or mismatched redirect URI).

    Args:
        code (str):
        state (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthStatusResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        code=code,
        state=state,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    code: str,
    state: None | str | Unset = UNSET,
) -> Response[AuthStatusResponse | HTTPValidationError]:
    """Handle OAuth 2.0 callback

     Exchange the authorization code for tokens and create a session.

    Google redirects the user here after they grant (or deny) access.  This
    endpoint exchanges the ``code`` for access and refresh tokens, stores them
    under a new session key, and sets a ``session_id`` cookie on the response.

    Args:
        code: The authorization code from the Google redirect.
        response: The FastAPI response object (used to set the session cookie).
        oauth_manager: The singleton OAuth manager (injected by FastAPI).
        state: Optional state parameter used to map the session back to a Slack user.

    Returns:
        An :class:`AuthStatusResponse` with ``authenticated=True`` and the new
        ``session_id``.

    Raises:
        HTTPException(400): If the code exchange fails (e.g. code already used,
            invalid, or mismatched redirect URI).

    Args:
        code (str):
        state (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthStatusResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        code=code,
        state=state,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    code: str,
    state: None | str | Unset = UNSET,
) -> AuthStatusResponse | HTTPValidationError | None:
    """Handle OAuth 2.0 callback

     Exchange the authorization code for tokens and create a session.

    Google redirects the user here after they grant (or deny) access.  This
    endpoint exchanges the ``code`` for access and refresh tokens, stores them
    under a new session key, and sets a ``session_id`` cookie on the response.

    Args:
        code: The authorization code from the Google redirect.
        response: The FastAPI response object (used to set the session cookie).
        oauth_manager: The singleton OAuth manager (injected by FastAPI).
        state: Optional state parameter used to map the session back to a Slack user.

    Returns:
        An :class:`AuthStatusResponse` with ``authenticated=True`` and the new
        ``session_id``.

    Raises:
        HTTPException(400): If the code exchange fails (e.g. code already used,
            invalid, or mismatched redirect URI).

    Args:
        code (str):
        state (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthStatusResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            code=code,
            state=state,
        )
    ).parsed
