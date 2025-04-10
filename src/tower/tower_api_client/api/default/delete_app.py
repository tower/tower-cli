from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.delete_app_response import DeleteAppResponse
from ...types import Response


def _get_kwargs(
    name: str,
    *,
    client: AuthenticatedClient,
) -> Dict[str, Any]:
    url = "{}/apps/{name}".format(client.base_url, name=name)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "delete",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, response: httpx.Response) -> Optional[DeleteAppResponse]:
    if response.status_code == 200:
        response_200 = DeleteAppResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[DeleteAppResponse]:
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
) -> Response[DeleteAppResponse]:
    """Delete app

     Delete one of your apps, the associated code, and all the runs as well.

    Args:
        name (str): The name of the app to delete.

    Returns:
        Response[DeleteAppResponse]
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
) -> Optional[DeleteAppResponse]:
    """Delete app

     Delete one of your apps, the associated code, and all the runs as well.

    Args:
        name (str): The name of the app to delete.

    Returns:
        Response[DeleteAppResponse]
    """

    return sync_detailed(
        name=name,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
) -> Response[DeleteAppResponse]:
    """Delete app

     Delete one of your apps, the associated code, and all the runs as well.

    Args:
        name (str): The name of the app to delete.

    Returns:
        Response[DeleteAppResponse]
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
) -> Optional[DeleteAppResponse]:
    """Delete app

     Delete one of your apps, the associated code, and all the runs as well.

    Args:
        name (str): The name of the app to delete.

    Returns:
        Response[DeleteAppResponse]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
        )
    ).parsed
