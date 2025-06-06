from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.acknowledge_alert_response import AcknowledgeAlertResponse
from ...types import Response


def _get_kwargs(
    alert_seq: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/alerts/{alert_seq}/acknowledge".format(
            alert_seq=alert_seq,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[AcknowledgeAlertResponse]:
    if response.status_code == 200:
        response_200 = AcknowledgeAlertResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[AcknowledgeAlertResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    alert_seq: int,
    *,
    client: AuthenticatedClient,
) -> Response[AcknowledgeAlertResponse]:
    """Acknowledge alert

     Mark an alert as acknowledged

    Args:
        alert_seq (int): Seq of the alert to acknowledge

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AcknowledgeAlertResponse]
    """

    kwargs = _get_kwargs(
        alert_seq=alert_seq,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    alert_seq: int,
    *,
    client: AuthenticatedClient,
) -> Optional[AcknowledgeAlertResponse]:
    """Acknowledge alert

     Mark an alert as acknowledged

    Args:
        alert_seq (int): Seq of the alert to acknowledge

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AcknowledgeAlertResponse
    """

    return sync_detailed(
        alert_seq=alert_seq,
        client=client,
    ).parsed


async def asyncio_detailed(
    alert_seq: int,
    *,
    client: AuthenticatedClient,
) -> Response[AcknowledgeAlertResponse]:
    """Acknowledge alert

     Mark an alert as acknowledged

    Args:
        alert_seq (int): Seq of the alert to acknowledge

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AcknowledgeAlertResponse]
    """

    kwargs = _get_kwargs(
        alert_seq=alert_seq,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    alert_seq: int,
    *,
    client: AuthenticatedClient,
) -> Optional[AcknowledgeAlertResponse]:
    """Acknowledge alert

     Mark an alert as acknowledged

    Args:
        alert_seq (int): Seq of the alert to acknowledge

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AcknowledgeAlertResponse
    """

    return (
        await asyncio_detailed(
            alert_seq=alert_seq,
            client=client,
        )
    ).parsed
