from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.describe_whoami_response import DescribeWhoamiResponse
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/whoami",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DescribeWhoamiResponse | ErrorModel:
    if response.status_code == 200:
        response_200 = DescribeWhoamiResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DescribeWhoamiResponse | ErrorModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[DescribeWhoamiResponse | ErrorModel]:
    """Describe whoami

     Returns an RS256-signed identity JWT for the authenticated user. The token's signature can be
    verified using the public keys served at /.well-known/jwks.json. Intended for downstream consumers
    (e.g. Convex) that need a verifiable user identity.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeWhoamiResponse | ErrorModel]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
) -> DescribeWhoamiResponse | ErrorModel | None:
    """Describe whoami

     Returns an RS256-signed identity JWT for the authenticated user. The token's signature can be
    verified using the public keys served at /.well-known/jwks.json. Intended for downstream consumers
    (e.g. Convex) that need a verifiable user identity.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeWhoamiResponse | ErrorModel
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[DescribeWhoamiResponse | ErrorModel]:
    """Describe whoami

     Returns an RS256-signed identity JWT for the authenticated user. The token's signature can be
    verified using the public keys served at /.well-known/jwks.json. Intended for downstream consumers
    (e.g. Convex) that need a verifiable user identity.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeWhoamiResponse | ErrorModel]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
) -> DescribeWhoamiResponse | ErrorModel | None:
    """Describe whoami

     Returns an RS256-signed identity JWT for the authenticated user. The token's signature can be
    verified using the public keys served at /.well-known/jwks.json. Intended for downstream consumers
    (e.g. Convex) that need a verifiable user identity.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeWhoamiResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
