from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.batch_describe_runs_logs_params import BatchDescribeRunsLogsParams
from ...models.batched_run_log_lines import BatchedRunLogLines
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs(
    *,
    body: list[BatchDescribeRunsLogsParams],
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/batch/describe-runs-logs",
    }

    _kwargs["json"] = []
    for body_item_data in body:
        body_item = body_item_data.to_dict()
        _kwargs["json"].append(body_item)

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | list[BatchedRunLogLines]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = BatchedRunLogLines.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | list[BatchedRunLogLines]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: list[BatchDescribeRunsLogsParams],
) -> Response[ErrorModel | list[BatchedRunLogLines]]:
    """Batch describe runs logs

     Describe multiple run logs in a single request.

    Args:
        body (list[BatchDescribeRunsLogsParams]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | list[BatchedRunLogLines]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: list[BatchDescribeRunsLogsParams],
) -> ErrorModel | list[BatchedRunLogLines] | None:
    """Batch describe runs logs

     Describe multiple run logs in a single request.

    Args:
        body (list[BatchDescribeRunsLogsParams]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | list[BatchedRunLogLines]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: list[BatchDescribeRunsLogsParams],
) -> Response[ErrorModel | list[BatchedRunLogLines]]:
    """Batch describe runs logs

     Describe multiple run logs in a single request.

    Args:
        body (list[BatchDescribeRunsLogsParams]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | list[BatchedRunLogLines]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: list[BatchDescribeRunsLogsParams],
) -> ErrorModel | list[BatchedRunLogLines] | None:
    """Batch describe runs logs

     Describe multiple run logs in a single request.

    Args:
        body (list[BatchDescribeRunsLogsParams]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | list[BatchedRunLogLines]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
