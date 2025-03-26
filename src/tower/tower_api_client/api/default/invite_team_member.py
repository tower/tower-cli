from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.invite_team_member_params import InviteTeamMemberParams
from ...models.invite_team_member_response import InviteTeamMemberResponse
from ...types import Response


def _get_kwargs(
    slug: str,
    *,
    client: AuthenticatedClient,
    json_body: InviteTeamMemberParams,
) -> Dict[str, Any]:
    url = "{}/teams/{slug}/invites".format(client.base_url, slug=slug)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    json_json_body = json_body.to_dict()

    return {
        "method": "post",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
    }


def _parse_response(*, response: httpx.Response) -> Optional[InviteTeamMemberResponse]:
    if response.status_code == 200:
        response_200 = InviteTeamMemberResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[InviteTeamMemberResponse]:
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
    json_body: InviteTeamMemberParams,
) -> Response[InviteTeamMemberResponse]:
    """Invite Team Member

     Invite a new team

    Args:
        slug (str): The slug of the team to invite someone to
        json_body (InviteTeamMemberParams):

    Returns:
        Response[InviteTeamMemberResponse]
    """

    kwargs = _get_kwargs(
        slug=slug,
        client=client,
        json_body=json_body,
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
    json_body: InviteTeamMemberParams,
) -> Optional[InviteTeamMemberResponse]:
    """Invite Team Member

     Invite a new team

    Args:
        slug (str): The slug of the team to invite someone to
        json_body (InviteTeamMemberParams):

    Returns:
        Response[InviteTeamMemberResponse]
    """

    return sync_detailed(
        slug=slug,
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    slug: str,
    *,
    client: AuthenticatedClient,
    json_body: InviteTeamMemberParams,
) -> Response[InviteTeamMemberResponse]:
    """Invite Team Member

     Invite a new team

    Args:
        slug (str): The slug of the team to invite someone to
        json_body (InviteTeamMemberParams):

    Returns:
        Response[InviteTeamMemberResponse]
    """

    kwargs = _get_kwargs(
        slug=slug,
        client=client,
        json_body=json_body,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    slug: str,
    *,
    client: AuthenticatedClient,
    json_body: InviteTeamMemberParams,
) -> Optional[InviteTeamMemberResponse]:
    """Invite Team Member

     Invite a new team

    Args:
        slug (str): The slug of the team to invite someone to
        json_body (InviteTeamMemberParams):

    Returns:
        Response[InviteTeamMemberResponse]
    """

    return (
        await asyncio_detailed(
            slug=slug,
            client=client,
            json_body=json_body,
        )
    ).parsed
