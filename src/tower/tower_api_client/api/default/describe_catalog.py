from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.describe_catalog_response import DescribeCatalogResponse
from ...models.error_model import ErrorModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    environment: str | Unset = "default",
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["environment"] = environment

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/catalogs/{name}".format(
            name=quote(str(name), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DescribeCatalogResponse | ErrorModel:
    if response.status_code == 200:
        response_200 = DescribeCatalogResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DescribeCatalogResponse | ErrorModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    environment: str | Unset = "default",
) -> Response[DescribeCatalogResponse | ErrorModel]:
    """Describe catalog

     Returns details for a specific catalog, including its property names and previews.

    Args:
        name (str): The name of the catalog.
        environment (str | Unset): The environment of the catalog. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeCatalogResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        name=name,
        environment=environment,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient,
    environment: str | Unset = "default",
) -> DescribeCatalogResponse | ErrorModel | None:
    """Describe catalog

     Returns details for a specific catalog, including its property names and previews.

    Args:
        name (str): The name of the catalog.
        environment (str | Unset): The environment of the catalog. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeCatalogResponse | ErrorModel
    """

    return sync_detailed(
        name=name,
        client=client,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    environment: str | Unset = "default",
) -> Response[DescribeCatalogResponse | ErrorModel]:
    """Describe catalog

     Returns details for a specific catalog, including its property names and previews.

    Args:
        name (str): The name of the catalog.
        environment (str | Unset): The environment of the catalog. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeCatalogResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        name=name,
        environment=environment,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
    environment: str | Unset = "default",
) -> DescribeCatalogResponse | ErrorModel | None:
    """Describe catalog

     Returns details for a specific catalog, including its property names and previews.

    Args:
        name (str): The name of the catalog.
        environment (str | Unset): The environment of the catalog. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeCatalogResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            environment=environment,
        )
    ).parsed
