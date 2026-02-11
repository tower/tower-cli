from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
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
            code=quote(str(code), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | UpdatePasswordResetResponse:
    if response.status_code == 200:
        response_200 = UpdatePasswordResetResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | UpdatePasswordResetResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    code: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdatePasswordResetParams,
) -> Response[ErrorModel | UpdatePasswordResetResponse]:
    """Update password reset

     Updates the password reset code with the new password

    Args:
        code (str): The password reset code that was sent to you
        body (UpdatePasswordResetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdatePasswordResetResponse]
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
    client: AuthenticatedClient | Client,
    body: UpdatePasswordResetParams,
) -> ErrorModel | UpdatePasswordResetResponse | None:
    """Update password reset

     Updates the password reset code with the new password

    Args:
        code (str): The password reset code that was sent to you
        body (UpdatePasswordResetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdatePasswordResetResponse
    """

    return sync_detailed(
        code=code,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    code: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdatePasswordResetParams,
) -> Response[ErrorModel | UpdatePasswordResetResponse]:
    """Update password reset

     Updates the password reset code with the new password

    Args:
        code (str): The password reset code that was sent to you
        body (UpdatePasswordResetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdatePasswordResetResponse]
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
    client: AuthenticatedClient | Client,
    body: UpdatePasswordResetParams,
) -> ErrorModel | UpdatePasswordResetResponse | None:
    """Update password reset

     Updates the password reset code with the new password

    Args:
        code (str): The password reset code that was sent to you
        body (UpdatePasswordResetParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdatePasswordResetResponse
    """

    return (
        await asyncio_detailed(
            code=code,
            client=client,
            body=body,
        )
    ).parsed
