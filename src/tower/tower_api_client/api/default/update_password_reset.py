from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.update_password_reset_params import UpdatePasswordResetParams
from ...models.update_password_reset_response import UpdatePasswordResetResponse
from ...types import Response


def _get_kwargs(
    code: str,
    *,
    body: UpdatePasswordResetParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/accounts/password-reset/{code}".format(
            code=code,
        ),
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[UpdatePasswordResetResponse]:
    if response.status_code == 200:
        response_200 = UpdatePasswordResetResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[UpdatePasswordResetResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    code: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdatePasswordResetParams,
) -> Response[UpdatePasswordResetResponse]:
    """Update password reset

     Updates the password reset code with the new password

    Args:
        code (str): The password reset code that was sent to you
        body (UpdatePasswordResetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[UpdatePasswordResetResponse]
    """

    kwargs = _get_kwargs(
        code=code,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    code: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdatePasswordResetParams,
) -> Optional[UpdatePasswordResetResponse]:
    """Update password reset

     Updates the password reset code with the new password

    Args:
        code (str): The password reset code that was sent to you
        body (UpdatePasswordResetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        UpdatePasswordResetResponse
    """

    return sync_detailed(
        code=code,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    code: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdatePasswordResetParams,
) -> Response[UpdatePasswordResetResponse]:
    """Update password reset

     Updates the password reset code with the new password

    Args:
        code (str): The password reset code that was sent to you
        body (UpdatePasswordResetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[UpdatePasswordResetResponse]
    """

    kwargs = _get_kwargs(
        code=code,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    code: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdatePasswordResetParams,
) -> Optional[UpdatePasswordResetResponse]:
    """Update password reset

     Updates the password reset code with the new password

    Args:
        code (str): The password reset code that was sent to you
        body (UpdatePasswordResetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        UpdatePasswordResetResponse
    """

    return (
        await asyncio_detailed(
            code=code,
            client=client,
            body=body,
        )
    ).parsed
