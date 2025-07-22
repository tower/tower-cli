from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_team_invitation_params import DeleteTeamInvitationParams
from ...models.delete_team_invitation_response import DeleteTeamInvitationResponse
from ...types import Response


def _get_kwargs(
    name: str,
    *,
    body: DeleteTeamInvitationParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/teams/{name}/invites".format(
            name=name,
        ),
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[DeleteTeamInvitationResponse]:
    if response.status_code == 200:
        response_200 = DeleteTeamInvitationResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[DeleteTeamInvitationResponse]:
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
    body: DeleteTeamInvitationParams,
) -> Response[DeleteTeamInvitationResponse]:
    """Delete team invitation

     Delete a pending team invitation that you have previously sent

    Args:
        name (str): The name of the team to remove someone from
        body (DeleteTeamInvitationParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteTeamInvitationResponse]
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
    body: DeleteTeamInvitationParams,
) -> Optional[DeleteTeamInvitationResponse]:
    """Delete team invitation

     Delete a pending team invitation that you have previously sent

    Args:
        name (str): The name of the team to remove someone from
        body (DeleteTeamInvitationParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteTeamInvitationResponse
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
    body: DeleteTeamInvitationParams,
) -> Response[DeleteTeamInvitationResponse]:
    """Delete team invitation

     Delete a pending team invitation that you have previously sent

    Args:
        name (str): The name of the team to remove someone from
        body (DeleteTeamInvitationParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteTeamInvitationResponse]
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
    body: DeleteTeamInvitationParams,
) -> Optional[DeleteTeamInvitationResponse]:
    """Delete team invitation

     Delete a pending team invitation that you have previously sent

    Args:
        name (str): The name of the team to remove someone from
        body (DeleteTeamInvitationParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteTeamInvitationResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
        )
    ).parsed
