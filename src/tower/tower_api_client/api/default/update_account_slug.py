from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from ...client import AuthenticatedClient
from ...models.update_account_slug_params import UpdateAccountSlugParams
from ...models.update_account_slug_response import UpdateAccountSlugResponse
from ...types import Response


def _get_kwargs(
    slug: str,
    *,
    client: AuthenticatedClient,
    json_body: UpdateAccountSlugParams,
) -> Dict[str, Any]:
    url = "{}/accounts/{slug}".format(client.base_url, slug=slug)

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


def _parse_response(*, response: httpx.Response) -> Optional[UpdateAccountSlugResponse]:
    if response.status_code == 200:
        response_200 = UpdateAccountSlugResponse.from_dict(response.json())

        return response_200
    return None


def _build_response(*, response: httpx.Response) -> Response[UpdateAccountSlugResponse]:
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
    json_body: UpdateAccountSlugParams,
) -> Response[UpdateAccountSlugResponse]:
    """Update account slug

     Update the slug for an account

    Args:
        slug (str): The slug of the account to update
        json_body (UpdateAccountSlugParams):

    Returns:
        Response[UpdateAccountSlugResponse]
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
    json_body: UpdateAccountSlugParams,
) -> Optional[UpdateAccountSlugResponse]:
    """Update account slug

     Update the slug for an account

    Args:
        slug (str): The slug of the account to update
        json_body (UpdateAccountSlugParams):

    Returns:
        Response[UpdateAccountSlugResponse]
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
    json_body: UpdateAccountSlugParams,
) -> Response[UpdateAccountSlugResponse]:
    """Update account slug

     Update the slug for an account

    Args:
        slug (str): The slug of the account to update
        json_body (UpdateAccountSlugParams):

    Returns:
        Response[UpdateAccountSlugResponse]
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
    json_body: UpdateAccountSlugParams,
) -> Optional[UpdateAccountSlugResponse]:
    """Update account slug

     Update the slug for an account

    Args:
        slug (str): The slug of the account to update
        json_body (UpdateAccountSlugParams):

    Returns:
        Response[UpdateAccountSlugResponse]
    """

    return (
        await asyncio_detailed(
            slug=slug,
            client=client,
            json_body=json_body,
        )
    ).parsed
