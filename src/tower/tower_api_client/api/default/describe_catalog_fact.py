from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.describe_catalog_fact_response import DescribeCatalogFactResponse
from ...models.error_model import ErrorModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    catalog: str,
    name: str,
    *,
    environment: str | Unset = "default",
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["environment"] = environment

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/catalogs/{catalog}/facts/{name}".format(
            catalog=quote(str(catalog), safe=""),
            name=quote(str(name), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DescribeCatalogFactResponse | ErrorModel:
    if response.status_code == 200:
        response_200 = DescribeCatalogFactResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DescribeCatalogFactResponse | ErrorModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    catalog: str,
    name: str,
    *,
    client: AuthenticatedClient,
    environment: str | Unset = "default",
) -> Response[DescribeCatalogFactResponse | ErrorModel]:
    """Describe a catalog fact

     Returns a single semantic metadata fact addressed by its name within a catalog.

    Args:
        catalog (str): The name of the catalog.
        name (str): The name of the fact.
        environment (str | Unset): The environment of the catalog. Note that if a catalog with the
            requested name doesn't exist in the requested environment, the fact from the catalog with
            the same name in the default environment will be returned. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeCatalogFactResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        name=name,
        environment=environment,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    catalog: str,
    name: str,
    *,
    client: AuthenticatedClient,
    environment: str | Unset = "default",
) -> DescribeCatalogFactResponse | ErrorModel | None:
    """Describe a catalog fact

     Returns a single semantic metadata fact addressed by its name within a catalog.

    Args:
        catalog (str): The name of the catalog.
        name (str): The name of the fact.
        environment (str | Unset): The environment of the catalog. Note that if a catalog with the
            requested name doesn't exist in the requested environment, the fact from the catalog with
            the same name in the default environment will be returned. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeCatalogFactResponse | ErrorModel
    """

    return sync_detailed(
        catalog=catalog,
        name=name,
        client=client,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    catalog: str,
    name: str,
    *,
    client: AuthenticatedClient,
    environment: str | Unset = "default",
) -> Response[DescribeCatalogFactResponse | ErrorModel]:
    """Describe a catalog fact

     Returns a single semantic metadata fact addressed by its name within a catalog.

    Args:
        catalog (str): The name of the catalog.
        name (str): The name of the fact.
        environment (str | Unset): The environment of the catalog. Note that if a catalog with the
            requested name doesn't exist in the requested environment, the fact from the catalog with
            the same name in the default environment will be returned. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeCatalogFactResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        name=name,
        environment=environment,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    catalog: str,
    name: str,
    *,
    client: AuthenticatedClient,
    environment: str | Unset = "default",
) -> DescribeCatalogFactResponse | ErrorModel | None:
    """Describe a catalog fact

     Returns a single semantic metadata fact addressed by its name within a catalog.

    Args:
        catalog (str): The name of the catalog.
        name (str): The name of the fact.
        environment (str | Unset): The environment of the catalog. Note that if a catalog with the
            requested name doesn't exist in the requested environment, the fact from the catalog with
            the same name in the default environment will be returned. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeCatalogFactResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            catalog=catalog,
            name=name,
            client=client,
            environment=environment,
        )
    ).parsed
