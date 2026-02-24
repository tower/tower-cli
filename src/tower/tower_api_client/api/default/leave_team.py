from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.leave_team_response import LeaveTeamResponse
from ...types import Response


def _get_kwargs(
    name: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/teams/{name}/leave".format(
            name=quote(str(name), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | LeaveTeamResponse:
    if response.status_code == 200:
        response_200 = LeaveTeamResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | LeaveTeamResponse]:
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
) -> Response[ErrorModel | LeaveTeamResponse]:
    """Leave team

     Remove yourself from a team, if that's something you'd like to do for whatever reason. If you're the
    last member of a team, you cannot remove yourself. You should delete the team instead.

    Args:
        name (str): The name of the team to leave

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | LeaveTeamResponse]
    """

    kwargs = _get_kwargs(
        name=name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient,
) -> ErrorModel | LeaveTeamResponse | None:
    """Leave team

     Remove yourself from a team, if that's something you'd like to do for whatever reason. If you're the
    last member of a team, you cannot remove yourself. You should delete the team instead.

    Args:
        name (str): The name of the team to leave

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | LeaveTeamResponse
    """

    return sync_detailed(
        name=name,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
) -> Response[ErrorModel | LeaveTeamResponse]:
    """Leave team

     Remove yourself from a team, if that's something you'd like to do for whatever reason. If you're the
    last member of a team, you cannot remove yourself. You should delete the team instead.

    Args:
        name (str): The name of the team to leave

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | LeaveTeamResponse]
    """

    kwargs = _get_kwargs(
        name=name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
) -> ErrorModel | LeaveTeamResponse | None:
    """Leave team

     Remove yourself from a team, if that's something you'd like to do for whatever reason. If you're the
    last member of a team, you cannot remove yourself. You should delete the team instead.

    Args:
        name (str): The name of the team to leave

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | LeaveTeamResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
        )
    ).parsed
