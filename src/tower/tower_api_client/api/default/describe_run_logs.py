import datetime
from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.describe_run_logs_response import DescribeRunLogsResponse
from ...models.error_model import ErrorModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    seq: int,
    *,
    start_at: datetime.datetime | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_start_at: str | Unset = UNSET
    if not isinstance(start_at, Unset):
        json_start_at = start_at.isoformat()
    params["start_at"] = json_start_at

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{name}/runs/{seq}/logs".format(
            name=quote(str(name), safe=""),
            seq=quote(str(seq), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DescribeRunLogsResponse | ErrorModel:
    if response.status_code == 200:
        response_200 = DescribeRunLogsResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DescribeRunLogsResponse | ErrorModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
    start_at: datetime.datetime | Unset = UNSET,
) -> Response[DescribeRunLogsResponse | ErrorModel]:
    """Describe run logs

     Retrieves the logs associated with a particular run of an app.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.
        start_at (datetime.datetime | Unset): Fetch logs from this timestamp onwards (inclusive).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeRunLogsResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        name=name,
        seq=seq,
        start_at=start_at,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
    start_at: datetime.datetime | Unset = UNSET,
) -> DescribeRunLogsResponse | ErrorModel | None:
    """Describe run logs

     Retrieves the logs associated with a particular run of an app.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.
        start_at (datetime.datetime | Unset): Fetch logs from this timestamp onwards (inclusive).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeRunLogsResponse | ErrorModel
    """

    return sync_detailed(
        name=name,
        seq=seq,
        client=client,
        start_at=start_at,
    ).parsed


async def asyncio_detailed(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
    start_at: datetime.datetime | Unset = UNSET,
) -> Response[DescribeRunLogsResponse | ErrorModel]:
    """Describe run logs

     Retrieves the logs associated with a particular run of an app.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.
        start_at (datetime.datetime | Unset): Fetch logs from this timestamp onwards (inclusive).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeRunLogsResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        name=name,
        seq=seq,
        start_at=start_at,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
    start_at: datetime.datetime | Unset = UNSET,
) -> DescribeRunLogsResponse | ErrorModel | None:
    """Describe run logs

     Retrieves the logs associated with a particular run of an app.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.
        start_at (datetime.datetime | Unset): Fetch logs from this timestamp onwards (inclusive).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeRunLogsResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            name=name,
            seq=seq,
            client=client,
            start_at=start_at,
        )
    ).parsed
