from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.update_email_preferences_body import UpdateEmailPreferencesBody
from ...types import Response


def _get_kwargs(
    *,
    body: UpdateEmailPreferencesBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/user/email-preferences",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | UpdateEmailPreferencesBody:
    if response.status_code == 200:
        response_200 = UpdateEmailPreferencesBody.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | UpdateEmailPreferencesBody]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: UpdateEmailPreferencesBody,
) -> Response[ErrorModel | UpdateEmailPreferencesBody]:
    """Update email preferences

     Updates the set of email preferences the current user has. If a partial set of preferences is
    submitted, it will be updated accordingly.

    Args:
        body (UpdateEmailPreferencesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateEmailPreferencesBody]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: UpdateEmailPreferencesBody,
) -> ErrorModel | UpdateEmailPreferencesBody | None:
    """Update email preferences

     Updates the set of email preferences the current user has. If a partial set of preferences is
    submitted, it will be updated accordingly.

    Args:
        body (UpdateEmailPreferencesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateEmailPreferencesBody
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: UpdateEmailPreferencesBody,
) -> Response[ErrorModel | UpdateEmailPreferencesBody]:
    """Update email preferences

     Updates the set of email preferences the current user has. If a partial set of preferences is
    submitted, it will be updated accordingly.

    Args:
        body (UpdateEmailPreferencesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateEmailPreferencesBody]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: UpdateEmailPreferencesBody,
) -> ErrorModel | UpdateEmailPreferencesBody | None:
    """Update email preferences

     Updates the set of email preferences the current user has. If a partial set of preferences is
    submitted, it will be updated accordingly.

    Args:
        body (UpdateEmailPreferencesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateEmailPreferencesBody
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
