from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
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
        "method": "delete",
        "url": "/catalogs/{catalog}/facts/{name}".format(
            catalog=quote(str(catalog), safe=""),
            name=quote(str(name), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | ErrorModel:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | ErrorModel]:
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
) -> Response[Any | ErrorModel]:
    """Delete a catalog fact

     Deletes a semantic metadata fact addressed by its name within a catalog.

    Args:
        catalog (str): The name of the catalog.
        name (str): The name of the fact.
        environment (str | Unset): Environment containing the catalog definition to delete from.
            This operation does not fall back to default. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ErrorModel]
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
) -> Any | ErrorModel | None:
    """Delete a catalog fact

     Deletes a semantic metadata fact addressed by its name within a catalog.

    Args:
        catalog (str): The name of the catalog.
        name (str): The name of the fact.
        environment (str | Unset): Environment containing the catalog definition to delete from.
            This operation does not fall back to default. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ErrorModel
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
) -> Response[Any | ErrorModel]:
    """Delete a catalog fact

     Deletes a semantic metadata fact addressed by its name within a catalog.

    Args:
        catalog (str): The name of the catalog.
        name (str): The name of the fact.
        environment (str | Unset): Environment containing the catalog definition to delete from.
            This operation does not fall back to default. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ErrorModel]
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
) -> Any | ErrorModel | None:
    """Delete a catalog fact

     Deletes a semantic metadata fact addressed by its name within a catalog.

    Args:
        catalog (str): The name of the catalog.
        name (str): The name of the fact.
        environment (str | Unset): Environment containing the catalog definition to delete from.
            This operation does not fall back to default. Default: 'default'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ErrorModel
    """

    return (
        await asyncio_detailed(
            catalog=catalog,
            name=name,
            client=client,
            environment=environment,
        )
    ).parsed
