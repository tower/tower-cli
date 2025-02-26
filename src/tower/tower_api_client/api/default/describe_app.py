from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.describe_app_response import DescribeAppResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    client: AuthenticatedClient,
    runs: Union[Unset, None, int] = UNSET,
) -> Dict[str, Any]:
    url = "{}/apps/{name}".format(client.base_url, name=name)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    params: Dict[str, Any] = {}
    params["runs"] = runs

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(*, response: httpx.Response) -> Optional[DescribeAppResponse]:
    if response.status_code == 200:
        response_200 = DescribeAppResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[DescribeAppResponse]:
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
    runs: Union[Unset, None, int] = UNSET,
) -> Response[DescribeAppResponse]:
    """Describe app

     Get all the runs for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (Union[Unset, None, int]): The number of recent runs to fetch for the app.

    Returns:
        Response[DescribeAppResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        client=client,
        runs=runs,
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
    runs: Union[Unset, None, int] = UNSET,
) -> Optional[DescribeAppResponse]:
    """Describe app

     Get all the runs for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (Union[Unset, None, int]): The number of recent runs to fetch for the app.

    Returns:
        Response[DescribeAppResponse]
    """

    return sync_detailed(
        name=name,
        client=client,
        runs=runs,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    runs: Union[Unset, None, int] = UNSET,
) -> Response[DescribeAppResponse]:
    """Describe app

     Get all the runs for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (Union[Unset, None, int]): The number of recent runs to fetch for the app.

    Returns:
        Response[DescribeAppResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        client=client,
        runs=runs,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
    runs: Union[Unset, None, int] = UNSET,
) -> Optional[DescribeAppResponse]:
    """Describe app

     Get all the runs for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (Union[Unset, None, int]): The number of recent runs to fetch for the app.

    Returns:
        Response[DescribeAppResponse]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            runs=runs,
        )
    ).parsed
