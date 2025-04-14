from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.generate_run_statistics_response import GenerateRunStatisticsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    period: Union[Unset, None, str] = "24h",
) -> Dict[str, Any]:
    url = "{}/stats/runs".format(client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    params: Dict[str, Any] = {}
    params["period"] = period

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
) -> Optional[GenerateRunStatisticsResponse]:
    if response.status_code == 200:
        response_200 = GenerateRunStatisticsResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(
    *, response: httpx.Response
) -> Response[GenerateRunStatisticsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    period: Union[Unset, None, str] = "24h",
) -> Response[GenerateRunStatisticsResponse]:
    """Generate run statistics

     Generates statistics about runs over a specified time period.

    Args:
        period (Union[Unset, None, str]): Time period for statistics (24h, 7d, 30d) Default:
            '24h'.

    Returns:
        Response[GenerateRunStatisticsResponse]
    """

    kwargs = _get_kwargs(
        client=client,
        period=period,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: AuthenticatedClient,
    period: Union[Unset, None, str] = "24h",
) -> Optional[GenerateRunStatisticsResponse]:
    """Generate run statistics

     Generates statistics about runs over a specified time period.

    Args:
        period (Union[Unset, None, str]): Time period for statistics (24h, 7d, 30d) Default:
            '24h'.

    Returns:
        Response[GenerateRunStatisticsResponse]
    """

    return sync_detailed(
        client=client,
        period=period,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    period: Union[Unset, None, str] = "24h",
) -> Response[GenerateRunStatisticsResponse]:
    """Generate run statistics

     Generates statistics about runs over a specified time period.

    Args:
        period (Union[Unset, None, str]): Time period for statistics (24h, 7d, 30d) Default:
            '24h'.

    Returns:
        Response[GenerateRunStatisticsResponse]
    """

    kwargs = _get_kwargs(
        client=client,
        period=period,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    period: Union[Unset, None, str] = "24h",
) -> Optional[GenerateRunStatisticsResponse]:
    """Generate run statistics

     Generates statistics about runs over a specified time period.

    Args:
        period (Union[Unset, None, str]): Time period for statistics (24h, 7d, 30d) Default:
            '24h'.

    Returns:
        Response[GenerateRunStatisticsResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            period=period,
        )
    ).parsed
