from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_password_reset_params import CreatePasswordResetParams
from ...models.create_password_reset_response import CreatePasswordResetResponse
from ...types import Response


def _get_kwargs(
    *,
    body: CreatePasswordResetParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/accounts/password-reset",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[CreatePasswordResetResponse]:
    if response.status_code == 200:
        response_200 = CreatePasswordResetResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[CreatePasswordResetResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreatePasswordResetParams,
) -> Response[CreatePasswordResetResponse]:
    """Create password reset

     Starts the password reset process for an account. If an email address exists for the account
    supplied, you will get a reset password email.

    Args:
        body (CreatePasswordResetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreatePasswordResetResponse]
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
    client: Union[AuthenticatedClient, Client],
    body: CreatePasswordResetParams,
) -> Optional[CreatePasswordResetResponse]:
    """Create password reset

     Starts the password reset process for an account. If an email address exists for the account
    supplied, you will get a reset password email.

    Args:
        body (CreatePasswordResetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreatePasswordResetResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreatePasswordResetParams,
) -> Response[CreatePasswordResetResponse]:
    """Create password reset

     Starts the password reset process for an account. If an email address exists for the account
    supplied, you will get a reset password email.

    Args:
        body (CreatePasswordResetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreatePasswordResetResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreatePasswordResetParams,
) -> Optional[CreatePasswordResetResponse]:
    """Create password reset

     Starts the password reset process for an account. If an email address exists for the account
    supplied, you will get a reset password email.

    Args:
        body (CreatePasswordResetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreatePasswordResetResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
