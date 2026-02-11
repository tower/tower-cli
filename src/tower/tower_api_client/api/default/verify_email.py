from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.verify_email_params import VerifyEmailParams
from ...models.verify_email_response import VerifyEmailResponse
from ...types import Response


def _get_kwargs(
    *,
    body: VerifyEmailParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/user/verify",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | VerifyEmailResponse:
    if response.status_code == 200:
        response_200 = VerifyEmailResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | VerifyEmailResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: VerifyEmailParams,
) -> Response[ErrorModel | VerifyEmailResponse]:
    """Verify email

     If the user hasn't verified their email address, this API endpoint allows them to send a
    confirmation token they received via email to indeed verify they can receive emails.

    Args:
        body (VerifyEmailParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | VerifyEmailResponse]
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
    body: VerifyEmailParams,
) -> ErrorModel | VerifyEmailResponse | None:
    """Verify email

     If the user hasn't verified their email address, this API endpoint allows them to send a
    confirmation token they received via email to indeed verify they can receive emails.

    Args:
        body (VerifyEmailParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | VerifyEmailResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: VerifyEmailParams,
) -> Response[ErrorModel | VerifyEmailResponse]:
    """Verify email

     If the user hasn't verified their email address, this API endpoint allows them to send a
    confirmation token they received via email to indeed verify they can receive emails.

    Args:
        body (VerifyEmailParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | VerifyEmailResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: VerifyEmailParams,
) -> ErrorModel | VerifyEmailResponse | None:
    """Verify email

     If the user hasn't verified their email address, this API endpoint allows them to send a
    confirmation token they received via email to indeed verify they can receive emails.

    Args:
        body (VerifyEmailParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | VerifyEmailResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
