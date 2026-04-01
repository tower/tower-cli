from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.delete_guest_output_body import DeleteGuestOutputBody
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs(
    guest_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/guests/{guest_id}".format(
            guest_id=quote(str(guest_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DeleteGuestOutputBody | ErrorModel:
    if response.status_code == 204:
        response_204 = DeleteGuestOutputBody.from_dict(response.json())

        return response_204

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DeleteGuestOutputBody | ErrorModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    guest_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[DeleteGuestOutputBody | ErrorModel]:
    """Delete guest

     Deletes a guest and revokes their access. Any active sessions will be invalidated.

    Args:
        guest_id (str): The ID of the guest to delete.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteGuestOutputBody | ErrorModel]
    """

    kwargs = _get_kwargs(
        guest_id=guest_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    guest_id: str,
    *,
    client: AuthenticatedClient,
) -> DeleteGuestOutputBody | ErrorModel | None:
    """Delete guest

     Deletes a guest and revokes their access. Any active sessions will be invalidated.

    Args:
        guest_id (str): The ID of the guest to delete.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteGuestOutputBody | ErrorModel
    """

    return sync_detailed(
        guest_id=guest_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    guest_id: str,
    *,
    client: AuthenticatedClient,
) -> Response[DeleteGuestOutputBody | ErrorModel]:
    """Delete guest

     Deletes a guest and revokes their access. Any active sessions will be invalidated.

    Args:
        guest_id (str): The ID of the guest to delete.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteGuestOutputBody | ErrorModel]
    """

    kwargs = _get_kwargs(
        guest_id=guest_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    guest_id: str,
    *,
    client: AuthenticatedClient,
) -> DeleteGuestOutputBody | ErrorModel | None:
    """Delete guest

     Deletes a guest and revokes their access. Any active sessions will be invalidated.

    Args:
        guest_id (str): The ID of the guest to delete.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteGuestOutputBody | ErrorModel
    """

    return (
        await asyncio_detailed(
            guest_id=guest_id,
            client=client,
        )
    ).parsed
