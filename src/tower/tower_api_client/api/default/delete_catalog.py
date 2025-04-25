from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_catalog_response import DeleteCatalogResponse
from ...types import Response


def _get_kwargs(
    slug: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/catalogs/{slug}".format(
            slug=slug,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[DeleteCatalogResponse]:
    if response.status_code == 200:
        response_200 = DeleteCatalogResponse.from_dict(response.json())

        return response_200
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
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Response[DeleteCatalogResponse]:
    """Delete catalog

     Delete a new catalog object in the currently authenticated account.

    Args:
        slug (str): The slug of the catalog to update.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteCatalogResponse]
    """

    kwargs = _get_kwargs(
        slug=slug,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Optional[DeleteCatalogResponse]:
    """Delete catalog

     Delete a new catalog object in the currently authenticated account.

    Args:
        slug (str): The slug of the catalog to update.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteCatalogResponse
    """

    return sync_detailed(
        slug=slug,
        client=client,
    ).parsed


async def asyncio_detailed(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Response[DeleteCatalogResponse]:
    """Delete catalog

     Delete a new catalog object in the currently authenticated account.

    Args:
        slug (str): The slug of the catalog to update.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteCatalogResponse]
    """

    kwargs = _get_kwargs(
        slug=slug,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Optional[DeleteCatalogResponse]:
    """Delete catalog

     Delete a new catalog object in the currently authenticated account.

    Args:
        slug (str): The slug of the catalog to update.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteCatalogResponse
    """

    return (
        await asyncio_detailed(
            slug=slug,
            client=client,
        )
    ).parsed
