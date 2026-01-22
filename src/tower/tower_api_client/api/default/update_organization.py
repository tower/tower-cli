from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.update_organization_params import UpdateOrganizationParams
from ...models.update_organization_response import UpdateOrganizationResponse
from ...types import Response


def _get_kwargs(
    name: str,
    *,
    body: UpdateOrganizationParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/organizations/{name}".format(
            name=quote(str(name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | UpdateOrganizationResponse:
    if response.status_code == 200:
        response_200 = UpdateOrganizationResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | UpdateOrganizationResponse]:
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
    body: UpdateOrganizationParams,
) -> Response[ErrorModel | UpdateOrganizationResponse]:
    """Update organization

     Update an organization's name. Only the current owner can perform this operation.

    Args:
        name (str): The current name of the organization to update
        body (UpdateOrganizationParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateOrganizationResponse]
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
    body: UpdateOrganizationParams,
) -> ErrorModel | UpdateOrganizationResponse | None:
    """Update organization

     Update an organization's name. Only the current owner can perform this operation.

    Args:
        name (str): The current name of the organization to update
        body (UpdateOrganizationParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateOrganizationResponse
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
    body: UpdateOrganizationParams,
) -> Response[ErrorModel | UpdateOrganizationResponse]:
    """Update organization

     Update an organization's name. Only the current owner can perform this operation.

    Args:
        name (str): The current name of the organization to update
        body (UpdateOrganizationParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | UpdateOrganizationResponse]
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
    body: UpdateOrganizationParams,
) -> ErrorModel | UpdateOrganizationResponse | None:
    """Update organization

     Update an organization's name. Only the current owner can perform this operation.

    Args:
        name (str): The current name of the organization to update
        body (UpdateOrganizationParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | UpdateOrganizationResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
        )
    ).parsed
