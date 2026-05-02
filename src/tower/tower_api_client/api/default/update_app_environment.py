from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.update_app_environment_params import UpdateAppEnvironmentParams
from ...models.update_app_environment_response import UpdateAppEnvironmentResponse
from ...types import Response


def _get_kwargs(
    name: str,
    environment: str,
    *,
    body: UpdateAppEnvironmentParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/apps/{name}/environments/{environment}".format(
            name=quote(str(name), safe=""),
            environment=quote(str(environment), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | UpdateAppEnvironmentResponse:
    if response.status_code == 200:
        response_200 = UpdateAppEnvironmentResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | UpdateAppEnvironmentResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    environment: str,
    *,
    client: AuthenticatedClient,
    body: UpdateAppEnvironmentParams,
) -> Response[ErrorModel | UpdateAppEnvironmentResponse]:
    """Update app environment

     Update the configuration of an app in a specific environment, such as which version is deployed.

    Args:
        name (str): The name of the app.
        environment (str): The name of the environment.
        body (UpdateAppEnvironmentParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateAppEnvironmentResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        environment=environment,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    environment: str,
    *,
    client: AuthenticatedClient,
    body: UpdateAppEnvironmentParams,
) -> ErrorModel | UpdateAppEnvironmentResponse | None:
    """Update app environment

     Update the configuration of an app in a specific environment, such as which version is deployed.

    Args:
        name (str): The name of the app.
        environment (str): The name of the environment.
        body (UpdateAppEnvironmentParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateAppEnvironmentResponse
    """

    return sync_detailed(
        name=name,
        environment=environment,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    name: str,
    environment: str,
    *,
    client: AuthenticatedClient,
    body: UpdateAppEnvironmentParams,
) -> Response[ErrorModel | UpdateAppEnvironmentResponse]:
    """Update app environment

     Update the configuration of an app in a specific environment, such as which version is deployed.

    Args:
        name (str): The name of the app.
        environment (str): The name of the environment.
        body (UpdateAppEnvironmentParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateAppEnvironmentResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        environment=environment,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    environment: str,
    *,
    client: AuthenticatedClient,
    body: UpdateAppEnvironmentParams,
) -> ErrorModel | UpdateAppEnvironmentResponse | None:
    """Update app environment

     Update the configuration of an app in a specific environment, such as which version is deployed.

    Args:
        name (str): The name of the app.
        environment (str): The name of the environment.
        body (UpdateAppEnvironmentParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateAppEnvironmentResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            environment=environment,
            client=client,
            body=body,
        )
    ).parsed
