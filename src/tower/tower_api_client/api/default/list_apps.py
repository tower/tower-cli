from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.list_apps_response import ListAppsResponse
from ...models.list_apps_status_item import ListAppsStatusItem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    query: Union[Unset, None, str] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
    period: Union[Unset, None, str] = UNSET,
    num_runs: Union[Unset, None, int] = 20,
    status: Union[Unset, None, List[ListAppsStatusItem]] = UNSET,
) -> Dict[str, Any]:
    url = "{}/apps".format(client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    params: Dict[str, Any] = {}
    params["query"] = query

    params["page"] = page

    params["page_size"] = page_size

    params["period"] = period

    params["num_runs"] = num_runs

    json_status: Union[Unset, None, List[str]] = UNSET
    if not isinstance(status, Unset):
        if status is None:
            json_status = None
        else:
            json_status = []
            for status_item_data in status:
                status_item = status_item_data.value

                json_status.append(status_item)

    params["status"] = json_status

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(*, response: httpx.Response) -> Optional[ListAppsResponse]:
    if response.status_code == 200:
        response_200 = ListAppsResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[ListAppsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    query: Union[Unset, None, str] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
    period: Union[Unset, None, str] = UNSET,
    num_runs: Union[Unset, None, int] = 20,
    status: Union[Unset, None, List[ListAppsStatusItem]] = UNSET,
) -> Response[ListAppsResponse]:
    """List apps

     Get all the apps for the current account.

    Args:
        query (Union[Unset, None, str]): The search query to filter apps by.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.
        period (Union[Unset, None, str]): Time period for statistics (24h, 7d, 30d, or none)
        num_runs (Union[Unset, None, int]): Number of recent runs to fetch (-1 for all runs,
            defaults to 20) Default: 20.
        status (Union[Unset, None, List[ListAppsStatusItem]]): Filter apps by status(es) (comma
            separated for multiple). Valid values: active, failed, disabled etc.

    Returns:
        Response[ListAppsResponse]
    """

    kwargs = _get_kwargs(
        client=client,
        query=query,
        page=page,
        page_size=page_size,
        period=period,
        num_runs=num_runs,
        status=status,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: AuthenticatedClient,
    query: Union[Unset, None, str] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
    period: Union[Unset, None, str] = UNSET,
    num_runs: Union[Unset, None, int] = 20,
    status: Union[Unset, None, List[ListAppsStatusItem]] = UNSET,
) -> Optional[ListAppsResponse]:
    """List apps

     Get all the apps for the current account.

    Args:
        query (Union[Unset, None, str]): The search query to filter apps by.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.
        period (Union[Unset, None, str]): Time period for statistics (24h, 7d, 30d, or none)
        num_runs (Union[Unset, None, int]): Number of recent runs to fetch (-1 for all runs,
            defaults to 20) Default: 20.
        status (Union[Unset, None, List[ListAppsStatusItem]]): Filter apps by status(es) (comma
            separated for multiple). Valid values: active, failed, disabled etc.

    Returns:
        Response[ListAppsResponse]
    """

    return sync_detailed(
        client=client,
        query=query,
        page=page,
        page_size=page_size,
        period=period,
        num_runs=num_runs,
        status=status,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    query: Union[Unset, None, str] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
    period: Union[Unset, None, str] = UNSET,
    num_runs: Union[Unset, None, int] = 20,
    status: Union[Unset, None, List[ListAppsStatusItem]] = UNSET,
) -> Response[ListAppsResponse]:
    """List apps

     Get all the apps for the current account.

    Args:
        query (Union[Unset, None, str]): The search query to filter apps by.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.
        period (Union[Unset, None, str]): Time period for statistics (24h, 7d, 30d, or none)
        num_runs (Union[Unset, None, int]): Number of recent runs to fetch (-1 for all runs,
            defaults to 20) Default: 20.
        status (Union[Unset, None, List[ListAppsStatusItem]]): Filter apps by status(es) (comma
            separated for multiple). Valid values: active, failed, disabled etc.

    Returns:
        Response[ListAppsResponse]
    """

    kwargs = _get_kwargs(
        client=client,
        query=query,
        page=page,
        page_size=page_size,
        period=period,
        num_runs=num_runs,
        status=status,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    query: Union[Unset, None, str] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
    period: Union[Unset, None, str] = UNSET,
    num_runs: Union[Unset, None, int] = 20,
    status: Union[Unset, None, List[ListAppsStatusItem]] = UNSET,
) -> Optional[ListAppsResponse]:
    """List apps

     Get all the apps for the current account.

    Args:
        query (Union[Unset, None, str]): The search query to filter apps by.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.
        period (Union[Unset, None, str]): Time period for statistics (24h, 7d, 30d, or none)
        num_runs (Union[Unset, None, int]): Number of recent runs to fetch (-1 for all runs,
            defaults to 20) Default: 20.
        status (Union[Unset, None, List[ListAppsStatusItem]]): Filter apps by status(es) (comma
            separated for multiple). Valid values: active, failed, disabled etc.

    Returns:
        Response[ListAppsResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            query=query,
            page=page,
            page_size=page_size,
            period=period,
            num_runs=num_runs,
            status=status,
        )
    ).parsed
