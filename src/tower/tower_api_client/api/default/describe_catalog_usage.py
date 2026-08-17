from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.describe_catalog_usage_response import DescribeCatalogUsageResponse
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
        "url": "/catalogs/{name}/usage".format(
            name=quote(str(name), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DescribeCatalogUsageResponse | ErrorModel | None:
    if response.status_code == 200:
        response_200 = DescribeCatalogUsageResponse.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorModel.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = ErrorModel.from_dict(response.json())

        return response_404

    if response.status_code == 422:
        response_422 = ErrorModel.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = ErrorModel.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DescribeCatalogUsageResponse | ErrorModel]:
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
) -> Response[DescribeCatalogUsageResponse | ErrorModel]:
    """Describe catalog usage

     Returns physical bytes stored by one Tower-managed catalog, including Iceberg metadata and not-yet-
    compacted snapshot history. Measurements are cached and may be temporarily unavailable; measured_at
    is null when no measurement exists. BYO and S3 Tables catalogs are not metered.

    Args:
        name (str): The name of the catalog.
        environment (str | Unset): Environment whose catalog usage to return. When it has no same-
            named catalog, usage for the catalog from default is returned instead. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeCatalogUsageResponse | ErrorModel]
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
) -> DescribeCatalogUsageResponse | ErrorModel | None:
    """Describe catalog usage

     Returns physical bytes stored by one Tower-managed catalog, including Iceberg metadata and not-yet-
    compacted snapshot history. Measurements are cached and may be temporarily unavailable; measured_at
    is null when no measurement exists. BYO and S3 Tables catalogs are not metered.

    Args:
        name (str): The name of the catalog.
        environment (str | Unset): Environment whose catalog usage to return. When it has no same-
            named catalog, usage for the catalog from default is returned instead. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeCatalogUsageResponse | ErrorModel
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
) -> Response[DescribeCatalogUsageResponse | ErrorModel]:
    """Describe catalog usage

     Returns physical bytes stored by one Tower-managed catalog, including Iceberg metadata and not-yet-
    compacted snapshot history. Measurements are cached and may be temporarily unavailable; measured_at
    is null when no measurement exists. BYO and S3 Tables catalogs are not metered.

    Args:
        name (str): The name of the catalog.
        environment (str | Unset): Environment whose catalog usage to return. When it has no same-
            named catalog, usage for the catalog from default is returned instead. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeCatalogUsageResponse | ErrorModel]
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
) -> DescribeCatalogUsageResponse | ErrorModel | None:
    """Describe catalog usage

     Returns physical bytes stored by one Tower-managed catalog, including Iceberg metadata and not-yet-
    compacted snapshot history. Measurements are cached and may be temporarily unavailable; measured_at
    is null when no measurement exists. BYO and S3 Tables catalogs are not metered.

    Args:
        name (str): The name of the catalog.
        environment (str | Unset): Environment whose catalog usage to return. When it has no same-
            named catalog, usage for the catalog from default is returned instead. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeCatalogUsageResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            environment=environment,
        )
    ).parsed
