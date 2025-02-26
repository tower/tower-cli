from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.get_run_logs_output_body import GetRunLogsOutputBody
from ...types import Response


def _get_kwargs(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Dict[str, Any]:
    url = "{}/apps/{name}/runs/{seq}/logs".format(client.base_url, name=name, seq=seq)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(*, response: httpx.Response) -> Optional[GetRunLogsOutputBody]:
    if response.status_code == 200:
        response_200 = GetRunLogsOutputBody.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[GetRunLogsOutputBody]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Response[GetRunLogsOutputBody]:
    """Get logs for a specific app run.

     Retrieves the logs associated with a particular run of an app.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Returns:
        Response[GetRunLogsOutputBody]
    """

    kwargs = _get_kwargs(
        name=name,
        seq=seq,
        client=client,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Optional[GetRunLogsOutputBody]:
    """Get logs for a specific app run.

     Retrieves the logs associated with a particular run of an app.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Returns:
        Response[GetRunLogsOutputBody]
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
) -> Response[GetRunLogsOutputBody]:
    """Get logs for a specific app run.

     Retrieves the logs associated with a particular run of an app.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Returns:
        Response[GetRunLogsOutputBody]
    """

    kwargs = _get_kwargs(
        name=name,
        seq=seq,
        client=client,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    name: str,
    seq: int,
    *,
    client: AuthenticatedClient,
) -> Optional[GetRunLogsOutputBody]:
    """Get logs for a specific app run.

     Retrieves the logs associated with a particular run of an app.

    Args:
        name (str): The name of the app to get logs for.
        seq (int): The sequence number of the run to get logs for.

    Returns:
        Response[GetRunLogsOutputBody]
    """

    return (
        await asyncio_detailed(
            name=name,
            seq=seq,
            client=client,
        )
    ).parsed
