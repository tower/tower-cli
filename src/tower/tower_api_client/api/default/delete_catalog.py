from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_catalog_response import DeleteCatalogResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    environment: Union[Unset, str] = "default",
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["environment"] = environment

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/catalogs/{name}".format(
            name=name,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[DeleteCatalogResponse]:
    if response.status_code == 204:
        response_204 = DeleteCatalogResponse.from_dict(response.json())

        return response_204
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[DeleteCatalogResponse]:
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
    environment: Union[Unset, str] = "default",
) -> Response[DeleteCatalogResponse]:
    """Delete catalog

     Delete a new catalog object in the currently authenticated account.

    Args:
        name (str): The name of the catalog to update.
        environment (Union[Unset, str]): The environment of the catalog to delete. Default:
            'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteCatalogResponse]
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
    environment: Union[Unset, str] = "default",
) -> Optional[DeleteCatalogResponse]:
    """Delete catalog

     Delete a new catalog object in the currently authenticated account.

    Args:
        name (str): The name of the catalog to update.
        environment (Union[Unset, str]): The environment of the catalog to delete. Default:
            'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteCatalogResponse
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
    environment: Union[Unset, str] = "default",
) -> Response[DeleteCatalogResponse]:
    """Delete catalog

     Delete a new catalog object in the currently authenticated account.

    Args:
        name (str): The name of the catalog to update.
        environment (Union[Unset, str]): The environment of the catalog to delete. Default:
            'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteCatalogResponse]
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
    environment: Union[Unset, str] = "default",
) -> Optional[DeleteCatalogResponse]:
    """Delete catalog

     Delete a new catalog object in the currently authenticated account.

    Args:
        name (str): The name of the catalog to update.
        environment (Union[Unset, str]): The environment of the catalog to delete. Default:
            'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteCatalogResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            environment=environment,
        )
    ).parsed
