from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_secret_params import CreateSecretParams
from ...models.create_secret_response import CreateSecretResponse
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs(
    *,
    body: CreateSecretParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/secrets",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[CreateSecretResponse, ErrorModel]]:
    if response.status_code == 201:
        response_201 = CreateSecretResponse.from_dict(response.json())

        return response_201
    if response.status_code == 401:
        response_401 = ErrorModel.from_dict(response.json())

        return response_401
    if response.status_code == 409:
        response_409 = ErrorModel.from_dict(response.json())

        return response_409
    if response.status_code == 412:
        response_412 = ErrorModel.from_dict(response.json())

        return response_412
    if response.status_code == 500:
        response_500 = ErrorModel.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[CreateSecretResponse, ErrorModel]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: CreateSecretParams,
) -> Response[Union[CreateSecretResponse, ErrorModel]]:
    """Create secret

     Creates a new secret and associates it with the current account.

    Args:
        body (CreateSecretParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CreateSecretResponse, ErrorModel]]
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
    body: CreateSecretParams,
) -> Optional[Union[CreateSecretResponse, ErrorModel]]:
    """Create secret

     Creates a new secret and associates it with the current account.

    Args:
        body (CreateSecretParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CreateSecretResponse, ErrorModel]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: CreateSecretParams,
) -> Response[Union[CreateSecretResponse, ErrorModel]]:
    """Create secret

     Creates a new secret and associates it with the current account.

    Args:
        body (CreateSecretParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CreateSecretResponse, ErrorModel]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: CreateSecretParams,
) -> Optional[Union[CreateSecretResponse, ErrorModel]]:
    """Create secret

     Creates a new secret and associates it with the current account.

    Args:
        body (CreateSecretParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CreateSecretResponse, ErrorModel]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
