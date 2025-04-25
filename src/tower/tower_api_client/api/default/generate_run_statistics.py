from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.generate_run_statistics_response import GenerateRunStatisticsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    period: Union[Unset, str] = "24h",
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["period"] = period

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/stats/runs",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GenerateRunStatisticsResponse]:
    if response.status_code == 200:
        response_200 = GenerateRunStatisticsResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GenerateRunStatisticsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    period: Union[Unset, str] = "24h",
) -> Response[GenerateRunStatisticsResponse]:
    """Generate run statistics

     Generates statistics about runs over a specified time period.

    Args:
        period (Union[Unset, str]): Time period for statistics (24h, 7d, 30d) Default: '24h'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GenerateRunStatisticsResponse]
    """

    kwargs = _get_kwargs(
        period=period,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    period: Union[Unset, str] = "24h",
) -> Optional[GenerateRunStatisticsResponse]:
    """Generate run statistics

     Generates statistics about runs over a specified time period.

    Args:
        period (Union[Unset, str]): Time period for statistics (24h, 7d, 30d) Default: '24h'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GenerateRunStatisticsResponse
    """

    return sync_detailed(
        client=client,
        period=period,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    period: Union[Unset, str] = "24h",
) -> Response[GenerateRunStatisticsResponse]:
    """Generate run statistics

     Generates statistics about runs over a specified time period.

    Args:
        period (Union[Unset, str]): Time period for statistics (24h, 7d, 30d) Default: '24h'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GenerateRunStatisticsResponse]
    """

    kwargs = _get_kwargs(
        period=period,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    period: Union[Unset, str] = "24h",
) -> Optional[GenerateRunStatisticsResponse]:
    """Generate run statistics

     Generates statistics about runs over a specified time period.

    Args:
        period (Union[Unset, str]): Time period for statistics (24h, 7d, 30d) Default: '24h'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GenerateRunStatisticsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            period=period,
        )
    ).parsed
