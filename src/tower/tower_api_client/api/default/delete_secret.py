from http import HTTPStatus
from typing import Any, Dict, Union

import httpx

from ...client import AuthenticatedClient
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, None, str] = UNSET,
) -> Dict[str, Any]:
    url = "{}/secrets/{name}".format(client.base_url, name=name)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    params: Dict[str, Any] = {}
    params["environment"] = environment

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "delete",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _build_response(*, response: httpx.Response) -> Response[Any]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=None,
    )


def sync_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, None, str] = UNSET,
) -> Response[Any]:
    """Delete a secret.

     Delete a secret by name.

    Args:
        name (str): The name of the secret to delete.
        environment (Union[Unset, None, str]): The environment of the secret to delete.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        name=name,
        client=client,
        environment=environment,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, None, str] = UNSET,
) -> Response[Any]:
    """Delete a secret.

     Delete a secret by name.

    Args:
        name (str): The name of the secret to delete.
        environment (Union[Unset, None, str]): The environment of the secret to delete.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        name=name,
        client=client,
        environment=environment,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)
