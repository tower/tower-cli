from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_app_environments_response import ListAppEnvironmentsResponse
from ...types import Response


def _get_kwargs(
    slug: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{slug}/environments".format(
            slug=slug,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[ListAppEnvironmentsResponse]:
    if response.status_code == 200:
        response_200 = ListAppEnvironmentsResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[ListAppEnvironmentsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Response[ListAppEnvironmentsResponse]:
    """List app environments

     Generates a list of all the known environments for a given app in the current account.

    Args:
        slug (str): The name of the app to get the version for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListAppEnvironmentsResponse]
    """

    kwargs = _get_kwargs(
        slug=slug,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Optional[ListAppEnvironmentsResponse]:
    """List app environments

     Generates a list of all the known environments for a given app in the current account.

    Args:
        slug (str): The name of the app to get the version for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListAppEnvironmentsResponse
    """

    return sync_detailed(
        slug=slug,
        client=client,
    ).parsed


async def asyncio_detailed(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Response[ListAppEnvironmentsResponse]:
    """List app environments

     Generates a list of all the known environments for a given app in the current account.

    Args:
        slug (str): The name of the app to get the version for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListAppEnvironmentsResponse]
    """

    kwargs = _get_kwargs(
        slug=slug,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Optional[ListAppEnvironmentsResponse]:
    """List app environments

     Generates a list of all the known environments for a given app in the current account.

    Args:
        slug (str): The name of the app to get the version for.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListAppEnvironmentsResponse
    """

    return (
        await asyncio_detailed(
            slug=slug,
            client=client,
        )
    ).parsed
