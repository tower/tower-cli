from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.list_runs_response import ListRunsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    client: AuthenticatedClient,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Dict[str, Any]:
    url = "{}/apps/{name}/runs".format(client.base_url, name=name)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    params: Dict[str, Any] = {}
    params["page"] = page

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(*, response: httpx.Response) -> Optional[ListRunsResponse]:
    if response.status_code == 200:
        response_200 = ListRunsResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[ListRunsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Response[ListRunsResponse]:
    """List runs

     Generates a list of all the runs for a given app. The list is paginated based on the query string
    parameters passed in.

    Args:
        name (str): The name of the app to fetch runs for.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.

    Returns:
        Response[ListRunsResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        client=client,
        page=page,
        page_size=page_size,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Optional[ListRunsResponse]:
    """List runs

     Generates a list of all the runs for a given app. The list is paginated based on the query string
    parameters passed in.

    Args:
        name (str): The name of the app to fetch runs for.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.

    Returns:
        Response[ListRunsResponse]
    """

    return sync_detailed(
        name=name,
        client=client,
        page=page,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Response[ListRunsResponse]:
    """List runs

     Generates a list of all the runs for a given app. The list is paginated based on the query string
    parameters passed in.

    Args:
        name (str): The name of the app to fetch runs for.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.

    Returns:
        Response[ListRunsResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        client=client,
        page=page,
        page_size=page_size,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Optional[ListRunsResponse]:
    """List runs

     Generates a list of all the runs for a given app. The list is paginated based on the query string
    parameters passed in.

    Args:
        name (str): The name of the app to fetch runs for.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.

    Returns:
        Response[ListRunsResponse]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            page=page,
            page_size=page_size,
        )
    ).parsed
