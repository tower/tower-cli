from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.describe_secrets_key_response import DescribeSecretsKeyResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    format_: Union[Unset, None, str] = UNSET,
) -> Dict[str, Any]:
    url = "{}/secrets/key".format(client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    params: Dict[str, Any] = {}
    params["format"] = format_

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(
    *, response: httpx.Response
) -> Optional[DescribeSecretsKeyResponse]:
    if response.status_code == 200:
        response_200 = DescribeSecretsKeyResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(
    *, response: httpx.Response
) -> Response[DescribeSecretsKeyResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    format_: Union[Unset, None, str] = UNSET,
) -> Response[DescribeSecretsKeyResponse]:
    """Describe encryption key

     Gets the encryption key used for encrypting secrets that you want to create in Tower.

    Args:
        format_ (Union[Unset, None, str]): The format to return the key in. Options are 'pkcs1'
            and 'spki'.

    Returns:
        Response[DescribeSecretsKeyResponse]
    """

    kwargs = _get_kwargs(
        client=client,
        format_=format_,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: AuthenticatedClient,
    format_: Union[Unset, None, str] = UNSET,
) -> Optional[DescribeSecretsKeyResponse]:
    """Describe encryption key

     Gets the encryption key used for encrypting secrets that you want to create in Tower.

    Args:
        format_ (Union[Unset, None, str]): The format to return the key in. Options are 'pkcs1'
            and 'spki'.

    Returns:
        Response[DescribeSecretsKeyResponse]
    """

    return sync_detailed(
        client=client,
        format_=format_,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    format_: Union[Unset, None, str] = UNSET,
) -> Response[DescribeSecretsKeyResponse]:
    """Describe encryption key

     Gets the encryption key used for encrypting secrets that you want to create in Tower.

    Args:
        format_ (Union[Unset, None, str]): The format to return the key in. Options are 'pkcs1'
            and 'spki'.

    Returns:
        Response[DescribeSecretsKeyResponse]
    """

    kwargs = _get_kwargs(
        client=client,
        format_=format_,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    format_: Union[Unset, None, str] = UNSET,
) -> Optional[DescribeSecretsKeyResponse]:
    """Describe encryption key

     Gets the encryption key used for encrypting secrets that you want to create in Tower.

    Args:
        format_ (Union[Unset, None, str]): The format to return the key in. Options are 'pkcs1'
            and 'spki'.

    Returns:
        Response[DescribeSecretsKeyResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            format_=format_,
        )
    ).parsed
