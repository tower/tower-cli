from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.generate_app_statistics_response import GenerateAppStatisticsResponse
from ...types import Response


def _get_kwargs(
    *,
    client: AuthenticatedClient,
) -> Dict[str, Any]:
    url = "{}/stats/apps".format(client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(
    *, response: httpx.Response
) -> Optional[GenerateAppStatisticsResponse]:
    if response.status_code == 200:
        response_200 = GenerateAppStatisticsResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(
    *, response: httpx.Response
) -> Response[GenerateAppStatisticsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[GenerateAppStatisticsResponse]:
    """Generate app statistics

     Generates current statistics about apps

    Returns:
        Response[GenerateAppStatisticsResponse]
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
) -> Optional[GenerateAppStatisticsResponse]:
    """Generate app statistics

     Generates current statistics about apps

    Returns:
        Response[GenerateAppStatisticsResponse]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[GenerateAppStatisticsResponse]:
    """Generate app statistics

     Generates current statistics about apps

    Returns:
        Response[GenerateAppStatisticsResponse]
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
) -> Optional[GenerateAppStatisticsResponse]:
    """Generate app statistics

     Generates current statistics about apps

    Returns:
        Response[GenerateAppStatisticsResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
