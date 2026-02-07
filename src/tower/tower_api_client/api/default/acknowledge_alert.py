from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.acknowledge_alert_response import AcknowledgeAlertResponse
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs(
    alert_seq: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/alerts/{alert_seq}/acknowledge".format(
            alert_seq=quote(str(alert_seq), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AcknowledgeAlertResponse | ErrorModel:
    if response.status_code == 200:
        response_200 = AcknowledgeAlertResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[AcknowledgeAlertResponse | ErrorModel]:
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
) -> Response[AcknowledgeAlertResponse | ErrorModel]:
    """Acknowledge alert

     Mark an alert as acknowledged

    Args:
        alert_seq (int): Seq of the alert to acknowledge

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AcknowledgeAlertResponse | ErrorModel]
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
) -> AcknowledgeAlertResponse | ErrorModel | None:
    """Acknowledge alert

     Mark an alert as acknowledged

    Args:
        alert_seq (int): Seq of the alert to acknowledge

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AcknowledgeAlertResponse | ErrorModel
    """

    return sync_detailed(
        alert_seq=alert_seq,
        client=client,
    ).parsed


async def asyncio_detailed(
    alert_seq: int,
    *,
    client: AuthenticatedClient,
) -> Response[AcknowledgeAlertResponse | ErrorModel]:
    """Acknowledge alert

     Mark an alert as acknowledged

    Args:
        alert_seq (int): Seq of the alert to acknowledge

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AcknowledgeAlertResponse | ErrorModel]
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
) -> AcknowledgeAlertResponse | ErrorModel | None:
    """Acknowledge alert

     Mark an alert as acknowledged

    Args:
        alert_seq (int): Seq of the alert to acknowledge

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AcknowledgeAlertResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            alert_seq=alert_seq,
            client=client,
        )
    ).parsed
