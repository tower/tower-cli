from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_secrets_output_body import GetSecretsOutputBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    environment: Union[Unset, str] = UNSET,
    all_: Union[Unset, bool] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["environment"] = environment

    params["all"] = all_

    params["page"] = page

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/secrets",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GetSecretsOutputBody]:
    if response.status_code == 200:
        response_200 = GetSecretsOutputBody.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GetSecretsOutputBody]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, str] = UNSET,
    all_: Union[Unset, bool] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
) -> Response[GetSecretsOutputBody]:
    """Get all secrets in your account.

     Get all secrets in your account

    Args:
        environment (Union[Unset, str]): The environment to filter by.
        all_ (Union[Unset, bool]): Whether to fetch all secrets or only the ones that are not
            marked as deleted.
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetSecretsOutputBody]
    """

    kwargs = _get_kwargs(
        environment=environment,
        all_=all_,
        page=page,
        page_size=page_size,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, str] = UNSET,
    all_: Union[Unset, bool] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
) -> Optional[GetSecretsOutputBody]:
    """Get all secrets in your account.

     Get all secrets in your account

    Args:
        environment (Union[Unset, str]): The environment to filter by.
        all_ (Union[Unset, bool]): Whether to fetch all secrets or only the ones that are not
            marked as deleted.
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetSecretsOutputBody
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
    environment: Union[Unset, str] = UNSET,
    all_: Union[Unset, bool] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
) -> Response[GetSecretsOutputBody]:
    """Get all secrets in your account.

     Get all secrets in your account

    Args:
        environment (Union[Unset, str]): The environment to filter by.
        all_ (Union[Unset, bool]): Whether to fetch all secrets or only the ones that are not
            marked as deleted.
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetSecretsOutputBody]
    """

    kwargs = _get_kwargs(
        environment=environment,
        all_=all_,
        page=page,
        page_size=page_size,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, str] = UNSET,
    all_: Union[Unset, bool] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
) -> Optional[GetSecretsOutputBody]:
    """Get all secrets in your account.

     Get all secrets in your account

    Args:
        environment (Union[Unset, str]): The environment to filter by.
        all_ (Union[Unset, bool]): Whether to fetch all secrets or only the ones that are not
            marked as deleted.
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetSecretsOutputBody
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
