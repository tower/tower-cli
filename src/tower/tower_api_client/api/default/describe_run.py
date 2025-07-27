from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.describe_run_response import DescribeRunResponse
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs(
    name: str,
    seq: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{name}/runs/{seq}".format(
            name=name,
            seq=seq,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[DescribeRunResponse, ErrorModel]]:
    if response.status_code == 200:
        response_200 = DescribeRunResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = ErrorModel.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = ErrorModel.from_dict(response.json())

        return response_404
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[DescribeRunResponse, ErrorModel]]:
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
) -> Response[Union[DescribeRunResponse, ErrorModel]]:
    """Describe run

     Describe a run of an app.

    Args:
        name (str): The name of the app to fetch runs for.
        seq (int): The number of the run to fetch.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DescribeRunResponse, ErrorModel]]
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
) -> Optional[Union[DescribeRunResponse, ErrorModel]]:
    """Describe run

     Describe a run of an app.

    Args:
        name (str): The name of the app to fetch runs for.
        seq (int): The number of the run to fetch.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DescribeRunResponse, ErrorModel]
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
) -> Response[Union[DescribeRunResponse, ErrorModel]]:
    """Describe run

     Describe a run of an app.

    Args:
        name (str): The name of the app to fetch runs for.
        seq (int): The number of the run to fetch.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DescribeRunResponse, ErrorModel]]
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
) -> Optional[Union[DescribeRunResponse, ErrorModel]]:
    """Describe run

     Describe a run of an app.

    Args:
        name (str): The name of the app to fetch runs for.
        seq (int): The number of the run to fetch.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DescribeRunResponse, ErrorModel]
    """

    return (
        await asyncio_detailed(
            name=name,
            seq=seq,
            client=client,
        )
    ).parsed
