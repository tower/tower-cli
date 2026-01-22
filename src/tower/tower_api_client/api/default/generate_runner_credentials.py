from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.generate_runner_credentials_response import (
    GenerateRunnerCredentialsResponse,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/runners/credentials",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | GenerateRunnerCredentialsResponse:
    if response.status_code == 200:
        response_200 = GenerateRunnerCredentialsResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | GenerateRunnerCredentialsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[ErrorModel | GenerateRunnerCredentialsResponse]:
    """Generate runner credentials

     Uses your current authentication context to generate runner credentials that are used for
    authenticating runner requests

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | GenerateRunnerCredentialsResponse]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
) -> ErrorModel | GenerateRunnerCredentialsResponse | None:
    """Generate runner credentials

     Uses your current authentication context to generate runner credentials that are used for
    authenticating runner requests

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | GenerateRunnerCredentialsResponse
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[ErrorModel | GenerateRunnerCredentialsResponse]:
    """Generate runner credentials

     Uses your current authentication context to generate runner credentials that are used for
    authenticating runner requests

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | GenerateRunnerCredentialsResponse]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
) -> ErrorModel | GenerateRunnerCredentialsResponse | None:
    """Generate runner credentials

     Uses your current authentication context to generate runner credentials that are used for
    authenticating runner requests

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | GenerateRunnerCredentialsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
