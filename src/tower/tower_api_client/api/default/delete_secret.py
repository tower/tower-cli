from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_secret_response import DeleteSecretResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    environment: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["environment"] = environment

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/secrets/{name}".format(
            name=name,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[DeleteSecretResponse]:
    if response.status_code == 200:
        response_200 = DeleteSecretResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[DeleteSecretResponse]:
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
    environment: Union[Unset, str] = UNSET,
) -> Response[DeleteSecretResponse]:
    """Delete secret

     Delete a secret by name.

    Args:
        name (str): The name of the secret to delete.
        environment (Union[Unset, str]): The environment of the secret to delete.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteSecretResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        environment=environment,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, str] = UNSET,
) -> Optional[DeleteSecretResponse]:
    """Delete secret

     Delete a secret by name.

    Args:
        name (str): The name of the secret to delete.
        environment (Union[Unset, str]): The environment of the secret to delete.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteSecretResponse
    """

    return sync_detailed(
        name=name,
        client=client,
        environment=environment,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, str] = UNSET,
) -> Response[DeleteSecretResponse]:
    """Delete secret

     Delete a secret by name.

    Args:
        name (str): The name of the secret to delete.
        environment (Union[Unset, str]): The environment of the secret to delete.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteSecretResponse]
    """

    kwargs = _get_kwargs(
        name=name,
        environment=environment,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
    environment: Union[Unset, str] = UNSET,
) -> Optional[DeleteSecretResponse]:
    """Delete secret

     Delete a secret by name.

    Args:
        name (str): The name of the secret to delete.
        environment (Union[Unset, str]): The environment of the secret to delete.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteSecretResponse
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            environment=environment,
        )
    ).parsed
