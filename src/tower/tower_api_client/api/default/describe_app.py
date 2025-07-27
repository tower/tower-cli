import datetime
from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.describe_app_response import DescribeAppResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    runs: Union[Unset, int] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    timezone: Union[Unset, str] = "UTC",
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["runs"] = runs

    json_start_at: Union[Unset, str] = UNSET
    if not isinstance(start_at, Unset):
        json_start_at = start_at.isoformat()
    params["start_at"] = json_start_at

    json_end_at: Union[Unset, str] = UNSET
    if not isinstance(end_at, Unset):
        json_end_at = end_at.isoformat()
    params["end_at"] = json_end_at

    params["timezone"] = timezone

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{name}".format(
            name=name,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[DescribeAppResponse]:
    if response.status_code == 200:
        response_200 = DescribeAppResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[DescribeAppResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    runs: Union[Unset, int] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    timezone: Union[Unset, str] = "UTC",
) -> Response[DescribeAppResponse]:
    """Describe app

     Get all the runs for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (Union[Unset, int]): The number of recent runs to fetch for the app.
        start_at (Union[Unset, datetime.datetime]): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (Union[Unset, datetime.datetime]): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        timezone (Union[Unset, str]): Timezone for the statistics (e.g., 'Europe/Berlin').
            Defaults to UTC. Default: 'UTC'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeAppResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        runs=runs,
        start_at=start_at,
        end_at=end_at,
        timezone=timezone,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient,
    runs: Union[Unset, int] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    timezone: Union[Unset, str] = "UTC",
) -> Optional[DescribeAppResponse]:
    """Describe app

     Get all the runs for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (Union[Unset, int]): The number of recent runs to fetch for the app.
        start_at (Union[Unset, datetime.datetime]): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (Union[Unset, datetime.datetime]): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        timezone (Union[Unset, str]): Timezone for the statistics (e.g., 'Europe/Berlin').
            Defaults to UTC. Default: 'UTC'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeAppResponse
    """

    return sync_detailed(
        name=name,
        client=client,
        runs=runs,
        start_at=start_at,
        end_at=end_at,
        timezone=timezone,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    runs: Union[Unset, int] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    timezone: Union[Unset, str] = "UTC",
) -> Response[DescribeAppResponse]:
    """Describe app

     Get all the runs for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (Union[Unset, int]): The number of recent runs to fetch for the app.
        start_at (Union[Unset, datetime.datetime]): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (Union[Unset, datetime.datetime]): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        timezone (Union[Unset, str]): Timezone for the statistics (e.g., 'Europe/Berlin').
            Defaults to UTC. Default: 'UTC'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeAppResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        runs=runs,
        start_at=start_at,
        end_at=end_at,
        timezone=timezone,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
    runs: Union[Unset, int] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    timezone: Union[Unset, str] = "UTC",
) -> Optional[DescribeAppResponse]:
    """Describe app

     Get all the runs for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (Union[Unset, int]): The number of recent runs to fetch for the app.
        start_at (Union[Unset, datetime.datetime]): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (Union[Unset, datetime.datetime]): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        timezone (Union[Unset, str]): Timezone for the statistics (e.g., 'Europe/Berlin').
            Defaults to UTC. Default: 'UTC'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeAppResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            runs=runs,
            start_at=start_at,
            end_at=end_at,
            timezone=timezone,
        )
    ).parsed
