from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.resend_team_invitation_params import ResendTeamInvitationParams
from ...models.resend_team_invitation_response import ResendTeamInvitationResponse
from ...types import Response


def _get_kwargs(
    slug: str,
    *,
    client: AuthenticatedClient,
    json_body: ResendTeamInvitationParams,
) -> Dict[str, Any]:
    url = "{}/teams/{slug}/invites/resend".format(client.base_url, slug=slug)

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


def _parse_response(
    *, response: httpx.Response
) -> Optional[ResendTeamInvitationResponse]:
    if response.status_code == 200:
        response_200 = ResendTeamInvitationResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(
    *, response: httpx.Response
) -> Response[ResendTeamInvitationResponse]:
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
    json_body: ResendTeamInvitationParams,
) -> Response[ResendTeamInvitationResponse]:
    """Resend Team Invitation

     Resend a team invitation to a user if they need a reminder or if they lost it

    Args:
        slug (str): The slug of the team to invite someone to
        json_body (ResendTeamInvitationParams):

    Returns:
        Response[ResendTeamInvitationResponse]
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
    json_body: ResendTeamInvitationParams,
) -> Optional[ResendTeamInvitationResponse]:
    """Resend Team Invitation

     Resend a team invitation to a user if they need a reminder or if they lost it

    Args:
        slug (str): The slug of the team to invite someone to
        json_body (ResendTeamInvitationParams):

    Returns:
        Response[ResendTeamInvitationResponse]
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
    json_body: ResendTeamInvitationParams,
) -> Response[ResendTeamInvitationResponse]:
    """Resend Team Invitation

     Resend a team invitation to a user if they need a reminder or if they lost it

    Args:
        slug (str): The slug of the team to invite someone to
        json_body (ResendTeamInvitationParams):

    Returns:
        Response[ResendTeamInvitationResponse]
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
    json_body: ResendTeamInvitationParams,
) -> Optional[ResendTeamInvitationResponse]:
    """Resend Team Invitation

     Resend a team invitation to a user if they need a reminder or if they lost it

    Args:
        slug (str): The slug of the team to invite someone to
        json_body (ResendTeamInvitationParams):

    Returns:
        Response[ResendTeamInvitationResponse]
    """

    return (
        await asyncio_detailed(
            slug=slug,
            client=client,
            json_body=json_body,
        )
    ).parsed
