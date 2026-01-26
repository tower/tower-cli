import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.search_runs_response import SearchRunsResponse
from ...models.search_runs_status_item import SearchRunsStatusItem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    status: list[SearchRunsStatusItem] | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["page"] = page

    params["page_size"] = page_size

    json_status: list[str] | Unset = UNSET
    if not isinstance(status, Unset):
        json_status = []
        for status_item_data in status:
            status_item = status_item_data.value
            json_status.append(status_item)

    params["status"] = json_status

    json_start_at: str | Unset = UNSET
    if not isinstance(start_at, Unset):
        json_start_at = start_at.isoformat()
    params["start_at"] = json_start_at

    json_end_at: str | Unset = UNSET
    if not isinstance(end_at, Unset):
        json_end_at = end_at.isoformat()
    params["end_at"] = json_end_at

    params["environment"] = environment

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/runs",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | SearchRunsResponse:
    if response.status_code == 200:
        response_200 = SearchRunsResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | SearchRunsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    status: list[SearchRunsStatusItem] | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> Response[ErrorModel | SearchRunsResponse]:
    """Search runs

     Search, filter, and list runs across all of the apps in your account.

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        status (list[SearchRunsStatusItem] | Unset): Filter runs by status(es). Define multiple
            with a comma-separated list. Supplying none will return all statuses.
        start_at (datetime.datetime | Unset): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (datetime.datetime | Unset): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        environment (str | Unset): Filter runs by environment. If not provided, all environments
            will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | SearchRunsResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        page_size=page_size,
        status=status,
        start_at=start_at,
        end_at=end_at,
        environment=environment,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    status: list[SearchRunsStatusItem] | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> ErrorModel | SearchRunsResponse | None:
    """Search runs

     Search, filter, and list runs across all of the apps in your account.

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        status (list[SearchRunsStatusItem] | Unset): Filter runs by status(es). Define multiple
            with a comma-separated list. Supplying none will return all statuses.
        start_at (datetime.datetime | Unset): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (datetime.datetime | Unset): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        environment (str | Unset): Filter runs by environment. If not provided, all environments
            will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | SearchRunsResponse
    """

    return sync_detailed(
        client=client,
        page=page,
        page_size=page_size,
        status=status,
        start_at=start_at,
        end_at=end_at,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    status: list[SearchRunsStatusItem] | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> Response[ErrorModel | SearchRunsResponse]:
    """Search runs

     Search, filter, and list runs across all of the apps in your account.

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        status (list[SearchRunsStatusItem] | Unset): Filter runs by status(es). Define multiple
            with a comma-separated list. Supplying none will return all statuses.
        start_at (datetime.datetime | Unset): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (datetime.datetime | Unset): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        environment (str | Unset): Filter runs by environment. If not provided, all environments
            will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | SearchRunsResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        page_size=page_size,
        status=status,
        start_at=start_at,
        end_at=end_at,
        environment=environment,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    status: list[SearchRunsStatusItem] | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> ErrorModel | SearchRunsResponse | None:
    """Search runs

     Search, filter, and list runs across all of the apps in your account.

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        status (list[SearchRunsStatusItem] | Unset): Filter runs by status(es). Define multiple
            with a comma-separated list. Supplying none will return all statuses.
        start_at (datetime.datetime | Unset): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (datetime.datetime | Unset): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        environment (str | Unset): Filter runs by environment. If not provided, all environments
            will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | SearchRunsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            page_size=page_size,
            status=status,
            start_at=start_at,
            end_at=end_at,
            environment=environment,
        )
    ).parsed
