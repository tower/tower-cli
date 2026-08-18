from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.batch_describe_runs_params import BatchDescribeRunsParams
from ...models.batch_describe_runs_response import BatchDescribeRunsResponse
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs(
    *,
    body: list[BatchDescribeRunsParams],
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/batch/describe-runs",
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
) -> BatchDescribeRunsResponse | ErrorModel:
    if response.status_code == 200:
        response_200 = BatchDescribeRunsResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[BatchDescribeRunsResponse | ErrorModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: list[BatchDescribeRunsParams],
) -> Response[BatchDescribeRunsResponse | ErrorModel]:
    """Batch describe runs

     Describe multiple runs in a single request.

    Args:
        body (list[BatchDescribeRunsParams]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BatchDescribeRunsResponse | ErrorModel]
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
    body: list[BatchDescribeRunsParams],
) -> BatchDescribeRunsResponse | ErrorModel | None:
    """Batch describe runs

     Describe multiple runs in a single request.

    Args:
        body (list[BatchDescribeRunsParams]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BatchDescribeRunsResponse | ErrorModel
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: list[BatchDescribeRunsParams],
) -> Response[BatchDescribeRunsResponse | ErrorModel]:
    """Batch describe runs

     Describe multiple runs in a single request.

    Args:
        body (list[BatchDescribeRunsParams]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BatchDescribeRunsResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: list[BatchDescribeRunsParams],
) -> BatchDescribeRunsResponse | ErrorModel | None:
    """Batch describe runs

     Describe multiple runs in a single request.

    Args:
        body (list[BatchDescribeRunsParams]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BatchDescribeRunsResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
