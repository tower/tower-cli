from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.invite_team_member_params import InviteTeamMemberParams
from ...models.invite_team_member_response import InviteTeamMemberResponse
from ...types import Response


def _get_kwargs(
    slug: str,
    *,
    body: InviteTeamMemberParams,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/teams/{slug}/invites".format(
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
) -> Optional[InviteTeamMemberResponse]:
    if response.status_code == 200:
        response_200 = InviteTeamMemberResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[InviteTeamMemberResponse]:
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
    body: InviteTeamMemberParams,
) -> Response[InviteTeamMemberResponse]:
    """Invite team member

     Invite a new team

    Args:
        slug (str): The slug of the team to invite someone to
        body (InviteTeamMemberParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[InviteTeamMemberResponse]
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
    body: InviteTeamMemberParams,
) -> Optional[InviteTeamMemberResponse]:
    """Invite team member

     Invite a new team

    Args:
        slug (str): The slug of the team to invite someone to
        body (InviteTeamMemberParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        InviteTeamMemberResponse
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
    body: InviteTeamMemberParams,
) -> Response[InviteTeamMemberResponse]:
    """Invite team member

     Invite a new team

    Args:
        slug (str): The slug of the team to invite someone to
        body (InviteTeamMemberParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[InviteTeamMemberResponse]
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
    body: InviteTeamMemberParams,
) -> Optional[InviteTeamMemberResponse]:
    """Invite team member

     Invite a new team

    Args:
        slug (str): The slug of the team to invite someone to
        body (InviteTeamMemberParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        InviteTeamMemberResponse
    """

    return (
        await asyncio_detailed(
            slug=slug,
            client=client,
            body=body,
        )
    ).parsed
