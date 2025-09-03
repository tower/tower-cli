import datetime
from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.search_runs_response import SearchRunsResponse
from ...models.search_runs_status_item import SearchRunsStatusItem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 20,
    status: Union[Unset, list[SearchRunsStatusItem]] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["page"] = page

    params["page_size"] = page_size

    json_status: Union[Unset, list[str]] = UNSET
    if not isinstance(status, Unset):
        json_status = []
        for status_item_data in status:
            status_item = status_item_data.value
            json_status.append(status_item)

    params["status"] = json_status

    json_start_at: Union[Unset, str] = UNSET
    if not isinstance(start_at, Unset):
        json_start_at = start_at.isoformat()
    params["start_at"] = json_start_at

    json_end_at: Union[Unset, str] = UNSET
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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[SearchRunsResponse]:
    if response.status_code == 200:
        response_200 = SearchRunsResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[SearchRunsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 20,
    status: Union[Unset, list[SearchRunsStatusItem]] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Response[SearchRunsResponse]:
    """Search runs

     Search, filter, and list runs across all of the apps in your account.

    Args:
        page (Union[Unset, int]): The page number to fetch. Default: 1.
        page_size (Union[Unset, int]): The number of records to fetch on each page. Default: 20.
        status (Union[Unset, list[SearchRunsStatusItem]]): Filter runs by status(es). Define
            multiple with a comma-separated list. Supplying none will return all statuses.
        start_at (Union[Unset, datetime.datetime]): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (Union[Unset, datetime.datetime]): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        environment (Union[Unset, str]): Filter runs by environment. If not provided, all
            environments will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[SearchRunsResponse]
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
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 20,
    status: Union[Unset, list[SearchRunsStatusItem]] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Optional[SearchRunsResponse]:
    """Search runs

     Search, filter, and list runs across all of the apps in your account.

    Args:
        page (Union[Unset, int]): The page number to fetch. Default: 1.
        page_size (Union[Unset, int]): The number of records to fetch on each page. Default: 20.
        status (Union[Unset, list[SearchRunsStatusItem]]): Filter runs by status(es). Define
            multiple with a comma-separated list. Supplying none will return all statuses.
        start_at (Union[Unset, datetime.datetime]): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (Union[Unset, datetime.datetime]): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        environment (Union[Unset, str]): Filter runs by environment. If not provided, all
            environments will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        SearchRunsResponse
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
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 20,
    status: Union[Unset, list[SearchRunsStatusItem]] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Response[SearchRunsResponse]:
    """Search runs

     Search, filter, and list runs across all of the apps in your account.

    Args:
        page (Union[Unset, int]): The page number to fetch. Default: 1.
        page_size (Union[Unset, int]): The number of records to fetch on each page. Default: 20.
        status (Union[Unset, list[SearchRunsStatusItem]]): Filter runs by status(es). Define
            multiple with a comma-separated list. Supplying none will return all statuses.
        start_at (Union[Unset, datetime.datetime]): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (Union[Unset, datetime.datetime]): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        environment (Union[Unset, str]): Filter runs by environment. If not provided, all
            environments will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[SearchRunsResponse]
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
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 20,
    status: Union[Unset, list[SearchRunsStatusItem]] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Optional[SearchRunsResponse]:
    """Search runs

     Search, filter, and list runs across all of the apps in your account.

    Args:
        page (Union[Unset, int]): The page number to fetch. Default: 1.
        page_size (Union[Unset, int]): The number of records to fetch on each page. Default: 20.
        status (Union[Unset, list[SearchRunsStatusItem]]): Filter runs by status(es). Define
            multiple with a comma-separated list. Supplying none will return all statuses.
        start_at (Union[Unset, datetime.datetime]): Filter runs scheduled after this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        end_at (Union[Unset, datetime.datetime]): Filter runs scheduled before or at this datetime
            (inclusive). Provide timestamps in ISO-8601 format.
        environment (Union[Unset, str]): Filter runs by environment. If not provided, all
            environments will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        SearchRunsResponse
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
