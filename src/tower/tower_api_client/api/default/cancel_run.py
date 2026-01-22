from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.cancel_run_response import CancelRunResponse
from ...models.error_model import ErrorModel
from ...types import Response


def _get_kwargs(
    name: str,
    seq: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/apps/{name}/runs/{seq}".format(
            name=quote(str(name), safe=""),
            seq=quote(str(seq), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CancelRunResponse | ErrorModel:
    if response.status_code == 200:
        response_200 = CancelRunResponse.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[CancelRunResponse | ErrorModel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Response[CancelRunResponse | ErrorModel]:
    """Cancel run

     Cancel a run

    Args:
        name (str): The name of the app to fetch runs for.
        seq (int): The number of the run to fetch.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CancelRunResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        name=name,
        seq=seq,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> CancelRunResponse | ErrorModel | None:
    """Cancel run

     Cancel a run

    Args:
        name (str): The name of the app to fetch runs for.
        seq (int): The number of the run to fetch.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CancelRunResponse | ErrorModel
    """

    return sync_detailed(
        name=name,
        seq=seq,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Response[CancelRunResponse | ErrorModel]:
    """Cancel run

     Cancel a run

    Args:
        name (str): The name of the app to fetch runs for.
        seq (int): The number of the run to fetch.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CancelRunResponse | ErrorModel]
    """

    kwargs = _get_kwargs(
        name=name,
        seq=seq,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> CancelRunResponse | ErrorModel | None:
    """Cancel run

     Cancel a run

    Args:
        name (str): The name of the app to fetch runs for.
        seq (int): The number of the run to fetch.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CancelRunResponse | ErrorModel
    """

    return (
        await asyncio_detailed(
            name=name,
            seq=seq,
            client=client,
        )
    ).parsed
