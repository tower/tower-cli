from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.list_app_versions_response import ListAppVersionsResponse
from ...types import Response


def _get_kwargs(
    name: str,
    *,
    client: AuthenticatedClient,
) -> Dict[str, Any]:
    url = "{}/apps/{name}/versions".format(client.base_url, name=name)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, response: httpx.Response) -> Optional[ListAppVersionsResponse]:
    if response.status_code == 200:
        response_200 = ListAppVersionsResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[ListAppVersionsResponse]:
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
) -> Response[ListAppVersionsResponse]:
    """List app versions

     List all versions of an app in the current account, sorted with the most recent first.

    Args:
        name (str): The name of the app to list versions for.

    Returns:
        Response[ListAppVersionsResponse]
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
) -> Optional[ListAppVersionsResponse]:
    """List app versions

     List all versions of an app in the current account, sorted with the most recent first.

    Args:
        name (str): The name of the app to list versions for.

    Returns:
        Response[ListAppVersionsResponse]
    """

    return sync_detailed(
        name=name,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
) -> Response[ListAppVersionsResponse]:
    """List app versions

     List all versions of an app in the current account, sorted with the most recent first.

    Args:
        name (str): The name of the app to list versions for.

    Returns:
        Response[ListAppVersionsResponse]
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
) -> Optional[ListAppVersionsResponse]:
    """List app versions

     List all versions of an app in the current account, sorted with the most recent first.

    Args:
        name (str): The name of the app to list versions for.

    Returns:
        Response[ListAppVersionsResponse]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
        )
    ).parsed
