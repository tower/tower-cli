from http import HTTPStatus
from typing import Any, Dict

import httpx

from ...client import AuthenticatedClient
from ...types import Response


def _get_kwargs(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Dict[str, Any]:
    url = "{}/apps/{name}/runs/{seq}/logs/stream".format(
        client.base_url, name=name, seq=seq
    )

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _build_response(*, response: httpx.Response) -> Response[Any]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=None,
    )


def sync_detailed(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Response[Any]:
    """Stream logs for a specific app run

     Streams the logs associated with a particular run of an app in real-time.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        name=name,
        seq=seq,
        client=client,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


async def asyncio_detailed(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Response[Any]:
    """Stream logs for a specific app run

     Streams the logs associated with a particular run of an app in real-time.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        name=name,
        seq=seq,
        client=client,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)
