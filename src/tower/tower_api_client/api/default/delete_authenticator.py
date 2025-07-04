from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_authenticator_params import DeleteAuthenticatorParams
from ...models.delete_authenticator_response import DeleteAuthenticatorResponse
from ...types import Response


def _get_kwargs(
    *,
    body: DeleteAuthenticatorParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/accounts/authenticator",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[DeleteAuthenticatorResponse]:
    if response.status_code == 200:
        response_200 = DeleteAuthenticatorResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[DeleteAuthenticatorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: DeleteAuthenticatorParams,
) -> Response[DeleteAuthenticatorResponse]:
    """Delete authenticator

     Removes an authenticator from your account so you're no longer required to provide it at login.

    Args:
        body (DeleteAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteAuthenticatorResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: DeleteAuthenticatorParams,
) -> Optional[DeleteAuthenticatorResponse]:
    """Delete authenticator

     Removes an authenticator from your account so you're no longer required to provide it at login.

    Args:
        body (DeleteAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteAuthenticatorResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: DeleteAuthenticatorParams,
) -> Response[DeleteAuthenticatorResponse]:
    """Delete authenticator

     Removes an authenticator from your account so you're no longer required to provide it at login.

    Args:
        body (DeleteAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteAuthenticatorResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: DeleteAuthenticatorParams,
) -> Optional[DeleteAuthenticatorResponse]:
    """Delete authenticator

     Removes an authenticator from your account so you're no longer required to provide it at login.

    Args:
        body (DeleteAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteAuthenticatorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
