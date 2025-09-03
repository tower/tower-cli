from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.stream_alerts_event_error import StreamAlertsEventError
from ...models.stream_alerts_event_run_failure_alert import (
    StreamAlertsEventRunFailureAlert,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/alerts/stream",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    list[Union["StreamAlertsEventError", "StreamAlertsEventRunFailureAlert"]]
]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.text
        for response_200_item_data in _response_200:

            def _parse_response_200_item(
                data: object,
            ) -> Union["StreamAlertsEventError", "StreamAlertsEventRunFailureAlert"]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    response_200_item_type_0 = StreamAlertsEventError.from_dict(data)

                    return response_200_item_type_0
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_item_type_1 = StreamAlertsEventRunFailureAlert.from_dict(
                    data
                )

                return response_200_item_type_1

            response_200_item = _parse_response_200_item(response_200_item_data)

            response_200.append(response_200_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    list[Union["StreamAlertsEventError", "StreamAlertsEventRunFailureAlert"]]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[
    list[Union["StreamAlertsEventError", "StreamAlertsEventRunFailureAlert"]]
]:
    """Stream alert notifications

     Streams alert notifications in real-time

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[Union['StreamAlertsEventError', 'StreamAlertsEventRunFailureAlert']]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
) -> Optional[
    list[Union["StreamAlertsEventError", "StreamAlertsEventRunFailureAlert"]]
]:
    """Stream alert notifications

     Streams alert notifications in real-time

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[Union['StreamAlertsEventError', 'StreamAlertsEventRunFailureAlert']]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[
    list[Union["StreamAlertsEventError", "StreamAlertsEventRunFailureAlert"]]
]:
    """Stream alert notifications

     Streams alert notifications in real-time

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[Union['StreamAlertsEventError', 'StreamAlertsEventRunFailureAlert']]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
) -> Optional[
    list[Union["StreamAlertsEventError", "StreamAlertsEventRunFailureAlert"]]
]:
    """Stream alert notifications

     Streams alert notifications in real-time

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[Union['StreamAlertsEventError', 'StreamAlertsEventRunFailureAlert']]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
