from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.create_authenticator_params import CreateAuthenticatorParams
from ...models.create_authenticator_response import CreateAuthenticatorResponse
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs(
    *,
    body: CreateAuthenticatorParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/authenticators",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CreateAuthenticatorResponse | ErrorModel:
    if response.status_code == 200:
        response_200 = CreateAuthenticatorResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[CreateAuthenticatorResponse | ErrorModel]:
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
) -> Response[CreateAuthenticatorResponse | ErrorModel]:
    """Create authenticator

     Associates an authenticator with your account, where the authenticator is identified by the URL with
    an otpauth URI scheme.

    Args:
        body (CreateAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreateAuthenticatorResponse | ErrorModel]
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
) -> CreateAuthenticatorResponse | ErrorModel | None:
    """Create authenticator

     Associates an authenticator with your account, where the authenticator is identified by the URL with
    an otpauth URI scheme.

    Args:
        body (CreateAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreateAuthenticatorResponse | ErrorModel
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: CreateAuthenticatorParams,
) -> Response[CreateAuthenticatorResponse | ErrorModel]:
    """Create authenticator

     Associates an authenticator with your account, where the authenticator is identified by the URL with
    an otpauth URI scheme.

    Args:
        body (CreateAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreateAuthenticatorResponse | ErrorModel]
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
) -> CreateAuthenticatorResponse | ErrorModel | None:
    """Create authenticator

     Associates an authenticator with your account, where the authenticator is identified by the URL with
    an otpauth URI scheme.

    Args:
        body (CreateAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreateAuthenticatorResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
