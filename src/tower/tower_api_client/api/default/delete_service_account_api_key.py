from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.delete_service_account_api_key_params import (
    DeleteServiceAccountAPIKeyParams,
)
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs(
    id_or_name: str,
    *,
    body: DeleteServiceAccountAPIKeyParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "delete",
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
    id_or_name: str,
    *,
    client: AuthenticatedClient,
    body: DeleteServiceAccountAPIKeyParams,
) -> Response[Any | ErrorModel]:
    """Delete API key for service account

     Revoke an API key bound to a service account. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account.
        body (DeleteServiceAccountAPIKeyParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ErrorModel]
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
    body: DeleteServiceAccountAPIKeyParams,
) -> Any | ErrorModel | None:
    """Delete API key for service account

     Revoke an API key bound to a service account. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account.
        body (DeleteServiceAccountAPIKeyParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ErrorModel
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
    body: DeleteServiceAccountAPIKeyParams,
) -> Response[Any | ErrorModel]:
    """Delete API key for service account

     Revoke an API key bound to a service account. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account.
        body (DeleteServiceAccountAPIKeyParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ErrorModel]
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
    body: DeleteServiceAccountAPIKeyParams,
) -> Any | ErrorModel | None:
    """Delete API key for service account

     Revoke an API key bound to a service account. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account.
        body (DeleteServiceAccountAPIKeyParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ErrorModel
    """

    return (
        await asyncio_detailed(
            id_or_name=id_or_name,
            client=client,
            body=body,
        )
    ).parsed
