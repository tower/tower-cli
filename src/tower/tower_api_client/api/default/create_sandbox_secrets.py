from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_sandbox_secrets_params import CreateSandboxSecretsParams
from ...models.create_sandbox_secrets_response import CreateSandboxSecretsResponse
from ...types import Response


def _get_kwargs(
    *,
    body: CreateSandboxSecretsParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/sandbox/secrets",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[CreateSandboxSecretsResponse]:
    if response.status_code == 200:
        response_200 = CreateSandboxSecretsResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[CreateSandboxSecretsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: CreateSandboxSecretsParams,
) -> Response[CreateSandboxSecretsResponse]:
    """Create Tower-provided sandbox secrets

     Creates secrets with Tower-provided default values for the specified keys in the given environment.

    Args:
        body (CreateSandboxSecretsParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreateSandboxSecretsResponse]
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
    body: CreateSandboxSecretsParams,
) -> Optional[CreateSandboxSecretsResponse]:
    """Create Tower-provided sandbox secrets

     Creates secrets with Tower-provided default values for the specified keys in the given environment.

    Args:
        body (CreateSandboxSecretsParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreateSandboxSecretsResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: CreateSandboxSecretsParams,
) -> Response[CreateSandboxSecretsResponse]:
    """Create Tower-provided sandbox secrets

     Creates secrets with Tower-provided default values for the specified keys in the given environment.

    Args:
        body (CreateSandboxSecretsParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreateSandboxSecretsResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: CreateSandboxSecretsParams,
) -> Optional[CreateSandboxSecretsResponse]:
    """Create Tower-provided sandbox secrets

     Creates secrets with Tower-provided default values for the specified keys in the given environment.

    Args:
        body (CreateSandboxSecretsParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreateSandboxSecretsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
