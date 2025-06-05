from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.log_line import LogLine
from ...models.sse_warning import SSEWarning
from ...types import Response


def _get_kwargs(
    slug: str,
    seq: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{slug}/runs/{seq}/logs/stream".format(
            slug=slug,
            seq=seq,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[list[Union["LogLine", "SSEWarning"]]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.text
        for response_200_item_data in _response_200:

            def _parse_response_200_item(
                data: object,
            ) -> Union["LogLine", "SSEWarning"]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    response_200_item_type_0 = LogLine.from_dict(data)

                    return response_200_item_type_0
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_item_type_1 = SSEWarning.from_dict(data)

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
) -> Response[list[Union["LogLine", "SSEWarning"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    slug: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Response[list[Union["LogLine", "SSEWarning"]]]:
    """Stream run logs

     Streams the logs associated with a particular run of an app in real-time.

    Args:
        slug (str): The slug of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[Union['LogLine', 'SSEWarning']]]
    """

    kwargs = _get_kwargs(
        slug=slug,
        seq=seq,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    slug: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Optional[list[Union["LogLine", "SSEWarning"]]]:
    """Stream run logs

     Streams the logs associated with a particular run of an app in real-time.

    Args:
        slug (str): The slug of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[Union['LogLine', 'SSEWarning']]
    """

    return sync_detailed(
        slug=slug,
        seq=seq,
        client=client,
    ).parsed


async def asyncio_detailed(
    slug: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Response[list[Union["LogLine", "SSEWarning"]]]:
    """Stream run logs

     Streams the logs associated with a particular run of an app in real-time.

    Args:
        slug (str): The slug of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[Union['LogLine', 'SSEWarning']]]
    """

    kwargs = _get_kwargs(
        slug=slug,
        seq=seq,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    slug: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Optional[list[Union["LogLine", "SSEWarning"]]]:
    """Stream run logs

     Streams the logs associated with a particular run of an app in real-time.

    Args:
        slug (str): The slug of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[Union['LogLine', 'SSEWarning']]
    """

    return (
        await asyncio_detailed(
            slug=slug,
            seq=seq,
            client=client,
        )
    ).parsed
