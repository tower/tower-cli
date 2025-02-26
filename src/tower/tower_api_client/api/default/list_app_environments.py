from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.list_app_environments_response import ListAppEnvironmentsResponse
from ...types import Response


def _get_kwargs(
    name: str,
    *,
    client: AuthenticatedClient,
) -> Dict[str, Any]:
    url = "{}/apps/{name}/environments".format(client.base_url, name=name)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(
    *, response: httpx.Response
) -> Optional[ListAppEnvironmentsResponse]:
    if response.status_code == 200:
        response_200 = ListAppEnvironmentsResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(
    *, response: httpx.Response
) -> Response[ListAppEnvironmentsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
) -> Response[ListAppEnvironmentsResponse]:
    """List app environments

     Generates a list of all the known environments for a given app in the current account.

    Args:
        name (str): The name of the app to get the version for.

    Returns:
        Response[ListAppEnvironmentsResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        client=client,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient,
) -> Optional[ListAppEnvironmentsResponse]:
    """List app environments

     Generates a list of all the known environments for a given app in the current account.

    Args:
        name (str): The name of the app to get the version for.

    Returns:
        Response[ListAppEnvironmentsResponse]
    """

    return sync_detailed(
        name=name,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
) -> Response[ListAppEnvironmentsResponse]:
    """List app environments

     Generates a list of all the known environments for a given app in the current account.

    Args:
        name (str): The name of the app to get the version for.

    Returns:
        Response[ListAppEnvironmentsResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        client=client,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
) -> Optional[ListAppEnvironmentsResponse]:
    """List app environments

     Generates a list of all the known environments for a given app in the current account.

    Args:
        name (str): The name of the app to get the version for.

    Returns:
        Response[ListAppEnvironmentsResponse]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
        )
    ).parsed
