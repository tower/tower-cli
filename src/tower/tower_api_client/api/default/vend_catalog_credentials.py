from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.vend_catalog_credentials_body import VendCatalogCredentialsBody
from ...models.vend_catalog_credentials_response import VendCatalogCredentialsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    body: VendCatalogCredentialsBody,
    environment: str | Unset = "default",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["environment"] = environment

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/catalogs/{name}/credentials".format(
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
) -> ErrorModel | VendCatalogCredentialsResponse | None:
    if response.status_code == 200:
        response_200 = VendCatalogCredentialsResponse.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorModel.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = ErrorModel.from_dict(response.json())

        return response_403

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
) -> Response[ErrorModel | VendCatalogCredentialsResponse]:
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
    body: VendCatalogCredentialsBody,
    environment: str | Unset = "default",
) -> Response[ErrorModel | VendCatalogCredentialsResponse]:
    r"""Vend catalog credentials

     Mints a short-lived OAuth bearer token for browser or SDK access to a managed (tower-catalog)
    catalog. Defaults to read-only (`mode: \"read\"`); pass `mode: \"read-write\"` in the body (requires
    the catalogs:update scope) for a token bound to the read-write principal. Team membership is
    enforced before vending; the master Polaris credentials never leave Tower.

    Args:
        name (str): The name of the catalog.
        environment (str | Unset): The environment of the catalog. Default: 'default'.
        body (VendCatalogCredentialsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | VendCatalogCredentialsResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
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
    body: VendCatalogCredentialsBody,
    environment: str | Unset = "default",
) -> ErrorModel | VendCatalogCredentialsResponse | None:
    r"""Vend catalog credentials

     Mints a short-lived OAuth bearer token for browser or SDK access to a managed (tower-catalog)
    catalog. Defaults to read-only (`mode: \"read\"`); pass `mode: \"read-write\"` in the body (requires
    the catalogs:update scope) for a token bound to the read-write principal. Team membership is
    enforced before vending; the master Polaris credentials never leave Tower.

    Args:
        name (str): The name of the catalog.
        environment (str | Unset): The environment of the catalog. Default: 'default'.
        body (VendCatalogCredentialsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | VendCatalogCredentialsResponse
    """

    return sync_detailed(
        name=name,
        client=client,
        body=body,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    body: VendCatalogCredentialsBody,
    environment: str | Unset = "default",
) -> Response[ErrorModel | VendCatalogCredentialsResponse]:
    r"""Vend catalog credentials

     Mints a short-lived OAuth bearer token for browser or SDK access to a managed (tower-catalog)
    catalog. Defaults to read-only (`mode: \"read\"`); pass `mode: \"read-write\"` in the body (requires
    the catalogs:update scope) for a token bound to the read-write principal. Team membership is
    enforced before vending; the master Polaris credentials never leave Tower.

    Args:
        name (str): The name of the catalog.
        environment (str | Unset): The environment of the catalog. Default: 'default'.
        body (VendCatalogCredentialsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | VendCatalogCredentialsResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        environment=environment,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
    body: VendCatalogCredentialsBody,
    environment: str | Unset = "default",
) -> ErrorModel | VendCatalogCredentialsResponse | None:
    r"""Vend catalog credentials

     Mints a short-lived OAuth bearer token for browser or SDK access to a managed (tower-catalog)
    catalog. Defaults to read-only (`mode: \"read\"`); pass `mode: \"read-write\"` in the body (requires
    the catalogs:update scope) for a token bound to the read-write principal. Team membership is
    enforced before vending; the master Polaris credentials never leave Tower.

    Args:
        name (str): The name of the catalog.
        environment (str | Unset): The environment of the catalog. Default: 'default'.
        body (VendCatalogCredentialsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | VendCatalogCredentialsResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
            environment=environment,
        )
    ).parsed
