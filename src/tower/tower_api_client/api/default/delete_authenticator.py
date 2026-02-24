from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.delete_authenticator_params import DeleteAuthenticatorParams
from ...models.delete_authenticator_response import DeleteAuthenticatorResponse
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs(
    *,
    body: DeleteAuthenticatorParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/authenticators",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DeleteAuthenticatorResponse | ErrorModel:
    if response.status_code == 200:
        response_200 = DeleteAuthenticatorResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DeleteAuthenticatorResponse | ErrorModel]:
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
) -> Response[DeleteAuthenticatorResponse | ErrorModel]:
    """Delete authenticator

     Removes an authenticator from your account so you're no longer required to provide it at login.

    Args:
        body (DeleteAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteAuthenticatorResponse | ErrorModel]
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
) -> DeleteAuthenticatorResponse | ErrorModel | None:
    """Delete authenticator

     Removes an authenticator from your account so you're no longer required to provide it at login.

    Args:
        body (DeleteAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteAuthenticatorResponse | ErrorModel
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: DeleteAuthenticatorParams,
) -> Response[DeleteAuthenticatorResponse | ErrorModel]:
    """Delete authenticator

     Removes an authenticator from your account so you're no longer required to provide it at login.

    Args:
        body (DeleteAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteAuthenticatorResponse | ErrorModel]
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
) -> DeleteAuthenticatorResponse | ErrorModel | None:
    """Delete authenticator

     Removes an authenticator from your account so you're no longer required to provide it at login.

    Args:
        body (DeleteAuthenticatorParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteAuthenticatorResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
