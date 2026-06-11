from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.describe_catalog_response import DescribeCatalogResponse
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/storage/catalogs/default",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | DescribeCatalogResponse | None:
    if response.status_code == 200:
        response_200 = DescribeCatalogResponse.from_dict(response.json())

        return response_200

    if response.status_code == 202:
        response_202 = cast(Any, None)
        return response_202

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | DescribeCatalogResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[Any | DescribeCatalogResponse]:
    """Describe default catalog

     Returns the team's default catalog, provisioning it lazily if it does not yet exist.

    When two concurrent first calls race to provision the catalog, the loser receives 202 Accepted;
    retry after a few seconds and the catalog will be ready.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DescribeCatalogResponse]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
) -> Any | DescribeCatalogResponse | None:
    """Describe default catalog

     Returns the team's default catalog, provisioning it lazily if it does not yet exist.

    When two concurrent first calls race to provision the catalog, the loser receives 202 Accepted;
    retry after a few seconds and the catalog will be ready.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DescribeCatalogResponse
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[Any | DescribeCatalogResponse]:
    """Describe default catalog

     Returns the team's default catalog, provisioning it lazily if it does not yet exist.

    When two concurrent first calls race to provision the catalog, the loser receives 202 Accepted;
    retry after a few seconds and the catalog will be ready.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DescribeCatalogResponse]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
) -> Any | DescribeCatalogResponse | None:
    """Describe default catalog

     Returns the team's default catalog, provisioning it lazily if it does not yet exist.

    When two concurrent first calls race to provision the catalog, the loser receives 202 Accepted;
    retry after a few seconds and the catalog will be ready.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DescribeCatalogResponse
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
