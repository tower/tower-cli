from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.delete_team_invitation_params import DeleteTeamInvitationParams
from ...models.delete_team_invitation_response import DeleteTeamInvitationResponse
from ...types import Response


def _get_kwargs(
    slug: str,
    *,
    client: AuthenticatedClient,
    json_body: DeleteTeamInvitationParams,
) -> Dict[str, Any]:
    url = "{}/teams/{slug}/invites".format(client.base_url, slug=slug)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    json_json_body = json_body.to_dict()

    return {
        "method": "delete",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
    }


def _parse_response(
    *, response: httpx.Response
) -> Optional[DeleteTeamInvitationResponse]:
    if response.status_code == 200:
        response_200 = DeleteTeamInvitationResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(
    *, response: httpx.Response
) -> Response[DeleteTeamInvitationResponse]:
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
    json_body: DeleteTeamInvitationParams,
) -> Response[DeleteTeamInvitationResponse]:
    """Delete Team Invitation

     Delete a pending team invitation that you have previously sent

    Args:
        slug (str): The slug of the team to remove someone from
        json_body (DeleteTeamInvitationParams):

    Returns:
        Response[DeleteTeamInvitationResponse]
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
    json_body: DeleteTeamInvitationParams,
) -> Optional[DeleteTeamInvitationResponse]:
    """Delete Team Invitation

     Delete a pending team invitation that you have previously sent

    Args:
        slug (str): The slug of the team to remove someone from
        json_body (DeleteTeamInvitationParams):

    Returns:
        Response[DeleteTeamInvitationResponse]
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
    json_body: DeleteTeamInvitationParams,
) -> Response[DeleteTeamInvitationResponse]:
    """Delete Team Invitation

     Delete a pending team invitation that you have previously sent

    Args:
        slug (str): The slug of the team to remove someone from
        json_body (DeleteTeamInvitationParams):

    Returns:
        Response[DeleteTeamInvitationResponse]
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
    json_body: DeleteTeamInvitationParams,
) -> Optional[DeleteTeamInvitationResponse]:
    """Delete Team Invitation

     Delete a pending team invitation that you have previously sent

    Args:
        slug (str): The slug of the team to remove someone from
        json_body (DeleteTeamInvitationParams):

    Returns:
        Response[DeleteTeamInvitationResponse]
    """

    return (
        await asyncio_detailed(
            slug=slug,
            client=client,
            json_body=json_body,
        )
    ).parsed
