from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.describe_secrets_key_response import DescribeSecretsKeyResponse
from ...models.error_model import ErrorModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    format_: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["format"] = format_

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/secrets/key",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DescribeSecretsKeyResponse | ErrorModel:
    if response.status_code == 200:
        response_200 = DescribeSecretsKeyResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DescribeSecretsKeyResponse | ErrorModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    format_: str | Unset = UNSET,
) -> Response[DescribeSecretsKeyResponse | ErrorModel]:
    """Describe encryption key

     Gets the encryption key used for encrypting secrets that you want to create in Tower.

    Args:
        format_ (str | Unset): The format to return the key in. Options are 'pkcs1' and 'spki'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeSecretsKeyResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        format_=format_,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    format_: str | Unset = UNSET,
) -> DescribeSecretsKeyResponse | ErrorModel | None:
    """Describe encryption key

     Gets the encryption key used for encrypting secrets that you want to create in Tower.

    Args:
        format_ (str | Unset): The format to return the key in. Options are 'pkcs1' and 'spki'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeSecretsKeyResponse | ErrorModel
    """

    return sync_detailed(
        client=client,
        format_=format_,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    format_: str | Unset = UNSET,
) -> Response[DescribeSecretsKeyResponse | ErrorModel]:
    """Describe encryption key

     Gets the encryption key used for encrypting secrets that you want to create in Tower.

    Args:
        format_ (str | Unset): The format to return the key in. Options are 'pkcs1' and 'spki'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeSecretsKeyResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        format_=format_,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    format_: str | Unset = UNSET,
) -> DescribeSecretsKeyResponse | ErrorModel | None:
    """Describe encryption key

     Gets the encryption key used for encrypting secrets that you want to create in Tower.

    Args:
        format_ (str | Unset): The format to return the key in. Options are 'pkcs1' and 'spki'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeSecretsKeyResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            client=client,
            format_=format_,
        )
    ).parsed
