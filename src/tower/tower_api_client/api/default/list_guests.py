from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.list_guests_response import ListGuestsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    app: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["app"] = app

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/guests",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | ListGuestsResponse:
    if response.status_code == 200:
        response_200 = ListGuestsResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | ListGuestsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    app: str | Unset = UNSET,
) -> Response[ErrorModel | ListGuestsResponse]:
    """List guests

     Lists all guests for the current account, optionally filtered by app.

    Args:
        app (str | Unset): Filter guests by app name.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | ListGuestsResponse]
    """

    kwargs = _get_kwargs(
        app=app,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    app: str | Unset = UNSET,
) -> ErrorModel | ListGuestsResponse | None:
    """List guests

     Lists all guests for the current account, optionally filtered by app.

    Args:
        app (str | Unset): Filter guests by app name.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | ListGuestsResponse
    """

    return sync_detailed(
        client=client,
        app=app,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    app: str | Unset = UNSET,
) -> Response[ErrorModel | ListGuestsResponse]:
    """List guests

     Lists all guests for the current account, optionally filtered by app.

    Args:
        app (str | Unset): Filter guests by app name.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | ListGuestsResponse]
    """

    kwargs = _get_kwargs(
        app=app,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    app: str | Unset = UNSET,
) -> ErrorModel | ListGuestsResponse | None:
    """List guests

     Lists all guests for the current account, optionally filtered by app.

    Args:
        app (str | Unset): Filter guests by app name.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | ListGuestsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            app=app,
        )
    ).parsed
