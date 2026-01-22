import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.list_alerts_response import ListAlertsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    alert_type: str | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    acked: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["page"] = page

    params["page_size"] = page_size

    params["alert_type"] = alert_type

    json_start_at: str | Unset = UNSET
    if not isinstance(start_at, Unset):
        json_start_at = start_at.isoformat()
    params["start_at"] = json_start_at

    json_end_at: str | Unset = UNSET
    if not isinstance(end_at, Unset):
        json_end_at = end_at.isoformat()
    params["end_at"] = json_end_at

    params["acked"] = acked

    params["environment"] = environment

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/alerts",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | ListAlertsResponse:
    if response.status_code == 200:
        response_200 = ListAlertsResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | ListAlertsResponse]:
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
    alert_type: str | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    acked: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> Response[ErrorModel | ListAlertsResponse]:
    """List alerts

     List alerts for the current account with optional filtering

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        alert_type (str | Unset): Filter alerts by alert type
        start_at (datetime.datetime | Unset): Filter alerts created after or at this datetime
            (inclusive)
        end_at (datetime.datetime | Unset): Filter alerts created before or at this datetime
            (inclusive)
        acked (str | Unset): Filter alerts by acknowledged status.
        environment (str | Unset): Filter alerts by environment (e.g., production, staging)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | ListAlertsResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        page_size=page_size,
        alert_type=alert_type,
        start_at=start_at,
        end_at=end_at,
        acked=acked,
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
    alert_type: str | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    acked: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> ErrorModel | ListAlertsResponse | None:
    """List alerts

     List alerts for the current account with optional filtering

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        alert_type (str | Unset): Filter alerts by alert type
        start_at (datetime.datetime | Unset): Filter alerts created after or at this datetime
            (inclusive)
        end_at (datetime.datetime | Unset): Filter alerts created before or at this datetime
            (inclusive)
        acked (str | Unset): Filter alerts by acknowledged status.
        environment (str | Unset): Filter alerts by environment (e.g., production, staging)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | ListAlertsResponse
    """

    return sync_detailed(
        client=client,
        page=page,
        page_size=page_size,
        alert_type=alert_type,
        start_at=start_at,
        end_at=end_at,
        acked=acked,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    alert_type: str | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    acked: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> Response[ErrorModel | ListAlertsResponse]:
    """List alerts

     List alerts for the current account with optional filtering

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        alert_type (str | Unset): Filter alerts by alert type
        start_at (datetime.datetime | Unset): Filter alerts created after or at this datetime
            (inclusive)
        end_at (datetime.datetime | Unset): Filter alerts created before or at this datetime
            (inclusive)
        acked (str | Unset): Filter alerts by acknowledged status.
        environment (str | Unset): Filter alerts by environment (e.g., production, staging)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | ListAlertsResponse]
    """

    kwargs = _get_kwargs(
        page=page,
        page_size=page_size,
        alert_type=alert_type,
        start_at=start_at,
        end_at=end_at,
        acked=acked,
        environment=environment,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    page: int | Unset = 1,
    page_size: int | Unset = 20,
    alert_type: str | Unset = UNSET,
    start_at: datetime.datetime | Unset = UNSET,
    end_at: datetime.datetime | Unset = UNSET,
    acked: str | Unset = UNSET,
    environment: str | Unset = UNSET,
) -> ErrorModel | ListAlertsResponse | None:
    """List alerts

     List alerts for the current account with optional filtering

    Args:
        page (int | Unset): The page number to fetch. Default: 1.
        page_size (int | Unset): The number of records to fetch on each page. Default: 20.
        alert_type (str | Unset): Filter alerts by alert type
        start_at (datetime.datetime | Unset): Filter alerts created after or at this datetime
            (inclusive)
        end_at (datetime.datetime | Unset): Filter alerts created before or at this datetime
            (inclusive)
        acked (str | Unset): Filter alerts by acknowledged status.
        environment (str | Unset): Filter alerts by environment (e.g., production, staging)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | ListAlertsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            page_size=page_size,
            alert_type=alert_type,
            start_at=start_at,
            end_at=end_at,
            acked=acked,
            environment=environment,
        )
    ).parsed
