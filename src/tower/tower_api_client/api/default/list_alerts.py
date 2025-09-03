import datetime
from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_alerts_response import ListAlertsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    alert_type: Union[Unset, str] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
    acked: Union[Unset, str] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["alert_type"] = alert_type

    json_start_at: Union[Unset, str] = UNSET
    if not isinstance(start_at, Unset):
        json_start_at = start_at.isoformat()
    params["start_at"] = json_start_at

    json_end_at: Union[Unset, str] = UNSET
    if not isinstance(end_at, Unset):
        json_end_at = end_at.isoformat()
    params["end_at"] = json_end_at

    params["page"] = page

    params["page_size"] = page_size

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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[ListAlertsResponse]:
    if response.status_code == 200:
        response_200 = ListAlertsResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[ListAlertsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    alert_type: Union[Unset, str] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
    acked: Union[Unset, str] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Response[ListAlertsResponse]:
    """List alerts

     List alerts for the current account with optional filtering

    Args:
        alert_type (Union[Unset, str]): Filter alerts by alert type
        start_at (Union[Unset, datetime.datetime]): Filter alerts created after or at this
            datetime (inclusive)
        end_at (Union[Unset, datetime.datetime]): Filter alerts created before or at this datetime
            (inclusive)
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.
        acked (Union[Unset, str]): Filter alerts by acknowledged status.
        environment (Union[Unset, str]): Filter alerts by environment (e.g., production, staging)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListAlertsResponse]
    """

    kwargs = _get_kwargs(
        alert_type=alert_type,
        start_at=start_at,
        end_at=end_at,
        page=page,
        page_size=page_size,
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
    alert_type: Union[Unset, str] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
    acked: Union[Unset, str] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Optional[ListAlertsResponse]:
    """List alerts

     List alerts for the current account with optional filtering

    Args:
        alert_type (Union[Unset, str]): Filter alerts by alert type
        start_at (Union[Unset, datetime.datetime]): Filter alerts created after or at this
            datetime (inclusive)
        end_at (Union[Unset, datetime.datetime]): Filter alerts created before or at this datetime
            (inclusive)
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.
        acked (Union[Unset, str]): Filter alerts by acknowledged status.
        environment (Union[Unset, str]): Filter alerts by environment (e.g., production, staging)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListAlertsResponse
    """

    return sync_detailed(
        client=client,
        alert_type=alert_type,
        start_at=start_at,
        end_at=end_at,
        page=page,
        page_size=page_size,
        acked=acked,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    alert_type: Union[Unset, str] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
    acked: Union[Unset, str] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Response[ListAlertsResponse]:
    """List alerts

     List alerts for the current account with optional filtering

    Args:
        alert_type (Union[Unset, str]): Filter alerts by alert type
        start_at (Union[Unset, datetime.datetime]): Filter alerts created after or at this
            datetime (inclusive)
        end_at (Union[Unset, datetime.datetime]): Filter alerts created before or at this datetime
            (inclusive)
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.
        acked (Union[Unset, str]): Filter alerts by acknowledged status.
        environment (Union[Unset, str]): Filter alerts by environment (e.g., production, staging)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListAlertsResponse]
    """

    kwargs = _get_kwargs(
        alert_type=alert_type,
        start_at=start_at,
        end_at=end_at,
        page=page,
        page_size=page_size,
        acked=acked,
        environment=environment,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    alert_type: Union[Unset, str] = UNSET,
    start_at: Union[Unset, datetime.datetime] = UNSET,
    end_at: Union[Unset, datetime.datetime] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
    acked: Union[Unset, str] = UNSET,
    environment: Union[Unset, str] = UNSET,
) -> Optional[ListAlertsResponse]:
    """List alerts

     List alerts for the current account with optional filtering

    Args:
        alert_type (Union[Unset, str]): Filter alerts by alert type
        start_at (Union[Unset, datetime.datetime]): Filter alerts created after or at this
            datetime (inclusive)
        end_at (Union[Unset, datetime.datetime]): Filter alerts created before or at this datetime
            (inclusive)
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.
        acked (Union[Unset, str]): Filter alerts by acknowledged status.
        environment (Union[Unset, str]): Filter alerts by environment (e.g., production, staging)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListAlertsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            alert_type=alert_type,
            start_at=start_at,
            end_at=end_at,
            page=page,
            page_size=page_size,
            acked=acked,
            environment=environment,
        )
    ).parsed
