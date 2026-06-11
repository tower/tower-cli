from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.update_service_account_params import UpdateServiceAccountParams
from ...models.update_service_account_response import UpdateServiceAccountResponse
from ...types import Response


def _get_kwargs(
    id_or_name: str,
    *,
    body: UpdateServiceAccountParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/service-accounts/{id_or_name}".format(
            id_or_name=quote(str(id_or_name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | UpdateServiceAccountResponse:
    if response.status_code == 200:
        response_200 = UpdateServiceAccountResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | UpdateServiceAccountResponse]:
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
    body: UpdateServiceAccountParams,
) -> Response[ErrorModel | UpdateServiceAccountResponse]:
    """Update service account

     Update one or more fields on an existing service account. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account to update.
        body (UpdateServiceAccountParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateServiceAccountResponse]
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
    body: UpdateServiceAccountParams,
) -> ErrorModel | UpdateServiceAccountResponse | None:
    """Update service account

     Update one or more fields on an existing service account. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account to update.
        body (UpdateServiceAccountParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateServiceAccountResponse
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
    body: UpdateServiceAccountParams,
) -> Response[ErrorModel | UpdateServiceAccountResponse]:
    """Update service account

     Update one or more fields on an existing service account. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account to update.
        body (UpdateServiceAccountParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateServiceAccountResponse]
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
    body: UpdateServiceAccountParams,
) -> ErrorModel | UpdateServiceAccountResponse | None:
    """Update service account

     Update one or more fields on an existing service account. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account to update.
        body (UpdateServiceAccountParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateServiceAccountResponse
    """

    return (
        await asyncio_detailed(
            id_or_name=id_or_name,
            client=client,
            body=body,
        )
    ).parsed
