from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_apps_filter import ListAppsFilter
from ...models.list_apps_response import ListAppsResponse
from ...models.list_apps_sort import ListAppsSort
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    query: Union[Unset, str] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
    num_runs: Union[Unset, int] = 20,
    sort: Union[Unset, ListAppsSort] = ListAppsSort.CREATED_AT,
    filter_: Union[Unset, ListAppsFilter] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["query"] = query

    params["page"] = page

    params["page_size"] = page_size

    params["num_runs"] = num_runs

    json_sort: Union[Unset, str] = UNSET
    if not isinstance(sort, Unset):
        json_sort = sort.value

    params["sort"] = json_sort

    json_filter_: Union[Unset, str] = UNSET
    if not isinstance(filter_, Unset):
        json_filter_ = filter_.value

    params["filter"] = json_filter_

    params["environment"] = environment

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[ListAppsResponse]:
    if response.status_code == 200:
        response_200 = ListAppsResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[ListAppsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    query: Union[Unset, str] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
    num_runs: Union[Unset, int] = 20,
    sort: Union[Unset, ListAppsSort] = ListAppsSort.CREATED_AT,
    filter_: Union[Unset, ListAppsFilter] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Response[ListAppsResponse]:
    """List apps

     Get all the apps for the current account.

    Args:
        query (Union[Unset, str]): The search query to filter apps by.
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.
        num_runs (Union[Unset, int]): Number of recent runs to fetch (-1 for all runs, defaults to
            20) Default: 20.
        sort (Union[Unset, ListAppsSort]): Sort order for the results. Default:
            ListAppsSort.CREATED_AT.
        filter_ (Union[Unset, ListAppsFilter]): Filter to see apps with certain statuses.
        environment (Union[Unset, str]): The environment to filter the apps by. If not provided,
            apps for all environments will be returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListAppsResponse]
    """

    kwargs = _get_kwargs(
        query=query,
        page=page,
        page_size=page_size,
        num_runs=num_runs,
        sort=sort,
        filter_=filter_,
        environment=environment,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    query: Union[Unset, str] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
    num_runs: Union[Unset, int] = 20,
    sort: Union[Unset, ListAppsSort] = ListAppsSort.CREATED_AT,
    filter_: Union[Unset, ListAppsFilter] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Optional[ListAppsResponse]:
    """List apps

     Get all the apps for the current account.

    Args:
        query (Union[Unset, str]): The search query to filter apps by.
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.
        num_runs (Union[Unset, int]): Number of recent runs to fetch (-1 for all runs, defaults to
            20) Default: 20.
        sort (Union[Unset, ListAppsSort]): Sort order for the results. Default:
            ListAppsSort.CREATED_AT.
        filter_ (Union[Unset, ListAppsFilter]): Filter to see apps with certain statuses.
        environment (Union[Unset, str]): The environment to filter the apps by. If not provided,
            apps for all environments will be returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListAppsResponse
    """

    return sync_detailed(
        client=client,
        query=query,
        page=page,
        page_size=page_size,
        num_runs=num_runs,
        sort=sort,
        filter_=filter_,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    query: Union[Unset, str] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
    num_runs: Union[Unset, int] = 20,
    sort: Union[Unset, ListAppsSort] = ListAppsSort.CREATED_AT,
    filter_: Union[Unset, ListAppsFilter] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Response[ListAppsResponse]:
    """List apps

     Get all the apps for the current account.

    Args:
        query (Union[Unset, str]): The search query to filter apps by.
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.
        num_runs (Union[Unset, int]): Number of recent runs to fetch (-1 for all runs, defaults to
            20) Default: 20.
        sort (Union[Unset, ListAppsSort]): Sort order for the results. Default:
            ListAppsSort.CREATED_AT.
        filter_ (Union[Unset, ListAppsFilter]): Filter to see apps with certain statuses.
        environment (Union[Unset, str]): The environment to filter the apps by. If not provided,
            apps for all environments will be returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListAppsResponse]
    """

    kwargs = _get_kwargs(
        query=query,
        page=page,
        page_size=page_size,
        num_runs=num_runs,
        sort=sort,
        filter_=filter_,
        environment=environment,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    query: Union[Unset, str] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
    num_runs: Union[Unset, int] = 20,
    sort: Union[Unset, ListAppsSort] = ListAppsSort.CREATED_AT,
    filter_: Union[Unset, ListAppsFilter] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Optional[ListAppsResponse]:
    """List apps

     Get all the apps for the current account.

    Args:
        query (Union[Unset, str]): The search query to filter apps by.
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.
        num_runs (Union[Unset, int]): Number of recent runs to fetch (-1 for all runs, defaults to
            20) Default: 20.
        sort (Union[Unset, ListAppsSort]): Sort order for the results. Default:
            ListAppsSort.CREATED_AT.
        filter_ (Union[Unset, ListAppsFilter]): Filter to see apps with certain statuses.
        environment (Union[Unset, str]): The environment to filter the apps by. If not provided,
            apps for all environments will be returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListAppsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            query=query,
            page=page,
            page_size=page_size,
            num_runs=num_runs,
            sort=sort,
            filter_=filter_,
            environment=environment,
        )
    ).parsed
