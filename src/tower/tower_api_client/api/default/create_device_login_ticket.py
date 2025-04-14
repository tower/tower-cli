from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import Client
from ...models.create_device_login_ticket_response import (
    CreateDeviceLoginTicketResponse,
)
from ...types import Response


def _get_kwargs(
    *,
    client: Client,
) -> Dict[str, Any]:
    url = "{}/login/device".format(client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(
    *, response: httpx.Response
) -> Optional[CreateDeviceLoginTicketResponse]:
    if response.status_code == 200:
        response_200 = CreateDeviceLoginTicketResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(
    *, response: httpx.Response
) -> Response[CreateDeviceLoginTicketResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: Client,
) -> Response[CreateDeviceLoginTicketResponse]:
    """Create a device login ticket

     Creates a new device login ticket and returns the codes and urls needed for authentication.

    Returns:
        Response[CreateDeviceLoginTicketResponse]
    """

    kwargs = _get_kwargs(
        client=client,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: Client,
) -> Optional[CreateDeviceLoginTicketResponse]:
    """Create a device login ticket

     Creates a new device login ticket and returns the codes and urls needed for authentication.

    Returns:
        Response[CreateDeviceLoginTicketResponse]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: Client,
) -> Response[CreateDeviceLoginTicketResponse]:
    """Create a device login ticket

     Creates a new device login ticket and returns the codes and urls needed for authentication.

    Returns:
        Response[CreateDeviceLoginTicketResponse]
    """

    kwargs = _get_kwargs(
        client=client,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: Client,
) -> Optional[CreateDeviceLoginTicketResponse]:
    """Create a device login ticket

     Creates a new device login ticket and returns the codes and urls needed for authentication.

    Returns:
        Response[CreateDeviceLoginTicketResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
