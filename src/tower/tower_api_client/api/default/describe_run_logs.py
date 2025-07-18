from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.describe_run_logs_response import DescribeRunLogsResponse
from ...types import Response


def _get_kwargs(
    name: str,
    seq: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{name}/runs/{seq}/logs".format(
            name=name,
            seq=seq,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[DescribeRunLogsResponse]:
    if response.status_code == 200:
        response_200 = DescribeRunLogsResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[DescribeRunLogsResponse]:
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
) -> Response[DescribeRunLogsResponse]:
    """Describe run logs

     Retrieves the logs associated with a particular run of an app.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeRunLogsResponse]
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
) -> Optional[DescribeRunLogsResponse]:
    """Describe run logs

     Retrieves the logs associated with a particular run of an app.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeRunLogsResponse
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
) -> Response[DescribeRunLogsResponse]:
    """Describe run logs

     Retrieves the logs associated with a particular run of an app.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeRunLogsResponse]
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
) -> Optional[DescribeRunLogsResponse]:
    """Describe run logs

     Retrieves the logs associated with a particular run of an app.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeRunLogsResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            seq=seq,
            client=client,
        )
    ).parsed
