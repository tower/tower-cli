import datetime
from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.generate_run_statistics_response import GenerateRunStatisticsResponse
from ...models.generate_run_statistics_status_item import (
    GenerateRunStatisticsStatusItem,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    status: Union[Unset, list[GenerateRunStatisticsStatusItem]] = UNSET,
    start_at: datetime.datetime,
    end_at: datetime.datetime,
    timezone: Union[Unset, str] = "UTC",
    environment: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_status: Union[Unset, list[str]] = UNSET
    if not isinstance(status, Unset):
        json_status = []
        for status_item_data in status:
            status_item = status_item_data.value
            json_status.append(status_item)

    params["status"] = json_status

    json_start_at = start_at.isoformat()
    params["start_at"] = json_start_at

    json_end_at = end_at.isoformat()
    params["end_at"] = json_end_at

    params["timezone"] = timezone

    params["environment"] = environment

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
    status: Union[Unset, list[GenerateRunStatisticsStatusItem]] = UNSET,
    start_at: datetime.datetime,
    end_at: datetime.datetime,
    timezone: Union[Unset, str] = "UTC",
    environment: Union[Unset, str] = UNSET,
) -> Response[GenerateRunStatisticsResponse]:
    """Generate run statistics

     Generates statistics about runs over a specified time period.

    Args:
        status (Union[Unset, list[GenerateRunStatisticsStatusItem]]): Filter runs by status(es).
            Define multiple with a comma-separated list. Supplying none will return all statuses.
        start_at (datetime.datetime): Start date and time for statistics (inclusive)
        end_at (datetime.datetime): End date and time for statistics (inclusive)
        timezone (Union[Unset, str]): Timezone for the statistics (e.g., 'Europe/Berlin').
            Defaults to UTC. Default: 'UTC'.
        environment (Union[Unset, str]): Filter runs by environment. If not provided, all
            environments will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GenerateRunStatisticsResponse]
    """

    kwargs = _get_kwargs(
        status=status,
        start_at=start_at,
        end_at=end_at,
        timezone=timezone,
        environment=environment,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    status: Union[Unset, list[GenerateRunStatisticsStatusItem]] = UNSET,
    start_at: datetime.datetime,
    end_at: datetime.datetime,
    timezone: Union[Unset, str] = "UTC",
    environment: Union[Unset, str] = UNSET,
) -> Optional[GenerateRunStatisticsResponse]:
    """Generate run statistics

     Generates statistics about runs over a specified time period.

    Args:
        status (Union[Unset, list[GenerateRunStatisticsStatusItem]]): Filter runs by status(es).
            Define multiple with a comma-separated list. Supplying none will return all statuses.
        start_at (datetime.datetime): Start date and time for statistics (inclusive)
        end_at (datetime.datetime): End date and time for statistics (inclusive)
        timezone (Union[Unset, str]): Timezone for the statistics (e.g., 'Europe/Berlin').
            Defaults to UTC. Default: 'UTC'.
        environment (Union[Unset, str]): Filter runs by environment. If not provided, all
            environments will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GenerateRunStatisticsResponse
    """

    return sync_detailed(
        client=client,
        status=status,
        start_at=start_at,
        end_at=end_at,
        timezone=timezone,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    status: Union[Unset, list[GenerateRunStatisticsStatusItem]] = UNSET,
    start_at: datetime.datetime,
    end_at: datetime.datetime,
    timezone: Union[Unset, str] = "UTC",
    environment: Union[Unset, str] = UNSET,
) -> Response[GenerateRunStatisticsResponse]:
    """Generate run statistics

     Generates statistics about runs over a specified time period.

    Args:
        status (Union[Unset, list[GenerateRunStatisticsStatusItem]]): Filter runs by status(es).
            Define multiple with a comma-separated list. Supplying none will return all statuses.
        start_at (datetime.datetime): Start date and time for statistics (inclusive)
        end_at (datetime.datetime): End date and time for statistics (inclusive)
        timezone (Union[Unset, str]): Timezone for the statistics (e.g., 'Europe/Berlin').
            Defaults to UTC. Default: 'UTC'.
        environment (Union[Unset, str]): Filter runs by environment. If not provided, all
            environments will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GenerateRunStatisticsResponse]
    """

    kwargs = _get_kwargs(
        status=status,
        start_at=start_at,
        end_at=end_at,
        timezone=timezone,
        environment=environment,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    status: Union[Unset, list[GenerateRunStatisticsStatusItem]] = UNSET,
    start_at: datetime.datetime,
    end_at: datetime.datetime,
    timezone: Union[Unset, str] = "UTC",
    environment: Union[Unset, str] = UNSET,
) -> Optional[GenerateRunStatisticsResponse]:
    """Generate run statistics

     Generates statistics about runs over a specified time period.

    Args:
        status (Union[Unset, list[GenerateRunStatisticsStatusItem]]): Filter runs by status(es).
            Define multiple with a comma-separated list. Supplying none will return all statuses.
        start_at (datetime.datetime): Start date and time for statistics (inclusive)
        end_at (datetime.datetime): End date and time for statistics (inclusive)
        timezone (Union[Unset, str]): Timezone for the statistics (e.g., 'Europe/Berlin').
            Defaults to UTC. Default: 'UTC'.
        environment (Union[Unset, str]): Filter runs by environment. If not provided, all
            environments will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GenerateRunStatisticsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            status=status,
            start_at=start_at,
            end_at=end_at,
            timezone=timezone,
            environment=environment,
        )
    ).parsed
