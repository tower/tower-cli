from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.list_service_account_api_keys_response import (
    ListServiceAccountAPIKeysResponse,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id_or_name: str,
    *,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["page"] = page

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/service-accounts/{id_or_name}/api-keys".format(
            id_or_name=quote(str(id_or_name), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | ListServiceAccountAPIKeysResponse:
    if response.status_code == 200:
        response_200 = ListServiceAccountAPIKeysResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | ListServiceAccountAPIKeysResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id_or_name: str,
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
) -> Response[ErrorModel | ListServiceAccountAPIKeysResponse]:
    """List API keys for service account

     List API keys bound to a service account. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account.
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | ListServiceAccountAPIKeysResponse]
    """

    kwargs = _get_kwargs(
        id_or_name=id_or_name,
        page=page,
        page_size=page_size,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id_or_name: str,
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
) -> ErrorModel | ListServiceAccountAPIKeysResponse | None:
    """List API keys for service account

     List API keys bound to a service account. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account.
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | ListServiceAccountAPIKeysResponse
    """

    return sync_detailed(
        id_or_name=id_or_name,
        client=client,
        page=page,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    id_or_name: str,
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
) -> Response[ErrorModel | ListServiceAccountAPIKeysResponse]:
    """List API keys for service account

     List API keys bound to a service account. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account.
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | ListServiceAccountAPIKeysResponse]
    """

    kwargs = _get_kwargs(
        id_or_name=id_or_name,
        page=page,
        page_size=page_size,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id_or_name: str,
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
) -> ErrorModel | ListServiceAccountAPIKeysResponse | None:
    """List API keys for service account

     List API keys bound to a service account. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account.
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | ListServiceAccountAPIKeysResponse
    """

    return (
        await asyncio_detailed(
            id_or_name=id_or_name,
            client=client,
            page=page,
            page_size=page_size,
        )
    ).parsed
