from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.update_catalog_fact_body import UpdateCatalogFactBody
from ...models.update_catalog_fact_response import UpdateCatalogFactResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    catalog: str,
    name: str,
    *,
    body: UpdateCatalogFactBody,
    environment: str | Unset = "default",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["environment"] = environment

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/catalogs/{catalog}/facts/{name}".format(
            catalog=quote(str(catalog), safe=""),
            name=quote(str(name), safe=""),
        ),
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | UpdateCatalogFactResponse:
    if response.status_code == 200:
        response_200 = UpdateCatalogFactResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | UpdateCatalogFactResponse]:
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
    body: UpdateCatalogFactBody,
    environment: str | Unset = "default",
) -> Response[ErrorModel | UpdateCatalogFactResponse]:
    """Update a catalog fact

     Idempotently sets a semantic metadata fact by name: creates it when the name is new, updates it when
    it already exists. An inferred write cannot overwrite an existing confirmed fact.

    Args:
        catalog (str): The name of the catalog.
        name (str): The name of the fact.
        environment (str | Unset): Environment containing the catalog definition to update. This
            operation does not fall back to default. Default: 'default'.
        body (UpdateCatalogFactBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateCatalogFactResponse]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        name=name,
        body=body,
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
    body: UpdateCatalogFactBody,
    environment: str | Unset = "default",
) -> ErrorModel | UpdateCatalogFactResponse | None:
    """Update a catalog fact

     Idempotently sets a semantic metadata fact by name: creates it when the name is new, updates it when
    it already exists. An inferred write cannot overwrite an existing confirmed fact.

    Args:
        catalog (str): The name of the catalog.
        name (str): The name of the fact.
        environment (str | Unset): Environment containing the catalog definition to update. This
            operation does not fall back to default. Default: 'default'.
        body (UpdateCatalogFactBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateCatalogFactResponse
    """

    return sync_detailed(
        catalog=catalog,
        name=name,
        client=client,
        body=body,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    catalog: str,
    name: str,
    *,
    client: AuthenticatedClient,
    body: UpdateCatalogFactBody,
    environment: str | Unset = "default",
) -> Response[ErrorModel | UpdateCatalogFactResponse]:
    """Update a catalog fact

     Idempotently sets a semantic metadata fact by name: creates it when the name is new, updates it when
    it already exists. An inferred write cannot overwrite an existing confirmed fact.

    Args:
        catalog (str): The name of the catalog.
        name (str): The name of the fact.
        environment (str | Unset): Environment containing the catalog definition to update. This
            operation does not fall back to default. Default: 'default'.
        body (UpdateCatalogFactBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateCatalogFactResponse]
    """

    kwargs = _get_kwargs(
        catalog=catalog,
        name=name,
        body=body,
        environment=environment,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    catalog: str,
    name: str,
    *,
    client: AuthenticatedClient,
    body: UpdateCatalogFactBody,
    environment: str | Unset = "default",
) -> ErrorModel | UpdateCatalogFactResponse | None:
    """Update a catalog fact

     Idempotently sets a semantic metadata fact by name: creates it when the name is new, updates it when
    it already exists. An inferred write cannot overwrite an existing confirmed fact.

    Args:
        catalog (str): The name of the catalog.
        name (str): The name of the fact.
        environment (str | Unset): Environment containing the catalog definition to update. This
            operation does not fall back to default. Default: 'default'.
        body (UpdateCatalogFactBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateCatalogFactResponse
    """

    return (
        await asyncio_detailed(
            catalog=catalog,
            name=name,
            client=client,
            body=body,
            environment=environment,
        )
    ).parsed
