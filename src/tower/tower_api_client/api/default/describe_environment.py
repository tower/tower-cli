from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.describe_environment_response import DescribeEnvironmentResponse
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs(
    name: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/environments/{name}".format(
            name=quote(str(name), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DescribeEnvironmentResponse | ErrorModel:
    if response.status_code == 200:
        response_200 = DescribeEnvironmentResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DescribeEnvironmentResponse | ErrorModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
) -> Response[DescribeEnvironmentResponse | ErrorModel]:
    """Describe environment

     Describe an environment and counts of its resources

    Args:
        name (str): The name of the environment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeEnvironmentResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        name=name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient,
) -> DescribeEnvironmentResponse | ErrorModel | None:
    """Describe environment

     Describe an environment and counts of its resources

    Args:
        name (str): The name of the environment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeEnvironmentResponse | ErrorModel
    """

    return sync_detailed(
        name=name,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
) -> Response[DescribeEnvironmentResponse | ErrorModel]:
    """Describe environment

     Describe an environment and counts of its resources

    Args:
        name (str): The name of the environment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeEnvironmentResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        name=name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
) -> DescribeEnvironmentResponse | ErrorModel | None:
    """Describe environment

     Describe an environment and counts of its resources

    Args:
        name (str): The name of the environment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeEnvironmentResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
        )
    ).parsed
