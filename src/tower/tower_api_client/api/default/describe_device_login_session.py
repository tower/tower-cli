from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import Client
from ...models.describe_device_login_session_response import (
    DescribeDeviceLoginSessionResponse,
)
from ...types import Response


def _get_kwargs(
    device_code: str,
    *,
    client: Client,
) -> Dict[str, Any]:
    url = "{}/login/device/{device_code}".format(
        client.base_url, device_code=device_code
    )

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
) -> Optional[DescribeDeviceLoginSessionResponse]:
    if response.status_code == 200:
        response_200 = DescribeDeviceLoginSessionResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(
    *, response: httpx.Response
) -> Response[DescribeDeviceLoginSessionResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    device_code: str,
    *,
    client: Client,
) -> Response[DescribeDeviceLoginSessionResponse]:
    """Describe device login session

     Checks if a device login code has been claimed and returns the user session if so.

    Args:
        device_code (str): The device code to check.

    Returns:
        Response[DescribeDeviceLoginSessionResponse]
    """

    kwargs = _get_kwargs(
        device_code=device_code,
        client=client,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    device_code: str,
    *,
    client: Client,
) -> Optional[DescribeDeviceLoginSessionResponse]:
    """Describe device login session

     Checks if a device login code has been claimed and returns the user session if so.

    Args:
        device_code (str): The device code to check.

    Returns:
        Response[DescribeDeviceLoginSessionResponse]
    """

    return sync_detailed(
        device_code=device_code,
        client=client,
    ).parsed


async def asyncio_detailed(
    device_code: str,
    *,
    client: Client,
) -> Response[DescribeDeviceLoginSessionResponse]:
    """Describe device login session

     Checks if a device login code has been claimed and returns the user session if so.

    Args:
        device_code (str): The device code to check.

    Returns:
        Response[DescribeDeviceLoginSessionResponse]
    """

    kwargs = _get_kwargs(
        device_code=device_code,
        client=client,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    device_code: str,
    *,
    client: Client,
) -> Optional[DescribeDeviceLoginSessionResponse]:
    """Describe device login session

     Checks if a device login code has been claimed and returns the user session if so.

    Args:
        device_code (str): The device code to check.

    Returns:
        Response[DescribeDeviceLoginSessionResponse]
    """

    return (
        await asyncio_detailed(
            device_code=device_code,
            client=client,
        )
    ).parsed
