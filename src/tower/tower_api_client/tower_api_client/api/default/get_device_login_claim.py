from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_device_login_claim_output_body import GetDeviceLoginClaimOutputBody
from ...types import Response


def _get_kwargs(
    device_code: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/login/device/{device_code}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GetDeviceLoginClaimOutputBody]:
    if response.status_code == 200:
        response_200 = GetDeviceLoginClaimOutputBody.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GetDeviceLoginClaimOutputBody]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    device_code: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[GetDeviceLoginClaimOutputBody]:
    """Check a device login code.

     Checks if a device login code has been claimed and returns the user session if so.

    Args:
        device_code (str): The device code to check.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetDeviceLoginClaimOutputBody]
    """

    kwargs = _get_kwargs(
        device_code=device_code,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    device_code: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[GetDeviceLoginClaimOutputBody]:
    """Check a device login code.

     Checks if a device login code has been claimed and returns the user session if so.

    Args:
        device_code (str): The device code to check.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetDeviceLoginClaimOutputBody
    """

    return sync_detailed(
        device_code=device_code,
        client=client,
    ).parsed


async def asyncio_detailed(
    device_code: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[GetDeviceLoginClaimOutputBody]:
    """Check a device login code.

     Checks if a device login code has been claimed and returns the user session if so.

    Args:
        device_code (str): The device code to check.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetDeviceLoginClaimOutputBody]
    """

    kwargs = _get_kwargs(
        device_code=device_code,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    device_code: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[GetDeviceLoginClaimOutputBody]:
    """Check a device login code.

     Checks if a device login code has been claimed and returns the user session if so.

    Args:
        device_code (str): The device code to check.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetDeviceLoginClaimOutputBody
    """

    return (
        await asyncio_detailed(
            device_code=device_code,
            client=client,
        )
    ).parsed
