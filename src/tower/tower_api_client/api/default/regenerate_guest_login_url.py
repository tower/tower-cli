from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.regenerate_guest_login_url_params import RegenerateGuestLoginURLParams
from ...models.regenerate_guest_login_url_response import (
    RegenerateGuestLoginURLResponse,
)
from ...types import Response


def _get_kwargs(
    guest_id: str,
    *,
    body: RegenerateGuestLoginURLParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/guests/{guest_id}/login-url".format(
            guest_id=quote(str(guest_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | RegenerateGuestLoginURLResponse:
    if response.status_code == 200:
        response_200 = RegenerateGuestLoginURLResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | RegenerateGuestLoginURLResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    guest_id: str,
    *,
    client: AuthenticatedClient,
    body: RegenerateGuestLoginURLParams,
) -> Response[ErrorModel | RegenerateGuestLoginURLResponse]:
    """Regenerate guest login URL

     Creates a new login URL for an existing guest. Use this if the previous URL expired or was
    compromised.

    Args:
        guest_id (str): The ID of the guest to regenerate the login URL for.
        body (RegenerateGuestLoginURLParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | RegenerateGuestLoginURLResponse]
    """

    kwargs = _get_kwargs(
        guest_id=guest_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    guest_id: str,
    *,
    client: AuthenticatedClient,
    body: RegenerateGuestLoginURLParams,
) -> ErrorModel | RegenerateGuestLoginURLResponse | None:
    """Regenerate guest login URL

     Creates a new login URL for an existing guest. Use this if the previous URL expired or was
    compromised.

    Args:
        guest_id (str): The ID of the guest to regenerate the login URL for.
        body (RegenerateGuestLoginURLParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | RegenerateGuestLoginURLResponse
    """

    return sync_detailed(
        guest_id=guest_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    guest_id: str,
    *,
    client: AuthenticatedClient,
    body: RegenerateGuestLoginURLParams,
) -> Response[ErrorModel | RegenerateGuestLoginURLResponse]:
    """Regenerate guest login URL

     Creates a new login URL for an existing guest. Use this if the previous URL expired or was
    compromised.

    Args:
        guest_id (str): The ID of the guest to regenerate the login URL for.
        body (RegenerateGuestLoginURLParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | RegenerateGuestLoginURLResponse]
    """

    kwargs = _get_kwargs(
        guest_id=guest_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    guest_id: str,
    *,
    client: AuthenticatedClient,
    body: RegenerateGuestLoginURLParams,
) -> ErrorModel | RegenerateGuestLoginURLResponse | None:
    """Regenerate guest login URL

     Creates a new login URL for an existing guest. Use this if the previous URL expired or was
    compromised.

    Args:
        guest_id (str): The ID of the guest to regenerate the login URL for.
        body (RegenerateGuestLoginURLParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | RegenerateGuestLoginURLResponse
    """

    return (
        await asyncio_detailed(
            guest_id=guest_id,
            client=client,
            body=body,
        )
    ).parsed
