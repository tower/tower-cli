from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.describe_app_version_response import DescribeAppVersionResponse
from ...types import Response


def _get_kwargs(
    name: str,
    num: str,
    *,
    client: AuthenticatedClient,
) -> Dict[str, Any]:
    url = "{}/apps/{name}/versions/{num}".format(client.base_url, name=name, num=num)

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
) -> Optional[DescribeAppVersionResponse]:
    if response.status_code == 200:
        response_200 = DescribeAppVersionResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(
    *, response: httpx.Response
) -> Response[DescribeAppVersionResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
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

    Returns:
        Response[DescribeAppVersionResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        num=num,
        client=client,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


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

    Returns:
        Response[DescribeAppVersionResponse]
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

    Returns:
        Response[DescribeAppVersionResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        num=num,
        client=client,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


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

    Returns:
        Response[DescribeAppVersionResponse]
    """

    return (
        await asyncio_detailed(
            name=name,
            num=num,
            client=client,
        )
    ).parsed
