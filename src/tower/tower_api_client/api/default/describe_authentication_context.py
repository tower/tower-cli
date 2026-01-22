from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.describe_authentication_context_body import (
    DescribeAuthenticationContextBody,
)
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/user/auth-context",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DescribeAuthenticationContextBody | ErrorModel:
    if response.status_code == 200:
        response_200 = DescribeAuthenticationContextBody.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DescribeAuthenticationContextBody | ErrorModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[DescribeAuthenticationContextBody | ErrorModel]:
    """Describe authentication context

     This API endpoint returns information about the current authentication context for the user that's
    used for various internal processes in Tower UI.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeAuthenticationContextBody | ErrorModel]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
) -> DescribeAuthenticationContextBody | ErrorModel | None:
    """Describe authentication context

     This API endpoint returns information about the current authentication context for the user that's
    used for various internal processes in Tower UI.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeAuthenticationContextBody | ErrorModel
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[DescribeAuthenticationContextBody | ErrorModel]:
    """Describe authentication context

     This API endpoint returns information about the current authentication context for the user that's
    used for various internal processes in Tower UI.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeAuthenticationContextBody | ErrorModel]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
) -> DescribeAuthenticationContextBody | ErrorModel | None:
    """Describe authentication context

     This API endpoint returns information about the current authentication context for the user that's
    used for various internal processes in Tower UI.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeAuthenticationContextBody | ErrorModel
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
