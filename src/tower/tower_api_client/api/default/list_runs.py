import datetime
from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_runs_response import ListRunsResponse
from ...models.list_runs_status_item import ListRunsStatusItem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 20,
    status: Union[Unset, list[ListRunsStatusItem]] = UNSET,
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
        "url": "/apps/{name}/runs".format(
            name=name,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[ListRunsResponse]:
    if response.status_code == 200:
        response_200 = ListRunsResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[ListRunsResponse]:
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
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 20,
    status: Union[Unset, list[ListRunsStatusItem]] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Response[ListRunsResponse]:
    """List runs

     Generates a list of all the runs for a given app. The list is paginated based on the query string
    parameters passed in.

    Args:
        name (str): The name of the app to fetch runs for.
        page (Union[Unset, int]): The page number to fetch. Default: 1.
        page_size (Union[Unset, int]): The number of records to fetch on each page. Default: 20.
        status (Union[Unset, list[ListRunsStatusItem]]): Filter runs by status(es) (comma
            separated for multiple).
        start_at (Union[Unset, datetime.datetime]): Filter runs scheduled after or at this
            datetime (inclusive)
        end_at (Union[Unset, datetime.datetime]): Filter runs scheduled before or at this datetime
            (inclusive)
        environment (Union[Unset, str]): Filter runs by environment. If not provided, all
            environments will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListRunsResponse]
    """

    kwargs = _get_kwargs(
        name=name,
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
    name: str,
    *,
    client: AuthenticatedClient,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 20,
    status: Union[Unset, list[ListRunsStatusItem]] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Optional[ListRunsResponse]:
    """List runs

     Generates a list of all the runs for a given app. The list is paginated based on the query string
    parameters passed in.

    Args:
        name (str): The name of the app to fetch runs for.
        page (Union[Unset, int]): The page number to fetch. Default: 1.
        page_size (Union[Unset, int]): The number of records to fetch on each page. Default: 20.
        status (Union[Unset, list[ListRunsStatusItem]]): Filter runs by status(es) (comma
            separated for multiple).
        start_at (Union[Unset, datetime.datetime]): Filter runs scheduled after or at this
            datetime (inclusive)
        end_at (Union[Unset, datetime.datetime]): Filter runs scheduled before or at this datetime
            (inclusive)
        environment (Union[Unset, str]): Filter runs by environment. If not provided, all
            environments will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListRunsResponse
    """

    return sync_detailed(
        name=name,
        client=client,
        page=page,
        page_size=page_size,
        status=status,
        start_at=start_at,
        end_at=end_at,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 20,
    status: Union[Unset, list[ListRunsStatusItem]] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Response[ListRunsResponse]:
    """List runs

     Generates a list of all the runs for a given app. The list is paginated based on the query string
    parameters passed in.

    Args:
        name (str): The name of the app to fetch runs for.
        page (Union[Unset, int]): The page number to fetch. Default: 1.
        page_size (Union[Unset, int]): The number of records to fetch on each page. Default: 20.
        status (Union[Unset, list[ListRunsStatusItem]]): Filter runs by status(es) (comma
            separated for multiple).
        start_at (Union[Unset, datetime.datetime]): Filter runs scheduled after or at this
            datetime (inclusive)
        end_at (Union[Unset, datetime.datetime]): Filter runs scheduled before or at this datetime
            (inclusive)
        environment (Union[Unset, str]): Filter runs by environment. If not provided, all
            environments will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListRunsResponse]
    """

    kwargs = _get_kwargs(
        name=name,
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
    name: str,
    *,
    client: AuthenticatedClient,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 20,
    status: Union[Unset, list[ListRunsStatusItem]] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Optional[ListRunsResponse]:
    """List runs

     Generates a list of all the runs for a given app. The list is paginated based on the query string
    parameters passed in.

    Args:
        name (str): The name of the app to fetch runs for.
        page (Union[Unset, int]): The page number to fetch. Default: 1.
        page_size (Union[Unset, int]): The number of records to fetch on each page. Default: 20.
        status (Union[Unset, list[ListRunsStatusItem]]): Filter runs by status(es) (comma
            separated for multiple).
        start_at (Union[Unset, datetime.datetime]): Filter runs scheduled after or at this
            datetime (inclusive)
        end_at (Union[Unset, datetime.datetime]): Filter runs scheduled before or at this datetime
            (inclusive)
        environment (Union[Unset, str]): Filter runs by environment. If not provided, all
            environments will be included.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListRunsResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            page=page,
            page_size=page_size,
            status=status,
            start_at=start_at,
            end_at=end_at,
            environment=environment,
        )
    ).parsed
