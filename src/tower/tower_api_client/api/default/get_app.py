from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_app_output_body import GetAppOutputBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    runs: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["runs"] = runs

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{name}".format(
            name=name,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GetAppOutputBody]:
    if response.status_code == 200:
        response_200 = GetAppOutputBody.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GetAppOutputBody]:
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
    runs: Union[Unset, int] = UNSET,
) -> Response[GetAppOutputBody]:
    """Get all the apps for the current account.

     Get all the apps for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (Union[Unset, int]): The number of recent runs to fetch for the app.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAppOutputBody]
    """

    kwargs = _get_kwargs(
        name=name,
        runs=runs,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient,
    runs: Union[Unset, int] = UNSET,
) -> Optional[GetAppOutputBody]:
    """Get all the apps for the current account.

     Get all the apps for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (Union[Unset, int]): The number of recent runs to fetch for the app.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAppOutputBody
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
    runs: Union[Unset, int] = UNSET,
) -> Response[GetAppOutputBody]:
    """Get all the apps for the current account.

     Get all the apps for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (Union[Unset, int]): The number of recent runs to fetch for the app.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAppOutputBody]
    """

    kwargs = _get_kwargs(
        name=name,
        runs=runs,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
    runs: Union[Unset, int] = UNSET,
) -> Optional[GetAppOutputBody]:
    """Get all the apps for the current account.

     Get all the apps for the current account.

    Args:
        name (str): The name of the app to fetch.
        runs (Union[Unset, int]): The number of recent runs to fetch for the app.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAppOutputBody
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            runs=runs,
        )
    ).parsed
