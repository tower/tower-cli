from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.update_team_params import UpdateTeamParams
from ...models.update_team_response import UpdateTeamResponse
from ...types import Response


def _get_kwargs(
    slug: str,
    *,
    client: AuthenticatedClient,
    json_body: UpdateTeamParams,
) -> Dict[str, Any]:
    url = "{}/teams/{slug}".format(client.base_url, slug=slug)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    json_json_body = json_body.to_dict()

    return {
        "method": "put",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
    }


def _parse_response(*, response: httpx.Response) -> Optional[UpdateTeamResponse]:
    if response.status_code == 200:
        response_200 = UpdateTeamResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[UpdateTeamResponse]:
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
    json_body: UpdateTeamParams,
) -> Response[UpdateTeamResponse]:
    """Update Team

     Update a team with a new name or slug. Note that updating the team with a new slug will cause all
    your URLs to change!

    Args:
        slug (str): The slug of the team to update
        json_body (UpdateTeamParams):

    Returns:
        Response[UpdateTeamResponse]
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
    json_body: UpdateTeamParams,
) -> Optional[UpdateTeamResponse]:
    """Update Team

     Update a team with a new name or slug. Note that updating the team with a new slug will cause all
    your URLs to change!

    Args:
        slug (str): The slug of the team to update
        json_body (UpdateTeamParams):

    Returns:
        Response[UpdateTeamResponse]
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
    json_body: UpdateTeamParams,
) -> Response[UpdateTeamResponse]:
    """Update Team

     Update a team with a new name or slug. Note that updating the team with a new slug will cause all
    your URLs to change!

    Args:
        slug (str): The slug of the team to update
        json_body (UpdateTeamParams):

    Returns:
        Response[UpdateTeamResponse]
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
    json_body: UpdateTeamParams,
) -> Optional[UpdateTeamResponse]:
    """Update Team

     Update a team with a new name or slug. Note that updating the team with a new slug will cause all
    your URLs to change!

    Args:
        slug (str): The slug of the team to update
        json_body (UpdateTeamParams):

    Returns:
        Response[UpdateTeamResponse]
    """

    return (
        await asyncio_detailed(
            slug=slug,
            client=client,
            json_body=json_body,
        )
    ).parsed
