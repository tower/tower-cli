from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.stream_shouldertaps_event_shouldertap import (
    StreamShouldertapsEventShouldertap,
)
from ...models.stream_shouldertaps_event_warning import StreamShouldertapsEventWarning
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/shouldertaps/stream",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    ErrorModel
    | list[StreamShouldertapsEventShouldertap | StreamShouldertapsEventWarning]
):
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.text
        for response_200_item_data in _response_200:

            def _parse_response_200_item(
                data: object,
            ) -> StreamShouldertapsEventShouldertap | StreamShouldertapsEventWarning:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    response_200_item_event_shouldertap = (
                        StreamShouldertapsEventShouldertap.from_dict(data)
                    )

                    return response_200_item_event_shouldertap
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_item_event_warning = (
                    StreamShouldertapsEventWarning.from_dict(data)
                )

                return response_200_item_event_warning

            response_200_item = _parse_response_200_item(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ErrorModel
    | list[StreamShouldertapsEventShouldertap | StreamShouldertapsEventWarning]
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
    ErrorModel
    | list[StreamShouldertapsEventShouldertap | StreamShouldertapsEventWarning]
]:
    """Stream shouldertaps

     Stream events over SSE that notify you of potential data staleness

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | list[StreamShouldertapsEventShouldertap | StreamShouldertapsEventWarning]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
) -> (
    ErrorModel
    | list[StreamShouldertapsEventShouldertap | StreamShouldertapsEventWarning]
    | None
):
    """Stream shouldertaps

     Stream events over SSE that notify you of potential data staleness

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | list[StreamShouldertapsEventShouldertap | StreamShouldertapsEventWarning]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
) -> Response[
    ErrorModel
    | list[StreamShouldertapsEventShouldertap | StreamShouldertapsEventWarning]
]:
    """Stream shouldertaps

     Stream events over SSE that notify you of potential data staleness

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | list[StreamShouldertapsEventShouldertap | StreamShouldertapsEventWarning]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
) -> (
    ErrorModel
    | list[StreamShouldertapsEventShouldertap | StreamShouldertapsEventWarning]
    | None
):
    """Stream shouldertaps

     Stream events over SSE that notify you of potential data staleness

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | list[StreamShouldertapsEventShouldertap | StreamShouldertapsEventWarning]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
