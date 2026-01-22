from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.run_app_params import RunAppParams
from ...models.run_app_response import RunAppResponse
from ...types import Response


def _get_kwargs(
    name: str,
    *,
    body: RunAppParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/apps/{name}/runs".format(
            name=quote(str(name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | RunAppResponse | None:
    if response.status_code == 201:
        response_201 = RunAppResponse.from_dict(response.json())

        return response_201

    if response.status_code == 401:
        response_401 = ErrorModel.from_dict(response.json())

        return response_401

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | RunAppResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    body: RunAppParams,
) -> Response[ErrorModel | RunAppResponse]:
    """Run app

     Runs an app with the supplied parameters.

    Args:
        name (str): The name of the app to fetch runs for.
        body (RunAppParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | RunAppResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient,
    body: RunAppParams,
) -> ErrorModel | RunAppResponse | None:
    """Run app

     Runs an app with the supplied parameters.

    Args:
        name (str): The name of the app to fetch runs for.
        body (RunAppParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | RunAppResponse
    """

    return sync_detailed(
        name=name,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    body: RunAppParams,
) -> Response[ErrorModel | RunAppResponse]:
    """Run app

     Runs an app with the supplied parameters.

    Args:
        name (str): The name of the app to fetch runs for.
        body (RunAppParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | RunAppResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
    body: RunAppParams,
) -> ErrorModel | RunAppResponse | None:
    """Run app

     Runs an app with the supplied parameters.

    Args:
        name (str): The name of the app to fetch runs for.
        body (RunAppParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | RunAppResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
        )
    ).parsed
