from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.list_team_invitations_response import ListTeamInvitationsResponse
from ...types import Response


def _get_kwargs(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Dict[str, Any]:
    url = "{}/teams/{slug}/invites".format(client.base_url, slug=slug)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(
    *, response: httpx.Response
) -> Optional[ListTeamInvitationsResponse]:
    if response.status_code == 200:
        response_200 = ListTeamInvitationsResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(
    *, response: httpx.Response
) -> Response[ListTeamInvitationsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Response[ListTeamInvitationsResponse]:
    """List Team Invitations

     List the pending invitations for a team

    Args:
        slug (str): The slug of the team to list members for

    Returns:
        Response[ListTeamInvitationsResponse]
    """

    kwargs = _get_kwargs(
        slug=slug,
        client=client,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Optional[ListTeamInvitationsResponse]:
    """List Team Invitations

     List the pending invitations for a team

    Args:
        slug (str): The slug of the team to list members for

    Returns:
        Response[ListTeamInvitationsResponse]
    """

    return sync_detailed(
        slug=slug,
        client=client,
    ).parsed


async def asyncio_detailed(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Response[ListTeamInvitationsResponse]:
    """List Team Invitations

     List the pending invitations for a team

    Args:
        slug (str): The slug of the team to list members for

    Returns:
        Response[ListTeamInvitationsResponse]
    """

    kwargs = _get_kwargs(
        slug=slug,
        client=client,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Optional[ListTeamInvitationsResponse]:
    """List Team Invitations

     List the pending invitations for a team

    Args:
        slug (str): The slug of the team to list members for

    Returns:
        Response[ListTeamInvitationsResponse]
    """

    return (
        await asyncio_detailed(
            slug=slug,
            client=client,
        )
    ).parsed
