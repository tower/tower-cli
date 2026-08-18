from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.update_app_params import UpdateAppParams
from ...models.update_app_response import UpdateAppResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    body: UpdateAppParams,
    x_tower_request_number: int | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_tower_request_number, Unset):
        headers["X-Tower-Request-Number"] = str(x_tower_request_number)

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/apps/{name}".format(
            name=quote(str(name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | UpdateAppResponse | None:
    if response.status_code == 200:
        response_200 = UpdateAppResponse.from_dict(response.json())

        return response_200

    if response.status_code == 412:
        response_412 = ErrorModel.from_dict(response.json())

        return response_412

    if response.status_code == 422:
        response_422 = ErrorModel.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = ErrorModel.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | UpdateAppResponse]:
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
    body: UpdateAppParams,
    x_tower_request_number: int | Unset = UNSET,
) -> Response[ErrorModel | UpdateAppResponse]:
    """Update app

     Update an app in the currently authenticated account.

    Args:
        name (str): The name of the App to update.
        x_tower_request_number (int | Unset): Optional account-scoped monotonic sequence token
            used to reject out-of-order writes. See the fence documentation for the acceptance window
            and retry behavior.
        body (UpdateAppParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateAppResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        x_tower_request_number=x_tower_request_number,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient,
    body: UpdateAppParams,
    x_tower_request_number: int | Unset = UNSET,
) -> ErrorModel | UpdateAppResponse | None:
    """Update app

     Update an app in the currently authenticated account.

    Args:
        name (str): The name of the App to update.
        x_tower_request_number (int | Unset): Optional account-scoped monotonic sequence token
            used to reject out-of-order writes. See the fence documentation for the acceptance window
            and retry behavior.
        body (UpdateAppParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateAppResponse
    """

    return sync_detailed(
        name=name,
        client=client,
        body=body,
        x_tower_request_number=x_tower_request_number,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    body: UpdateAppParams,
    x_tower_request_number: int | Unset = UNSET,
) -> Response[ErrorModel | UpdateAppResponse]:
    """Update app

     Update an app in the currently authenticated account.

    Args:
        name (str): The name of the App to update.
        x_tower_request_number (int | Unset): Optional account-scoped monotonic sequence token
            used to reject out-of-order writes. See the fence documentation for the acceptance window
            and retry behavior.
        body (UpdateAppParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateAppResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        x_tower_request_number=x_tower_request_number,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
    body: UpdateAppParams,
    x_tower_request_number: int | Unset = UNSET,
) -> ErrorModel | UpdateAppResponse | None:
    """Update app

     Update an app in the currently authenticated account.

    Args:
        name (str): The name of the App to update.
        x_tower_request_number (int | Unset): Optional account-scoped monotonic sequence token
            used to reject out-of-order writes. See the fence documentation for the acceptance window
            and retry behavior.
        body (UpdateAppParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateAppResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
            x_tower_request_number=x_tower_request_number,
        )
    ).parsed
