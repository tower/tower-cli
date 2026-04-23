from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.create_device_login_ticket_response import (
    CreateDeviceLoginTicketResponse,
)
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/login/device",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CreateDeviceLoginTicketResponse | ErrorModel:
    if response.status_code == 200:
        response_200 = CreateDeviceLoginTicketResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[CreateDeviceLoginTicketResponse | ErrorModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[CreateDeviceLoginTicketResponse | ErrorModel]:
    """Create device login ticket

     Creates a new device login ticket and returns the codes and urls needed for authentication.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreateDeviceLoginTicketResponse | ErrorModel]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> CreateDeviceLoginTicketResponse | ErrorModel | None:
    """Create device login ticket

     Creates a new device login ticket and returns the codes and urls needed for authentication.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreateDeviceLoginTicketResponse | ErrorModel
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[CreateDeviceLoginTicketResponse | ErrorModel]:
    """Create device login ticket

     Creates a new device login ticket and returns the codes and urls needed for authentication.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreateDeviceLoginTicketResponse | ErrorModel]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> CreateDeviceLoginTicketResponse | ErrorModel | None:
    """Create device login ticket

     Creates a new device login ticket and returns the codes and urls needed for authentication.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreateDeviceLoginTicketResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
