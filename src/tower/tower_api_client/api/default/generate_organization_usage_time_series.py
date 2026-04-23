from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.generate_organization_usage_time_series_response import (
    GenerateOrganizationUsageTimeSeriesResponse,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/usage/time-series",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | GenerateOrganizationUsageTimeSeriesResponse:
    if response.status_code == 200:
        response_200 = GenerateOrganizationUsageTimeSeriesResponse.from_dict(
            response.json()
        )

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | GenerateOrganizationUsageTimeSeriesResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[ErrorModel | GenerateOrganizationUsageTimeSeriesResponse]:
    """Get organization usage as time series

     Get the current billing cycle usage as a time series.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | GenerateOrganizationUsageTimeSeriesResponse]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
) -> ErrorModel | GenerateOrganizationUsageTimeSeriesResponse | None:
    """Get organization usage as time series

     Get the current billing cycle usage as a time series.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | GenerateOrganizationUsageTimeSeriesResponse
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[ErrorModel | GenerateOrganizationUsageTimeSeriesResponse]:
    """Get organization usage as time series

     Get the current billing cycle usage as a time series.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | GenerateOrganizationUsageTimeSeriesResponse]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
) -> ErrorModel | GenerateOrganizationUsageTimeSeriesResponse | None:
    """Get organization usage as time series

     Get the current billing cycle usage as a time series.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | GenerateOrganizationUsageTimeSeriesResponse
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
