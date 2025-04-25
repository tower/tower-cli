from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.describe_app_version_response import DescribeAppVersionResponse
from ...types import Response


def _get_kwargs(
    name: str,
    num: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{name}/versions/{num}".format(
            name=name,
            num=num,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[DescribeAppVersionResponse]:
    if response.status_code == 200:
        response_200 = DescribeAppVersionResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[DescribeAppVersionResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    num: str,
    *,
    client: AuthenticatedClient,
) -> Response[DescribeAppVersionResponse]:
    """Describe app version

     Describe an app version for an app in the current account.

    Args:
        name (str): The name of the app to get the version for.
        num (str): The version string to get the version for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeAppVersionResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        num=num,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    num: str,
    *,
    client: AuthenticatedClient,
) -> Optional[DescribeAppVersionResponse]:
    """Describe app version

     Describe an app version for an app in the current account.

    Args:
        name (str): The name of the app to get the version for.
        num (str): The version string to get the version for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeAppVersionResponse
    """

    return sync_detailed(
        name=name,
        num=num,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    num: str,
    *,
    client: AuthenticatedClient,
) -> Response[DescribeAppVersionResponse]:
    """Describe app version

     Describe an app version for an app in the current account.

    Args:
        name (str): The name of the app to get the version for.
        num (str): The version string to get the version for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DescribeAppVersionResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        num=num,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    num: str,
    *,
    client: AuthenticatedClient,
) -> Optional[DescribeAppVersionResponse]:
    """Describe app version

     Describe an app version for an app in the current account.

    Args:
        name (str): The name of the app to get the version for.
        num (str): The version string to get the version for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DescribeAppVersionResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            num=num,
            client=client,
        )
    ).parsed
