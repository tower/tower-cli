from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import Client
from ...models.create_account_params import CreateAccountParams
from ...models.create_account_response import CreateAccountResponse
from ...types import Response


def _get_kwargs(
    *,
    client: Client,
    json_body: CreateAccountParams,
) -> Dict[str, Any]:
    url = "{}/accounts".format(client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    json_json_body = json_body.to_dict()

    return {
        "method": "post",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
    }


def _parse_response(*, response: httpx.Response) -> Optional[CreateAccountResponse]:
    if response.status_code == 200:
        response_200 = CreateAccountResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[CreateAccountResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: Client,
    json_body: CreateAccountParams,
) -> Response[CreateAccountResponse]:
    """Create account

     This is the primary way that users register new accounts with Tower.

    Args:
        json_body (CreateAccountParams):

    Returns:
        Response[CreateAccountResponse]
    """

    kwargs = _get_kwargs(
        client=client,
        json_body=json_body,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: Client,
    json_body: CreateAccountParams,
) -> Optional[CreateAccountResponse]:
    """Create account

     This is the primary way that users register new accounts with Tower.

    Args:
        json_body (CreateAccountParams):

    Returns:
        Response[CreateAccountResponse]
    """

    return sync_detailed(
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Client,
    json_body: CreateAccountParams,
) -> Response[CreateAccountResponse]:
    """Create account

     This is the primary way that users register new accounts with Tower.

    Args:
        json_body (CreateAccountParams):

    Returns:
        Response[CreateAccountResponse]
    """

    kwargs = _get_kwargs(
        client=client,
        json_body=json_body,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: Client,
    json_body: CreateAccountParams,
) -> Optional[CreateAccountResponse]:
    """Create account

     This is the primary way that users register new accounts with Tower.

    Args:
        json_body (CreateAccountParams):

    Returns:
        Response[CreateAccountResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            json_body=json_body,
        )
    ).parsed
