from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
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

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | RefreshSessionResponse:
    if response.status_code == 200:
        response_200 = RefreshSessionResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | RefreshSessionResponse]:
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
) -> Response[ErrorModel | RefreshSessionResponse]:
    """Refresh session

     If your access tokens expire, this API endpoint takes a Refresh Token and returns a new set of
    Access Tokens for your session. Note that we don't rotate the Refresh Token itself, and it's not
    returned by this API endpoint.

    Args:
        body (RefreshSessionParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | RefreshSessionResponse]
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
) -> ErrorModel | RefreshSessionResponse | None:
    """Refresh session

     If your access tokens expire, this API endpoint takes a Refresh Token and returns a new set of
    Access Tokens for your session. Note that we don't rotate the Refresh Token itself, and it's not
    returned by this API endpoint.

    Args:
        body (RefreshSessionParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | RefreshSessionResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: RefreshSessionParams,
) -> Response[ErrorModel | RefreshSessionResponse]:
    """Refresh session

     If your access tokens expire, this API endpoint takes a Refresh Token and returns a new set of
    Access Tokens for your session. Note that we don't rotate the Refresh Token itself, and it's not
    returned by this API endpoint.

    Args:
        body (RefreshSessionParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | RefreshSessionResponse]
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
) -> ErrorModel | RefreshSessionResponse | None:
    """Refresh session

     If your access tokens expire, this API endpoint takes a Refresh Token and returns a new set of
    Access Tokens for your session. Note that we don't rotate the Refresh Token itself, and it's not
    returned by this API endpoint.

    Args:
        body (RefreshSessionParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | RefreshSessionResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
