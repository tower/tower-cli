from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_secrets_key_output_body import GetSecretsKeyOutputBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    format_: Union[Unset, str] = UNSET,
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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GetSecretsKeyOutputBody]:
    if response.status_code == 200:
        response_200 = GetSecretsKeyOutputBody.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GetSecretsKeyOutputBody]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    format_: Union[Unset, str] = UNSET,
) -> Response[GetSecretsKeyOutputBody]:
    """Get the encryption key for secrets.

     Get the encryption key for secrets.

    Args:
        format_ (Union[Unset, str]): The format to return the key in. Options are 'pkcs1' and
            'spki'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetSecretsKeyOutputBody]
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
    format_: Union[Unset, str] = UNSET,
) -> Optional[GetSecretsKeyOutputBody]:
    """Get the encryption key for secrets.

     Get the encryption key for secrets.

    Args:
        format_ (Union[Unset, str]): The format to return the key in. Options are 'pkcs1' and
            'spki'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetSecretsKeyOutputBody
    """

    return sync_detailed(
        client=client,
        format_=format_,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    format_: Union[Unset, str] = UNSET,
) -> Response[GetSecretsKeyOutputBody]:
    """Get the encryption key for secrets.

     Get the encryption key for secrets.

    Args:
        format_ (Union[Unset, str]): The format to return the key in. Options are 'pkcs1' and
            'spki'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetSecretsKeyOutputBody]
    """

    kwargs = _get_kwargs(
        format_=format_,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    format_: Union[Unset, str] = UNSET,
) -> Optional[GetSecretsKeyOutputBody]:
    """Get the encryption key for secrets.

     Get the encryption key for secrets.

    Args:
        format_ (Union[Unset, str]): The format to return the key in. Options are 'pkcs1' and
            'spki'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetSecretsKeyOutputBody
    """

    return (
        await asyncio_detailed(
            client=client,
            format_=format_,
        )
    ).parsed
