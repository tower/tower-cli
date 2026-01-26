from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.update_webhook_params import UpdateWebhookParams
from ...models.update_webhook_response import UpdateWebhookResponse
from ...types import Response


def _get_kwargs(
    name: str,
    *,
    body: UpdateWebhookParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/webhooks/{name}".format(
            name=quote(str(name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | UpdateWebhookResponse:
    if response.status_code == 200:
        response_200 = UpdateWebhookResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | UpdateWebhookResponse]:
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
    body: UpdateWebhookParams,
) -> Response[ErrorModel | UpdateWebhookResponse]:
    """Update webhook

     Updates webhook. Note: it is not possible to update the URL. To do so, you should delete and
    recreate the webhook instead.

    Args:
        name (str): The name of the webhook.
        body (UpdateWebhookParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateWebhookResponse]
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
    body: UpdateWebhookParams,
) -> ErrorModel | UpdateWebhookResponse | None:
    """Update webhook

     Updates webhook. Note: it is not possible to update the URL. To do so, you should delete and
    recreate the webhook instead.

    Args:
        name (str): The name of the webhook.
        body (UpdateWebhookParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateWebhookResponse
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
    body: UpdateWebhookParams,
) -> Response[ErrorModel | UpdateWebhookResponse]:
    """Update webhook

     Updates webhook. Note: it is not possible to update the URL. To do so, you should delete and
    recreate the webhook instead.

    Args:
        name (str): The name of the webhook.
        body (UpdateWebhookParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateWebhookResponse]
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
    body: UpdateWebhookParams,
) -> ErrorModel | UpdateWebhookResponse | None:
    """Update webhook

     Updates webhook. Note: it is not possible to update the URL. To do so, you should delete and
    recreate the webhook instead.

    Args:
        name (str): The name of the webhook.
        body (UpdateWebhookParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateWebhookResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
        )
    ).parsed
