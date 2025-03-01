from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.list_secrets_response import ListSecretsResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, None, str] = UNSET,
    all_: Union[Unset, None, bool] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Dict[str, Any]:
    url = "{}/secrets".format(client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    params: Dict[str, Any] = {}
    params["environment"] = environment

    params["all"] = all_

    params["page"] = page

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(*, response: httpx.Response) -> Optional[ListSecretsResponse]:
    if response.status_code == 200:
        response_200 = ListSecretsResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[ListSecretsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, None, str] = UNSET,
    all_: Union[Unset, None, bool] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Response[ListSecretsResponse]:
    """List secrets

     Lists all the secrets associated with your current account.

    Args:
        environment (Union[Unset, None, str]): The environment to filter by.
        all_ (Union[Unset, None, bool]): Whether to fetch all secrets or only the ones that are
            not marked as deleted.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.

    Returns:
        Response[ListSecretsResponse]
    """

    kwargs = _get_kwargs(
        client=client,
        environment=environment,
        all_=all_,
        page=page,
        page_size=page_size,
    )

    response = httpx.request(
        verify=client.verify_ssl,
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, None, str] = UNSET,
    all_: Union[Unset, None, bool] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Optional[ListSecretsResponse]:
    """List secrets

     Lists all the secrets associated with your current account.

    Args:
        environment (Union[Unset, None, str]): The environment to filter by.
        all_ (Union[Unset, None, bool]): Whether to fetch all secrets or only the ones that are
            not marked as deleted.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.

    Returns:
        Response[ListSecretsResponse]
    """

    return sync_detailed(
        client=client,
        environment=environment,
        all_=all_,
        page=page,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, None, str] = UNSET,
    all_: Union[Unset, None, bool] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Response[ListSecretsResponse]:
    """List secrets

     Lists all the secrets associated with your current account.

    Args:
        environment (Union[Unset, None, str]): The environment to filter by.
        all_ (Union[Unset, None, bool]): Whether to fetch all secrets or only the ones that are
            not marked as deleted.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.

    Returns:
        Response[ListSecretsResponse]
    """

    kwargs = _get_kwargs(
        client=client,
        environment=environment,
        all_=all_,
        page=page,
        page_size=page_size,
    )

    async with httpx.AsyncClient(verify=client.verify_ssl) as _client:
        response = await _client.request(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, None, str] = UNSET,
    all_: Union[Unset, None, bool] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Optional[ListSecretsResponse]:
    """List secrets

     Lists all the secrets associated with your current account.

    Args:
        environment (Union[Unset, None, str]): The environment to filter by.
        all_ (Union[Unset, None, bool]): Whether to fetch all secrets or only the ones that are
            not marked as deleted.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.

    Returns:
        Response[ListSecretsResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            environment=environment,
            all_=all_,
            page=page,
            page_size=page_size,
        )
    ).parsed
