from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.list_catalogs_response import ListCatalogsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    environment: str | Unset = UNSET,
    all_: bool | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["page"] = page

    params["page_size"] = page_size

    params["environment"] = environment

    params["all"] = all_

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/catalogs",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | ListCatalogsResponse:
    if response.status_code == 200:
        response_200 = ListCatalogsResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | ListCatalogsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    environment: str | Unset = UNSET,
    all_: bool | Unset = UNSET,
) -> Response[ErrorModel | ListCatalogsResponse]:
    """List catalogs

     Lists all the catalogs associated with your current account.

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        environment (str | Unset): The environment to filter by.
        all_ (bool | Unset): Whether to fetch all catalogs across all environments or only for the
            current environment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | ListCatalogsResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        page_size=page_size,
        environment=environment,
        all_=all_,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    environment: str | Unset = UNSET,
    all_: bool | Unset = UNSET,
) -> ErrorModel | ListCatalogsResponse | None:
    """List catalogs

     Lists all the catalogs associated with your current account.

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        environment (str | Unset): The environment to filter by.
        all_ (bool | Unset): Whether to fetch all catalogs across all environments or only for the
            current environment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | ListCatalogsResponse
    """

    return sync_detailed(
        client=client,
        page=page,
        page_size=page_size,
        environment=environment,
        all_=all_,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    environment: str | Unset = UNSET,
    all_: bool | Unset = UNSET,
) -> Response[ErrorModel | ListCatalogsResponse]:
    """List catalogs

     Lists all the catalogs associated with your current account.

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        environment (str | Unset): The environment to filter by.
        all_ (bool | Unset): Whether to fetch all catalogs across all environments or only for the
            current environment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | ListCatalogsResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        page_size=page_size,
        environment=environment,
        all_=all_,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    environment: str | Unset = UNSET,
    all_: bool | Unset = UNSET,
) -> ErrorModel | ListCatalogsResponse | None:
    """List catalogs

     Lists all the catalogs associated with your current account.

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        environment (str | Unset): The environment to filter by.
        all_ (bool | Unset): Whether to fetch all catalogs across all environments or only for the
            current environment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | ListCatalogsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            page_size=page_size,
            environment=environment,
            all_=all_,
        )
    ).parsed
