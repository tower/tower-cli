from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_app_version_output_body import GetAppVersionOutputBody
from ...types import Response


def _get_kwargs(
    name: str,
    num: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/apps/{name}/versions/{num}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GetAppVersionOutputBody]:
    if response.status_code == 200:
        response_200 = GetAppVersionOutputBody.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GetAppVersionOutputBody]:
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
) -> Response[GetAppVersionOutputBody]:
    """Get an app version.

     Get an app version.

    Args:
        name (str): The name of the app to get the version for.
        num (str): The version string to get the version for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAppVersionOutputBody]
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
) -> Optional[GetAppVersionOutputBody]:
    """Get an app version.

     Get an app version.

    Args:
        name (str): The name of the app to get the version for.
        num (str): The version string to get the version for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAppVersionOutputBody
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
) -> Response[GetAppVersionOutputBody]:
    """Get an app version.

     Get an app version.

    Args:
        name (str): The name of the app to get the version for.
        num (str): The version string to get the version for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAppVersionOutputBody]
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
) -> Optional[GetAppVersionOutputBody]:
    """Get an app version.

     Get an app version.

    Args:
        name (str): The name of the app to get the version for.
        num (str): The version string to get the version for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAppVersionOutputBody
    """

    return (
        await asyncio_detailed(
            name=name,
            num=num,
            client=client,
        )
    ).parsed
