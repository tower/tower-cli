from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ...client import AuthenticatedClient
from ...models.export_secrets_response import ExportSecretsResponse
from ...models.export_user_secrets_params import ExportUserSecretsParams
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    client: AuthenticatedClient,
    json_body: ExportUserSecretsParams,
    environment: Union[Unset, None, str] = UNSET,
    all_: Union[Unset, None, bool] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Dict[str, Any]:
    url = "{}/secrets/export".format(client.base_url)

    headers: Dict[str, str] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    params: Dict[str, Any] = {}
    params["environment"] = environment

    params["all"] = all_

    params["page"] = page

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    json_json_body = json_body.to_dict()

    return {
        "method": "get",
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
        "params": params,
    }


def _parse_response(*, response: httpx.Response) -> Optional[ExportSecretsResponse]:
    if response.status_code == 200:
        response_200 = ExportSecretsResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[ExportSecretsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    json_body: ExportUserSecretsParams,
    environment: Union[Unset, None, str] = UNSET,
    all_: Union[Unset, None, bool] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Response[ExportSecretsResponse]:
    """Export secrets

     Lists all the secrets in your current account and re-encrypt them with the public key you supplied.

    Args:
        environment (Union[Unset, None, str]): The environment to filter by.
        all_ (Union[Unset, None, bool]): Whether to fetch all secrets or only the ones that are
            not marked as deleted.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.
        json_body (ExportUserSecretsParams):

    Returns:
        Response[ExportSecretsResponse]
    """

    kwargs = _get_kwargs(
        client=client,
        json_body=json_body,
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
    json_body: ExportUserSecretsParams,
    environment: Union[Unset, None, str] = UNSET,
    all_: Union[Unset, None, bool] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Optional[ExportSecretsResponse]:
    """Export secrets

     Lists all the secrets in your current account and re-encrypt them with the public key you supplied.

    Args:
        environment (Union[Unset, None, str]): The environment to filter by.
        all_ (Union[Unset, None, bool]): Whether to fetch all secrets or only the ones that are
            not marked as deleted.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.
        json_body (ExportUserSecretsParams):

    Returns:
        Response[ExportSecretsResponse]
    """

    return sync_detailed(
        client=client,
        json_body=json_body,
        environment=environment,
        all_=all_,
        page=page,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    json_body: ExportUserSecretsParams,
    environment: Union[Unset, None, str] = UNSET,
    all_: Union[Unset, None, bool] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Response[ExportSecretsResponse]:
    """Export secrets

     Lists all the secrets in your current account and re-encrypt them with the public key you supplied.

    Args:
        environment (Union[Unset, None, str]): The environment to filter by.
        all_ (Union[Unset, None, bool]): Whether to fetch all secrets or only the ones that are
            not marked as deleted.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.
        json_body (ExportUserSecretsParams):

    Returns:
        Response[ExportSecretsResponse]
    """

    kwargs = _get_kwargs(
        client=client,
        json_body=json_body,
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
    json_body: ExportUserSecretsParams,
    environment: Union[Unset, None, str] = UNSET,
    all_: Union[Unset, None, bool] = UNSET,
    page: Union[Unset, None, int] = UNSET,
    page_size: Union[Unset, None, int] = UNSET,
) -> Optional[ExportSecretsResponse]:
    """Export secrets

     Lists all the secrets in your current account and re-encrypt them with the public key you supplied.

    Args:
        environment (Union[Unset, None, str]): The environment to filter by.
        all_ (Union[Unset, None, bool]): Whether to fetch all secrets or only the ones that are
            not marked as deleted.
        page (Union[Unset, None, int]): The page number to fetch.
        page_size (Union[Unset, None, int]): The number of records to fetch on each page.
        json_body (ExportUserSecretsParams):

    Returns:
        Response[ExportSecretsResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            json_body=json_body,
            environment=environment,
            all_=all_,
            page=page,
            page_size=page_size,
        )
    ).parsed
