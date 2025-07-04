from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_authenticator_params import CreateAuthenticatorParams
from ...models.create_authenticator_response import CreateAuthenticatorResponse
from ...types import Response


def _get_kwargs(
    *,
    body: CreateAuthenticatorParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/accounts/authenticator",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[CreateAuthenticatorResponse]:
    if response.status_code == 200:
        response_200 = CreateAuthenticatorResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[CreateAuthenticatorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: CreateAuthenticatorParams,
) -> Response[CreateAuthenticatorResponse]:
    """Create authenticator

     Associates an authenticator with your account, where the authenticator is identified by the URL with
    an otpauth URI scheme.

    Args:
        body (CreateAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreateAuthenticatorResponse]
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
    body: CreateAuthenticatorParams,
) -> Optional[CreateAuthenticatorResponse]:
    """Create authenticator

     Associates an authenticator with your account, where the authenticator is identified by the URL with
    an otpauth URI scheme.

    Args:
        body (CreateAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreateAuthenticatorResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: CreateAuthenticatorParams,
) -> Response[CreateAuthenticatorResponse]:
    """Create authenticator

     Associates an authenticator with your account, where the authenticator is identified by the URL with
    an otpauth URI scheme.

    Args:
        body (CreateAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreateAuthenticatorResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: CreateAuthenticatorParams,
) -> Optional[CreateAuthenticatorResponse]:
    """Create authenticator

     Associates an authenticator with your account, where the authenticator is identified by the URL with
    an otpauth URI scheme.

    Args:
        body (CreateAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreateAuthenticatorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
