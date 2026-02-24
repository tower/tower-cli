from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.list_apps_filter import ListAppsFilter
from ...models.list_apps_response import ListAppsResponse
from ...models.list_apps_sort import ListAppsSort
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    query: str | Unset = UNSET,
    num_runs: int | Unset = 20,
    sort: ListAppsSort | Unset = ListAppsSort.CREATED_AT,
    filter_: ListAppsFilter | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["page"] = page

    params["page_size"] = page_size

    params["query"] = query

    params["num_runs"] = num_runs

    json_sort: str | Unset = UNSET
    if not isinstance(sort, Unset):
        json_sort = sort.value

    params["sort"] = json_sort

    json_filter_: str | Unset = UNSET
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
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | ListAppsResponse:
    if response.status_code == 200:
        response_200 = ListAppsResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | ListAppsResponse]:
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
    query: str | Unset = UNSET,
    num_runs: int | Unset = 20,
    sort: ListAppsSort | Unset = ListAppsSort.CREATED_AT,
    filter_: ListAppsFilter | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> Response[ErrorModel | ListAppsResponse]:
    """List apps

     Get all the apps for the current account.

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        query (str | Unset): The search query to filter apps by.
        num_runs (int | Unset): Number of recent runs to fetch (-1 for all runs, defaults to 20)
            Default: 20.
        sort (ListAppsSort | Unset): Sort order for the results. Default: ListAppsSort.CREATED_AT.
        filter_ (ListAppsFilter | Unset): Filter to see apps with certain statuses.
        environment (str | Unset): The environment to filter the apps by. If not provided, apps
            for all environments will be returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | ListAppsResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        page_size=page_size,
        query=query,
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
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    query: str | Unset = UNSET,
    num_runs: int | Unset = 20,
    sort: ListAppsSort | Unset = ListAppsSort.CREATED_AT,
    filter_: ListAppsFilter | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> ErrorModel | ListAppsResponse | None:
    """List apps

     Get all the apps for the current account.

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        query (str | Unset): The search query to filter apps by.
        num_runs (int | Unset): Number of recent runs to fetch (-1 for all runs, defaults to 20)
            Default: 20.
        sort (ListAppsSort | Unset): Sort order for the results. Default: ListAppsSort.CREATED_AT.
        filter_ (ListAppsFilter | Unset): Filter to see apps with certain statuses.
        environment (str | Unset): The environment to filter the apps by. If not provided, apps
            for all environments will be returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | ListAppsResponse
    """

    return sync_detailed(
        client=client,
        page=page,
        page_size=page_size,
        query=query,
        num_runs=num_runs,
        sort=sort,
        filter_=filter_,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    query: str | Unset = UNSET,
    num_runs: int | Unset = 20,
    sort: ListAppsSort | Unset = ListAppsSort.CREATED_AT,
    filter_: ListAppsFilter | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> Response[ErrorModel | ListAppsResponse]:
    """List apps

     Get all the apps for the current account.

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        query (str | Unset): The search query to filter apps by.
        num_runs (int | Unset): Number of recent runs to fetch (-1 for all runs, defaults to 20)
            Default: 20.
        sort (ListAppsSort | Unset): Sort order for the results. Default: ListAppsSort.CREATED_AT.
        filter_ (ListAppsFilter | Unset): Filter to see apps with certain statuses.
        environment (str | Unset): The environment to filter the apps by. If not provided, apps
            for all environments will be returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | ListAppsResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        page_size=page_size,
        query=query,
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
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    query: str | Unset = UNSET,
    num_runs: int | Unset = 20,
    sort: ListAppsSort | Unset = ListAppsSort.CREATED_AT,
    filter_: ListAppsFilter | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> ErrorModel | ListAppsResponse | None:
    """List apps

     Get all the apps for the current account.

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        query (str | Unset): The search query to filter apps by.
        num_runs (int | Unset): Number of recent runs to fetch (-1 for all runs, defaults to 20)
            Default: 20.
        sort (ListAppsSort | Unset): Sort order for the results. Default: ListAppsSort.CREATED_AT.
        filter_ (ListAppsFilter | Unset): Filter to see apps with certain statuses.
        environment (str | Unset): The environment to filter the apps by. If not provided, apps
            for all environments will be returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | ListAppsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            page_size=page_size,
            query=query,
            num_runs=num_runs,
            sort=sort,
            filter_=filter_,
            environment=environment,
        )
    ).parsed
