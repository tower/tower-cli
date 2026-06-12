from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.create_service_account_api_key_params import (
    CreateServiceAccountAPIKeyParams,
)
from ...models.create_service_account_api_key_response import (
    CreateServiceAccountAPIKeyResponse,
)
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs(
    id_or_name: str,
    *,
    body: CreateServiceAccountAPIKeyParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/service-accounts/{id_or_name}/api-keys".format(
            id_or_name=quote(str(id_or_name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CreateServiceAccountAPIKeyResponse | ErrorModel:
    if response.status_code == 201:
        response_201 = CreateServiceAccountAPIKeyResponse.from_dict(response.json())

        return response_201

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[CreateServiceAccountAPIKeyResponse | ErrorModel]:
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
    body: CreateServiceAccountAPIKeyParams,
) -> Response[CreateServiceAccountAPIKeyResponse | ErrorModel]:
    """Create API key for service account

     Mint a new API key bound to a service account. The full identifier is only returned on this
    response. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account this key authenticates as.
        body (CreateServiceAccountAPIKeyParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreateServiceAccountAPIKeyResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        id_or_name=id_or_name,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id_or_name: str,
    *,
    client: AuthenticatedClient,
    body: CreateServiceAccountAPIKeyParams,
) -> CreateServiceAccountAPIKeyResponse | ErrorModel | None:
    """Create API key for service account

     Mint a new API key bound to a service account. The full identifier is only returned on this
    response. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account this key authenticates as.
        body (CreateServiceAccountAPIKeyParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreateServiceAccountAPIKeyResponse | ErrorModel
    """

    return sync_detailed(
        id_or_name=id_or_name,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    id_or_name: str,
    *,
    client: AuthenticatedClient,
    body: CreateServiceAccountAPIKeyParams,
) -> Response[CreateServiceAccountAPIKeyResponse | ErrorModel]:
    """Create API key for service account

     Mint a new API key bound to a service account. The full identifier is only returned on this
    response. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account this key authenticates as.
        body (CreateServiceAccountAPIKeyParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreateServiceAccountAPIKeyResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        id_or_name=id_or_name,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id_or_name: str,
    *,
    client: AuthenticatedClient,
    body: CreateServiceAccountAPIKeyParams,
) -> CreateServiceAccountAPIKeyResponse | ErrorModel | None:
    """Create API key for service account

     Mint a new API key bound to a service account. The full identifier is only returned on this
    response. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account this key authenticates as.
        body (CreateServiceAccountAPIKeyParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreateServiceAccountAPIKeyResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            id_or_name=id_or_name,
            client=client,
            body=body,
        )
    ).parsed
