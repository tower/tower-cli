from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.list_team_members_response import ListTeamMembersResponse
from ...types import Response


def _get_kwargs(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Dict[str, Any]:
    url = "{}/teams/{slug}/members".format(client.base_url, slug=slug)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, response: httpx.Response) -> Optional[ListTeamMembersResponse]:
    if response.status_code == 200:
        response_200 = ListTeamMembersResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[ListTeamMembersResponse]:
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
) -> Response[ListTeamMembersResponse]:
    """List Team Members

     List the members of a team

    Args:
        slug (str): The slug of the team to list members for

    Returns:
        Response[ListTeamMembersResponse]
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
) -> Optional[ListTeamMembersResponse]:
    """List Team Members

     List the members of a team

    Args:
        slug (str): The slug of the team to list members for

    Returns:
        Response[ListTeamMembersResponse]
    """

    return sync_detailed(
        slug=slug,
        client=client,
    ).parsed


async def asyncio_detailed(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Response[ListTeamMembersResponse]:
    """List Team Members

     List the members of a team

    Args:
        slug (str): The slug of the team to list members for

    Returns:
        Response[ListTeamMembersResponse]
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
) -> Optional[ListTeamMembersResponse]:
    """List Team Members

     List the members of a team

    Args:
        slug (str): The slug of the team to list members for

    Returns:
        Response[ListTeamMembersResponse]
    """

    return (
        await asyncio_detailed(
            slug=slug,
            client=client,
        )
    ).parsed
