from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.remove_team_member_params import RemoveTeamMemberParams
from ...models.remove_team_member_response import RemoveTeamMemberResponse
from ...types import Response


def _get_kwargs(
    slug: str,
    *,
    client: AuthenticatedClient,
    json_body: RemoveTeamMemberParams,
) -> Dict[str, Any]:
    url = "{}/teams/{slug}/members".format(client.base_url, slug=slug)

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


def _parse_response(*, response: httpx.Response) -> Optional[RemoveTeamMemberResponse]:
    if response.status_code == 200:
        response_200 = RemoveTeamMemberResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[RemoveTeamMemberResponse]:
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
    json_body: RemoveTeamMemberParams,
) -> Response[RemoveTeamMemberResponse]:
    """Remove Team Member

     Remove a new team

    Args:
        slug (str): The slug of the team to remove someone from
        json_body (RemoveTeamMemberParams):

    Returns:
        Response[RemoveTeamMemberResponse]
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
    json_body: RemoveTeamMemberParams,
) -> Optional[RemoveTeamMemberResponse]:
    """Remove Team Member

     Remove a new team

    Args:
        slug (str): The slug of the team to remove someone from
        json_body (RemoveTeamMemberParams):

    Returns:
        Response[RemoveTeamMemberResponse]
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
    json_body: RemoveTeamMemberParams,
) -> Response[RemoveTeamMemberResponse]:
    """Remove Team Member

     Remove a new team

    Args:
        slug (str): The slug of the team to remove someone from
        json_body (RemoveTeamMemberParams):

    Returns:
        Response[RemoveTeamMemberResponse]
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
    json_body: RemoveTeamMemberParams,
) -> Optional[RemoveTeamMemberResponse]:
    """Remove Team Member

     Remove a new team

    Args:
        slug (str): The slug of the team to remove someone from
        json_body (RemoveTeamMemberParams):

    Returns:
        Response[RemoveTeamMemberResponse]
    """

    return (
        await asyncio_detailed(
            slug=slug,
            client=client,
            json_body=json_body,
        )
    ).parsed
