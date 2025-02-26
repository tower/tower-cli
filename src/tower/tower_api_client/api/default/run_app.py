from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.run_app_params import RunAppParams
from ...models.run_app_response import RunAppResponse
from ...types import Response


def _get_kwargs(
    name: str,
    *,
    client: AuthenticatedClient,
    json_body: RunAppParams,
) -> Dict[str, Any]:
    url = "{}/apps/{name}/runs".format(client.base_url, name=name)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    json_json_body = json_body.to_dict()

    return {
        "method": "post",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
    }


def _parse_response(*, response: httpx.Response) -> Optional[RunAppResponse]:
    if response.status_code == 200:
        response_200 = RunAppResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[RunAppResponse]:
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
    json_body: RunAppParams,
) -> Response[RunAppResponse]:
    """Run app

     Runs an app with the supplied parameters.

    Args:
        name (str): The name of the app to fetch runs for.
        json_body (RunAppParams):

    Returns:
        Response[RunAppResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        client=client,
        json_body=json_body,
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
    json_body: RunAppParams,
) -> Optional[RunAppResponse]:
    """Run app

     Runs an app with the supplied parameters.

    Args:
        name (str): The name of the app to fetch runs for.
        json_body (RunAppParams):

    Returns:
        Response[RunAppResponse]
    """

    return sync_detailed(
        name=name,
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    json_body: RunAppParams,
) -> Response[RunAppResponse]:
    """Run app

     Runs an app with the supplied parameters.

    Args:
        name (str): The name of the app to fetch runs for.
        json_body (RunAppParams):

    Returns:
        Response[RunAppResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        client=client,
        json_body=json_body,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
    json_body: RunAppParams,
) -> Optional[RunAppResponse]:
    """Run app

     Runs an app with the supplied parameters.

    Args:
        name (str): The name of the app to fetch runs for.
        json_body (RunAppParams):

    Returns:
        Response[RunAppResponse]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            json_body=json_body,
        )
    ).parsed
