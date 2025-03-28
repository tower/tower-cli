from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.refresh_session_response import RefreshSessionResponse
from ...types import Response


def _get_kwargs(
    *,
    client: AuthenticatedClient,
) -> Dict[str, Any]:
    url = "{}/session/refresh".format(client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "post",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, response: httpx.Response) -> Optional[RefreshSessionResponse]:
    if response.status_code == 200:
        response_200 = RefreshSessionResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[RefreshSessionResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[RefreshSessionResponse]:
    """Refresh session

     Returns a new session based on the supplied authentication context. This is helpful when clients
    want to use POST instead of GET to check session information.

    Returns:
        Response[RefreshSessionResponse]
    """

    kwargs = _get_kwargs(
        client=client,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: AuthenticatedClient,
) -> Optional[RefreshSessionResponse]:
    """Refresh session

     Returns a new session based on the supplied authentication context. This is helpful when clients
    want to use POST instead of GET to check session information.

    Returns:
        Response[RefreshSessionResponse]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[RefreshSessionResponse]:
    """Refresh session

     Returns a new session based on the supplied authentication context. This is helpful when clients
    want to use POST instead of GET to check session information.

    Returns:
        Response[RefreshSessionResponse]
    """

    kwargs = _get_kwargs(
        client=client,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
) -> Optional[RefreshSessionResponse]:
    """Refresh session

     Returns a new session based on the supplied authentication context. This is helpful when clients
    want to use POST instead of GET to check session information.

    Returns:
        Response[RefreshSessionResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
