from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs(
    id_or_name: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/service-accounts/{id_or_name}".format(
            id_or_name=quote(str(id_or_name), safe=""),
        ),
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
    id_or_name: str,
    *,
    client: AuthenticatedClient,
) -> Response[Any | ErrorModel]:
    """Delete service account

     Tombstones a service account: revokes API keys, disables owned schedules, cancels in-flight runs,
    then soft-deletes the SA. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account to delete.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ErrorModel]
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
) -> Any | ErrorModel | None:
    """Delete service account

     Tombstones a service account: revokes API keys, disables owned schedules, cancels in-flight runs,
    then soft-deletes the SA. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account to delete.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ErrorModel
    """

    return sync_detailed(
        id_or_name=id_or_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    id_or_name: str,
    *,
    client: AuthenticatedClient,
) -> Response[Any | ErrorModel]:
    """Delete service account

     Tombstones a service account: revokes API keys, disables owned schedules, cancels in-flight runs,
    then soft-deletes the SA. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account to delete.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ErrorModel]
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
) -> Any | ErrorModel | None:
    """Delete service account

     Tombstones a service account: revokes API keys, disables owned schedules, cancels in-flight runs,
    then soft-deletes the SA. Team admin only.

    Args:
        id_or_name (str): The ID or name of the service account to delete.

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
        )
    ).parsed
