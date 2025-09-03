from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.stream_run_logs_event_log import StreamRunLogsEventLog
from ...models.stream_run_logs_event_warning import StreamRunLogsEventWarning
from ...types import Response


def _get_kwargs(
    name: str,
    seq: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{name}/runs/{seq}/logs/stream".format(
            name=name,
            seq=seq,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[list[Union["StreamRunLogsEventLog", "StreamRunLogsEventWarning"]]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.text
        for response_200_item_data in _response_200:

            def _parse_response_200_item(
                data: object,
            ) -> Union["StreamRunLogsEventLog", "StreamRunLogsEventWarning"]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    response_200_item_type_0 = StreamRunLogsEventLog.from_dict(data)

                    return response_200_item_type_0
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_item_type_1 = StreamRunLogsEventWarning.from_dict(data)

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
) -> Response[list[Union["StreamRunLogsEventLog", "StreamRunLogsEventWarning"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Response[list[Union["StreamRunLogsEventLog", "StreamRunLogsEventWarning"]]]:
    """Stream run logs

     Streams the logs associated with a particular run of an app in real-time.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[Union['StreamRunLogsEventLog', 'StreamRunLogsEventWarning']]]
    """

    kwargs = _get_kwargs(
        name=name,
        seq=seq,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Optional[list[Union["StreamRunLogsEventLog", "StreamRunLogsEventWarning"]]]:
    """Stream run logs

     Streams the logs associated with a particular run of an app in real-time.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[Union['StreamRunLogsEventLog', 'StreamRunLogsEventWarning']]
    """

    return sync_detailed(
        name=name,
        seq=seq,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Response[list[Union["StreamRunLogsEventLog", "StreamRunLogsEventWarning"]]]:
    """Stream run logs

     Streams the logs associated with a particular run of an app in real-time.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[Union['StreamRunLogsEventLog', 'StreamRunLogsEventWarning']]]
    """

    kwargs = _get_kwargs(
        name=name,
        seq=seq,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Optional[list[Union["StreamRunLogsEventLog", "StreamRunLogsEventWarning"]]]:
    """Stream run logs

     Streams the logs associated with a particular run of an app in real-time.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[Union['StreamRunLogsEventLog', 'StreamRunLogsEventWarning']]
    """

    return (
        await asyncio_detailed(
            name=name,
            seq=seq,
            client=client,
        )
    ).parsed
