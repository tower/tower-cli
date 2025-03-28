from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.deploy_app_response import DeployAppResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    client: AuthenticatedClient,
    content_encoding: Union[Unset, str] = UNSET,
) -> Dict[str, Any]:
    url = "{}/apps/{name}/deploy".format(client.base_url, name=name)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    if not isinstance(content_encoding, Unset):
        headers["Content-Encoding"] = content_encoding

    return {
        "method": "post",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, response: httpx.Response) -> Optional[DeployAppResponse]:
    if response.status_code == 200:
        response_200 = DeployAppResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[DeployAppResponse]:
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
    content_encoding: Union[Unset, str] = UNSET,
) -> Response[DeployAppResponse]:
    """Deploy app

     Deploy a new version of an app. Reads the request body, which is a TAR file (or a GZipped TAR file)
    and creates a new deployment for an app based on that file.

    Args:
        name (str): The name of the app to deploy.
        content_encoding (Union[Unset, str]): The encoding of the content.

    Returns:
        Response[DeployAppResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        client=client,
        content_encoding=content_encoding,
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
    content_encoding: Union[Unset, str] = UNSET,
) -> Optional[DeployAppResponse]:
    """Deploy app

     Deploy a new version of an app. Reads the request body, which is a TAR file (or a GZipped TAR file)
    and creates a new deployment for an app based on that file.

    Args:
        name (str): The name of the app to deploy.
        content_encoding (Union[Unset, str]): The encoding of the content.

    Returns:
        Response[DeployAppResponse]
    """

    return sync_detailed(
        name=name,
        client=client,
        content_encoding=content_encoding,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    content_encoding: Union[Unset, str] = UNSET,
) -> Response[DeployAppResponse]:
    """Deploy app

     Deploy a new version of an app. Reads the request body, which is a TAR file (or a GZipped TAR file)
    and creates a new deployment for an app based on that file.

    Args:
        name (str): The name of the app to deploy.
        content_encoding (Union[Unset, str]): The encoding of the content.

    Returns:
        Response[DeployAppResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        client=client,
        content_encoding=content_encoding,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
    content_encoding: Union[Unset, str] = UNSET,
) -> Optional[DeployAppResponse]:
    """Deploy app

     Deploy a new version of an app. Reads the request body, which is a TAR file (or a GZipped TAR file)
    and creates a new deployment for an app based on that file.

    Args:
        name (str): The name of the app to deploy.
        content_encoding (Union[Unset, str]): The encoding of the content.

    Returns:
        Response[DeployAppResponse]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            content_encoding=content_encoding,
        )
    ).parsed
