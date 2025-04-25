from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.leave_team_response import LeaveTeamResponse
from ...types import Response


def _get_kwargs(
    slug: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/teams/{slug}/leave".format(
            slug=slug,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[LeaveTeamResponse]:
    if response.status_code == 200:
        response_200 = LeaveTeamResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[LeaveTeamResponse]:
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
) -> Response[LeaveTeamResponse]:
    """Leave team

     Remove yourself from a team, if that's something you'd like to do for whatever reason. If you're the
    last member of a team, you cannot remove yourself. You should delete the team instead.

    Args:
        slug (str): The slug of the team to leave

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[LeaveTeamResponse]
    """

    kwargs = _get_kwargs(
        slug=slug,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Optional[LeaveTeamResponse]:
    """Leave team

     Remove yourself from a team, if that's something you'd like to do for whatever reason. If you're the
    last member of a team, you cannot remove yourself. You should delete the team instead.

    Args:
        slug (str): The slug of the team to leave

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        LeaveTeamResponse
    """

    return sync_detailed(
        slug=slug,
        client=client,
    ).parsed


async def asyncio_detailed(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Response[LeaveTeamResponse]:
    """Leave team

     Remove yourself from a team, if that's something you'd like to do for whatever reason. If you're the
    last member of a team, you cannot remove yourself. You should delete the team instead.

    Args:
        slug (str): The slug of the team to leave

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[LeaveTeamResponse]
    """

    kwargs = _get_kwargs(
        slug=slug,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    slug: str,
    *,
    client: AuthenticatedClient,
) -> Optional[LeaveTeamResponse]:
    """Leave team

     Remove yourself from a team, if that's something you'd like to do for whatever reason. If you're the
    last member of a team, you cannot remove yourself. You should delete the team instead.

    Args:
        slug (str): The slug of the team to leave

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        LeaveTeamResponse
    """

    return (
        await asyncio_detailed(
            slug=slug,
            client=client,
        )
    ).parsed
