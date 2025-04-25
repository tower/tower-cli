from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.run_app_params import RunAppParams
from ...models.run_app_response import RunAppResponse
from ...types import Response


def _get_kwargs(
    slug: str,
    *,
    body: RunAppParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/apps/{slug}/runs".format(
            slug=slug,
        ),
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ErrorModel, RunAppResponse]]:
    if response.status_code == 200:
        response_200 = RunAppResponse.from_dict(response.json())

        return response_200
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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ErrorModel, RunAppResponse]]:
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
    body: RunAppParams,
) -> Response[Union[ErrorModel, RunAppResponse]]:
    """Run app

     Runs an app with the supplied parameters.

    Args:
        slug (str): The slug of the app to fetch runs for.
        body (RunAppParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorModel, RunAppResponse]]
    """

    kwargs = _get_kwargs(
        slug=slug,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    slug: str,
    *,
    client: AuthenticatedClient,
    body: RunAppParams,
) -> Optional[Union[ErrorModel, RunAppResponse]]:
    """Run app

     Runs an app with the supplied parameters.

    Args:
        slug (str): The slug of the app to fetch runs for.
        body (RunAppParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorModel, RunAppResponse]
    """

    return sync_detailed(
        slug=slug,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    slug: str,
    *,
    client: AuthenticatedClient,
    body: RunAppParams,
) -> Response[Union[ErrorModel, RunAppResponse]]:
    """Run app

     Runs an app with the supplied parameters.

    Args:
        slug (str): The slug of the app to fetch runs for.
        body (RunAppParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorModel, RunAppResponse]]
    """

    kwargs = _get_kwargs(
        slug=slug,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    slug: str,
    *,
    client: AuthenticatedClient,
    body: RunAppParams,
) -> Optional[Union[ErrorModel, RunAppResponse]]:
    """Run app

     Runs an app with the supplied parameters.

    Args:
        slug (str): The slug of the app to fetch runs for.
        body (RunAppParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorModel, RunAppResponse]
    """

    return (
        await asyncio_detailed(
            slug=slug,
            client=client,
            body=body,
        )
    ).parsed
