from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.update_catalog_params import UpdateCatalogParams
from ...models.update_catalog_response import UpdateCatalogResponse
from ...types import Response


def _get_kwargs(
    name: str,
    *,
    body: UpdateCatalogParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/catalogs/{name}".format(
            name=quote(str(name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | UpdateCatalogResponse:
    if response.status_code == 200:
        response_200 = UpdateCatalogResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | UpdateCatalogResponse]:
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
    body: UpdateCatalogParams,
) -> Response[ErrorModel | UpdateCatalogResponse]:
    """Update catalog

     Update a new catalog object in the currently authenticated account.

    Args:
        name (str): The name of the catalog to update.
        body (UpdateCatalogParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateCatalogResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient,
    body: UpdateCatalogParams,
) -> ErrorModel | UpdateCatalogResponse | None:
    """Update catalog

     Update a new catalog object in the currently authenticated account.

    Args:
        name (str): The name of the catalog to update.
        body (UpdateCatalogParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateCatalogResponse
    """

    return sync_detailed(
        name=name,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    body: UpdateCatalogParams,
) -> Response[ErrorModel | UpdateCatalogResponse]:
    """Update catalog

     Update a new catalog object in the currently authenticated account.

    Args:
        name (str): The name of the catalog to update.
        body (UpdateCatalogParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateCatalogResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
    body: UpdateCatalogParams,
) -> ErrorModel | UpdateCatalogResponse | None:
    """Update catalog

     Update a new catalog object in the currently authenticated account.

    Args:
        name (str): The name of the catalog to update.
        body (UpdateCatalogParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateCatalogResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
        )
    ).parsed
