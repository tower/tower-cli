from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.export_secrets_response import ExportSecretsResponse
from ...models.export_user_secrets_params import ExportUserSecretsParams
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: ExportUserSecretsParams,
    environment: Union[Unset, str] = UNSET,
    all_: Union[Unset, bool] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["environment"] = environment

    params["all"] = all_

    params["page"] = page

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/secrets/export",
        "params": params,
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[ExportSecretsResponse]:
    if response.status_code == 200:
        response_200 = ExportSecretsResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[ExportSecretsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: ExportUserSecretsParams,
    environment: Union[Unset, str] = UNSET,
    all_: Union[Unset, bool] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
) -> Response[ExportSecretsResponse]:
    """Export secrets

     Lists all the secrets in your current account and re-encrypt them with the public key you supplied.

    Args:
        environment (Union[Unset, str]): The environment to filter by.
        all_ (Union[Unset, bool]): Whether to fetch all secrets or only the ones that are not
            marked as deleted.
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.
        body (ExportUserSecretsParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExportSecretsResponse]
    """

    kwargs = _get_kwargs(
        body=body,
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
    body: ExportUserSecretsParams,
    environment: Union[Unset, str] = UNSET,
    all_: Union[Unset, bool] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
) -> Optional[ExportSecretsResponse]:
    """Export secrets

     Lists all the secrets in your current account and re-encrypt them with the public key you supplied.

    Args:
        environment (Union[Unset, str]): The environment to filter by.
        all_ (Union[Unset, bool]): Whether to fetch all secrets or only the ones that are not
            marked as deleted.
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.
        body (ExportUserSecretsParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExportSecretsResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        environment=environment,
        all_=all_,
        page=page,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: ExportUserSecretsParams,
    environment: Union[Unset, str] = UNSET,
    all_: Union[Unset, bool] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
) -> Response[ExportSecretsResponse]:
    """Export secrets

     Lists all the secrets in your current account and re-encrypt them with the public key you supplied.

    Args:
        environment (Union[Unset, str]): The environment to filter by.
        all_ (Union[Unset, bool]): Whether to fetch all secrets or only the ones that are not
            marked as deleted.
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.
        body (ExportUserSecretsParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExportSecretsResponse]
    """

    kwargs = _get_kwargs(
        body=body,
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
    body: ExportUserSecretsParams,
    environment: Union[Unset, str] = UNSET,
    all_: Union[Unset, bool] = UNSET,
    page: Union[Unset, int] = UNSET,
    page_size: Union[Unset, int] = UNSET,
) -> Optional[ExportSecretsResponse]:
    """Export secrets

     Lists all the secrets in your current account and re-encrypt them with the public key you supplied.

    Args:
        environment (Union[Unset, str]): The environment to filter by.
        all_ (Union[Unset, bool]): Whether to fetch all secrets or only the ones that are not
            marked as deleted.
        page (Union[Unset, int]): The page number to fetch.
        page_size (Union[Unset, int]): The number of records to fetch on each page.
        body (ExportUserSecretsParams):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExportSecretsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            environment=environment,
            all_=all_,
            page=page,
            page_size=page_size,
        )
    ).parsed
