import datetime
from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.describe_app_response import DescribeAppResponse
from ...models.error_model import ErrorModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    runs: int | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    timezone: str | Unset = "UTC",
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["runs"] = runs

    json_start_at: str | Unset = UNSET
    if not isinstance(start_at, Unset):
        json_start_at = start_at.isoformat()
    params["start_at"] = json_start_at

    json_end_at: str | Unset = UNSET
    if not isinstance(end_at, Unset):
        json_end_at = end_at.isoformat()
    params["end_at"] = json_end_at

    params["timezone"] = timezone

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{name}".format(
            name=quote(str(name), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DescribeAppResponse | ErrorModel:
    if response.status_code == 200:
        response_200 = DescribeAppResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DescribeAppResponse | ErrorModel]:
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
    runs: int | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    timezone: str | Unset = "UTC",
) -> Response[DescribeAppResponse | ErrorModel]:
    """Describe app

     Get all the runs for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (int | Unset): The number of recent runs to fetch for the app.
        start_at (datetime.datetime | Unset): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (datetime.datetime | Unset): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        timezone (str | Unset): Timezone for the statistics (e.g., 'Europe/Berlin'). Defaults to
            UTC. Default: 'UTC'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeAppResponse | ErrorModel]
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
    runs: int | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    timezone: str | Unset = "UTC",
) -> DescribeAppResponse | ErrorModel | None:
    """Describe app

     Get all the runs for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (int | Unset): The number of recent runs to fetch for the app.
        start_at (datetime.datetime | Unset): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (datetime.datetime | Unset): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        timezone (str | Unset): Timezone for the statistics (e.g., 'Europe/Berlin'). Defaults to
            UTC. Default: 'UTC'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeAppResponse | ErrorModel
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
    runs: int | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    timezone: str | Unset = "UTC",
) -> Response[DescribeAppResponse | ErrorModel]:
    """Describe app

     Get all the runs for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (int | Unset): The number of recent runs to fetch for the app.
        start_at (datetime.datetime | Unset): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (datetime.datetime | Unset): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        timezone (str | Unset): Timezone for the statistics (e.g., 'Europe/Berlin'). Defaults to
            UTC. Default: 'UTC'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeAppResponse | ErrorModel]
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
    runs: int | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    timezone: str | Unset = "UTC",
) -> DescribeAppResponse | ErrorModel | None:
    """Describe app

     Get all the runs for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (int | Unset): The number of recent runs to fetch for the app.
        start_at (datetime.datetime | Unset): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (datetime.datetime | Unset): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        timezone (str | Unset): Timezone for the statistics (e.g., 'Europe/Berlin'). Defaults to
            UTC. Default: 'UTC'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeAppResponse | ErrorModel
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
