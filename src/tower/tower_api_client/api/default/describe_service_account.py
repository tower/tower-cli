from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.describe_service_account_response import DescribeServiceAccountResponse
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs(
    id_or_name: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/service-accounts/{id_or_name}".format(
            id_or_name=quote(str(id_or_name), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DescribeServiceAccountResponse | ErrorModel:
    if response.status_code == 200:
        response_200 = DescribeServiceAccountResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DescribeServiceAccountResponse | ErrorModel]:
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
) -> Response[DescribeServiceAccountResponse | ErrorModel]:
    """Describe service account

     Fetch a single service account by ID or name. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeServiceAccountResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        id_or_name=id_or_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id_or_name: str,
    *,
    client: AuthenticatedClient,
) -> DescribeServiceAccountResponse | ErrorModel | None:
    """Describe service account

     Fetch a single service account by ID or name. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeServiceAccountResponse | ErrorModel
    """

    return sync_detailed(
        id_or_name=id_or_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    id_or_name: str,
    *,
    client: AuthenticatedClient,
) -> Response[DescribeServiceAccountResponse | ErrorModel]:
    """Describe service account

     Fetch a single service account by ID or name. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeServiceAccountResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        id_or_name=id_or_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id_or_name: str,
    *,
    client: AuthenticatedClient,
) -> DescribeServiceAccountResponse | ErrorModel | None:
    """Describe service account

     Fetch a single service account by ID or name. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeServiceAccountResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            id_or_name=id_or_name,
            client=client,
        )
    ).parsed
