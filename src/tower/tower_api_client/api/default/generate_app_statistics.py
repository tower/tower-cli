from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.generate_app_statistics_response import GenerateAppStatisticsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    environment: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["environment"] = environment

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/stats/apps",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GenerateAppStatisticsResponse]:
    if response.status_code == 200:
        response_200 = GenerateAppStatisticsResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GenerateAppStatisticsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, str] = UNSET,
) -> Response[GenerateAppStatisticsResponse]:
    """Generate app statistics

     Generates current statistics about apps

    Args:
        environment (Union[Unset, str]): The environment to filter the statistics by. If not
            provided, statistics for all environments will be returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GenerateAppStatisticsResponse]
    """

    kwargs = _get_kwargs(
        environment=environment,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, str] = UNSET,
) -> Optional[GenerateAppStatisticsResponse]:
    """Generate app statistics

     Generates current statistics about apps

    Args:
        environment (Union[Unset, str]): The environment to filter the statistics by. If not
            provided, statistics for all environments will be returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GenerateAppStatisticsResponse
    """

    return sync_detailed(
        client=client,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, str] = UNSET,
) -> Response[GenerateAppStatisticsResponse]:
    """Generate app statistics

     Generates current statistics about apps

    Args:
        environment (Union[Unset, str]): The environment to filter the statistics by. If not
            provided, statistics for all environments will be returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GenerateAppStatisticsResponse]
    """

    kwargs = _get_kwargs(
        environment=environment,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, str] = UNSET,
) -> Optional[GenerateAppStatisticsResponse]:
    """Generate app statistics

     Generates current statistics about apps

    Args:
        environment (Union[Unset, str]): The environment to filter the statistics by. If not
            provided, statistics for all environments will be returned.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GenerateAppStatisticsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            environment=environment,
        )
    ).parsed
