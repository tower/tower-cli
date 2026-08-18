from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.list_catalog_facts_response import ListCatalogFactsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    catalog: str,
    *,
    environment: str | Unset = "default",
    scope: str | Unset = UNSET,
    object_: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["environment"] = environment

    params["scope"] = scope

    params["object"] = object_

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/catalogs/{catalog}/facts".format(
            catalog=quote(str(catalog), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | ListCatalogFactsResponse:
    if response.status_code == 200:
        response_200 = ListCatalogFactsResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | ListCatalogFactsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    catalog: str,
    *,
    client: AuthenticatedClient,
    environment: str | Unset = "default",
    scope: str | Unset = UNSET,
    object_: str | Unset = UNSET,
) -> Response[ErrorModel | ListCatalogFactsResponse]:
    """List catalog facts

     Lists the semantic metadata facts attached to a catalog, optionally filtered by scope and/or object
    path.

    Args:
        catalog (str): The name of the catalog.
        environment (str | Unset): The environment of the catalog. Note that if a catalog with the
            requested name doesn't exist in the requested environment, facts for the catalog with the
            same name from the default environment will be returned. Default: 'default'.
        scope (str | Unset): Filter facts by scope. When omitted, facts of every scope are
            returned.
        object_ (str | Unset): Filter facts by object path (exact match). When omitted, facts
            about any object are returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | ListCatalogFactsResponse]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        environment=environment,
        scope=scope,
        object_=object_,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    catalog: str,
    *,
    client: AuthenticatedClient,
    environment: str | Unset = "default",
    scope: str | Unset = UNSET,
    object_: str | Unset = UNSET,
) -> ErrorModel | ListCatalogFactsResponse | None:
    """List catalog facts

     Lists the semantic metadata facts attached to a catalog, optionally filtered by scope and/or object
    path.

    Args:
        catalog (str): The name of the catalog.
        environment (str | Unset): The environment of the catalog. Note that if a catalog with the
            requested name doesn't exist in the requested environment, facts for the catalog with the
            same name from the default environment will be returned. Default: 'default'.
        scope (str | Unset): Filter facts by scope. When omitted, facts of every scope are
            returned.
        object_ (str | Unset): Filter facts by object path (exact match). When omitted, facts
            about any object are returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | ListCatalogFactsResponse
    """

    return sync_detailed(
        catalog=catalog,
        client=client,
        environment=environment,
        scope=scope,
        object_=object_,
    ).parsed


async def asyncio_detailed(
    catalog: str,
    *,
    client: AuthenticatedClient,
    environment: str | Unset = "default",
    scope: str | Unset = UNSET,
    object_: str | Unset = UNSET,
) -> Response[ErrorModel | ListCatalogFactsResponse]:
    """List catalog facts

     Lists the semantic metadata facts attached to a catalog, optionally filtered by scope and/or object
    path.

    Args:
        catalog (str): The name of the catalog.
        environment (str | Unset): The environment of the catalog. Note that if a catalog with the
            requested name doesn't exist in the requested environment, facts for the catalog with the
            same name from the default environment will be returned. Default: 'default'.
        scope (str | Unset): Filter facts by scope. When omitted, facts of every scope are
            returned.
        object_ (str | Unset): Filter facts by object path (exact match). When omitted, facts
            about any object are returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | ListCatalogFactsResponse]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        environment=environment,
        scope=scope,
        object_=object_,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    catalog: str,
    *,
    client: AuthenticatedClient,
    environment: str | Unset = "default",
    scope: str | Unset = UNSET,
    object_: str | Unset = UNSET,
) -> ErrorModel | ListCatalogFactsResponse | None:
    """List catalog facts

     Lists the semantic metadata facts attached to a catalog, optionally filtered by scope and/or object
    path.

    Args:
        catalog (str): The name of the catalog.
        environment (str | Unset): The environment of the catalog. Note that if a catalog with the
            requested name doesn't exist in the requested environment, facts for the catalog with the
            same name from the default environment will be returned. Default: 'default'.
        scope (str | Unset): Filter facts by scope. When omitted, facts of every scope are
            returned.
        object_ (str | Unset): Filter facts by object path (exact match). When omitted, facts
            about any object are returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | ListCatalogFactsResponse
    """

    return (
        await asyncio_detailed(
            catalog=catalog,
            client=client,
            environment=environment,
            scope=scope,
            object_=object_,
        )
    ).parsed
