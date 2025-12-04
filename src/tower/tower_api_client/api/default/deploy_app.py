from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.deploy_app_json_body import DeployAppJsonBody
from ...models.deploy_app_response import DeployAppResponse
from ...models.error_model import ErrorModel
from ...types import UNSET, File, Response, Unset


def _get_kwargs(
    name: str,
    *,
    body: Union[
        DeployAppJsonBody,
        File,
    ],
    x_tower_checksum_sha256: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_tower_checksum_sha256, Unset):
        headers["X-Tower-Checksum-SHA256"] = x_tower_checksum_sha256

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/apps/{name}/deploy".format(
            name=name,
        ),
    }

    if isinstance(body, DeployAppJsonBody):
        _json_body = body.to_dict()

        _kwargs["json"] = _json_body
        headers["Content-Type"] = "application/json"
    if isinstance(body, File):
        _content_body = body.payload

        _kwargs["content"] = _content_body
        headers["Content-Type"] = "application/octet-stream"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[DeployAppResponse, ErrorModel]]:
    if response.status_code == 201:
        response_201 = DeployAppResponse.from_dict(response.json())

        return response_201
    if response.status_code == 400:
        response_400 = ErrorModel.from_dict(response.json())

        return response_400
    if response.status_code == 422:
        response_422 = ErrorModel.from_dict(response.json())

        return response_422
    if response.status_code == 500:
        response_500 = ErrorModel.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[DeployAppResponse, ErrorModel]]:
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
    body: Union[
        DeployAppJsonBody,
        File,
    ],
    x_tower_checksum_sha256: Union[Unset, str] = UNSET,
) -> Response[Union[DeployAppResponse, ErrorModel]]:
    """Deploy app

     Deploy a new version of an app. Accepts either a TAR file upload (application/tar) or a JSON body
    with source_uri (application/json) for deploying from a GitHub repository.

    Args:
        name (str): The name of the app to deploy.
        x_tower_checksum_sha256 (Union[Unset, str]): The SHA256 hash of the content, used to
            verify integrity.
        body (DeployAppJsonBody):  Example: {'source_uri': 'https://github.com/tower/tower-
            examples/tree/main/01-hello-world'}.
        body (File): A .tar or .tar.gz file containing the code to deploy and MANIFEST Example:
            <binary tar file stream>.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DeployAppResponse, ErrorModel]]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        x_tower_checksum_sha256=x_tower_checksum_sha256,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient,
    body: Union[
        DeployAppJsonBody,
        File,
    ],
    x_tower_checksum_sha256: Union[Unset, str] = UNSET,
) -> Optional[Union[DeployAppResponse, ErrorModel]]:
    """Deploy app

     Deploy a new version of an app. Accepts either a TAR file upload (application/tar) or a JSON body
    with source_uri (application/json) for deploying from a GitHub repository.

    Args:
        name (str): The name of the app to deploy.
        x_tower_checksum_sha256 (Union[Unset, str]): The SHA256 hash of the content, used to
            verify integrity.
        body (DeployAppJsonBody):  Example: {'source_uri': 'https://github.com/tower/tower-
            examples/tree/main/01-hello-world'}.
        body (File): A .tar or .tar.gz file containing the code to deploy and MANIFEST Example:
            <binary tar file stream>.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DeployAppResponse, ErrorModel]
    """

    return sync_detailed(
        name=name,
        client=client,
        body=body,
        x_tower_checksum_sha256=x_tower_checksum_sha256,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient,
    body: Union[
        DeployAppJsonBody,
        File,
    ],
    x_tower_checksum_sha256: Union[Unset, str] = UNSET,
) -> Response[Union[DeployAppResponse, ErrorModel]]:
    """Deploy app

     Deploy a new version of an app. Accepts either a TAR file upload (application/tar) or a JSON body
    with source_uri (application/json) for deploying from a GitHub repository.

    Args:
        name (str): The name of the app to deploy.
        x_tower_checksum_sha256 (Union[Unset, str]): The SHA256 hash of the content, used to
            verify integrity.
        body (DeployAppJsonBody):  Example: {'source_uri': 'https://github.com/tower/tower-
            examples/tree/main/01-hello-world'}.
        body (File): A .tar or .tar.gz file containing the code to deploy and MANIFEST Example:
            <binary tar file stream>.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DeployAppResponse, ErrorModel]]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        x_tower_checksum_sha256=x_tower_checksum_sha256,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient,
    body: Union[
        DeployAppJsonBody,
        File,
    ],
    x_tower_checksum_sha256: Union[Unset, str] = UNSET,
) -> Optional[Union[DeployAppResponse, ErrorModel]]:
    """Deploy app

     Deploy a new version of an app. Accepts either a TAR file upload (application/tar) or a JSON body
    with source_uri (application/json) for deploying from a GitHub repository.

    Args:
        name (str): The name of the app to deploy.
        x_tower_checksum_sha256 (Union[Unset, str]): The SHA256 hash of the content, used to
            verify integrity.
        body (DeployAppJsonBody):  Example: {'source_uri': 'https://github.com/tower/tower-
            examples/tree/main/01-hello-world'}.
        body (File): A .tar or .tar.gz file containing the code to deploy and MANIFEST Example:
            <binary tar file stream>.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DeployAppResponse, ErrorModel]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
            x_tower_checksum_sha256=x_tower_checksum_sha256,
        )
    ).parsed
