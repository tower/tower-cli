from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.describe_app_response import DescribeAppResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    slug: str,
    *,
    runs: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["runs"] = runs

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{slug}".format(
            slug=slug,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[DescribeAppResponse]:
    if response.status_code == 200:
        response_200 = DescribeAppResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[DescribeAppResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    slug: str,
    *,
    client: AuthenticatedClient,
    runs: Union[Unset, int] = UNSET,
) -> Response[DescribeAppResponse]:
    """Describe app

     Get all the runs for the current account.

    Args:
        slug (str): The slug of the app to fetch.
        runs (Union[Unset, int]): The number of recent runs to fetch for the app.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeAppResponse]
    """

    kwargs = _get_kwargs(
        slug=slug,
        runs=runs,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    slug: str,
    *,
    client: AuthenticatedClient,
    runs: Union[Unset, int] = UNSET,
) -> Optional[DescribeAppResponse]:
    """Describe app

     Get all the runs for the current account.

    Args:
        slug (str): The slug of the app to fetch.
        runs (Union[Unset, int]): The number of recent runs to fetch for the app.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeAppResponse
    """

    return sync_detailed(
        slug=slug,
        client=client,
        runs=runs,
    ).parsed


async def asyncio_detailed(
    slug: str,
    *,
    client: AuthenticatedClient,
    runs: Union[Unset, int] = UNSET,
) -> Response[DescribeAppResponse]:
    """Describe app

     Get all the runs for the current account.

    Args:
        slug (str): The slug of the app to fetch.
        runs (Union[Unset, int]): The number of recent runs to fetch for the app.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeAppResponse]
    """

    kwargs = _get_kwargs(
        slug=slug,
        runs=runs,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    slug: str,
    *,
    client: AuthenticatedClient,
    runs: Union[Unset, int] = UNSET,
) -> Optional[DescribeAppResponse]:
    """Describe app

     Get all the runs for the current account.

    Args:
        slug (str): The slug of the app to fetch.
        runs (Union[Unset, int]): The number of recent runs to fetch for the app.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeAppResponse
    """

    return (
        await asyncio_detailed(
            slug=slug,
            client=client,
            runs=runs,
        )
    ).parsed
