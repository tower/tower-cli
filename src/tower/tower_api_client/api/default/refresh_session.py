from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.refresh_session_params import RefreshSessionParams
from ...models.refresh_session_response import RefreshSessionResponse
from ...types import Response


def _get_kwargs(
    *,
    body: RefreshSessionParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/session/refresh",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[RefreshSessionResponse]:
    if response.status_code == 200:
        response_200 = RefreshSessionResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[RefreshSessionResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: RefreshSessionParams,
) -> Response[RefreshSessionResponse]:
    """Refresh session

     Returns a new session based on the supplied authentication context. This is helpful when clients
    want to use POST instead of GET to check session information.

    Args:
        body (RefreshSessionParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[RefreshSessionResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: RefreshSessionParams,
) -> Optional[RefreshSessionResponse]:
    """Refresh session

     Returns a new session based on the supplied authentication context. This is helpful when clients
    want to use POST instead of GET to check session information.

    Args:
        body (RefreshSessionParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        RefreshSessionResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: RefreshSessionParams,
) -> Response[RefreshSessionResponse]:
    """Refresh session

     Returns a new session based on the supplied authentication context. This is helpful when clients
    want to use POST instead of GET to check session information.

    Args:
        body (RefreshSessionParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[RefreshSessionResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: RefreshSessionParams,
) -> Optional[RefreshSessionResponse]:
    """Refresh session

     Returns a new session based on the supplied authentication context. This is helpful when clients
    want to use POST instead of GET to check session information.

    Args:
        body (RefreshSessionParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        RefreshSessionResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
