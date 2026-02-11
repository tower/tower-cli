from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error_model import ErrorModel
from ...models.get_feature_flag_response_body import GetFeatureFlagResponseBody
from ...types import Response


def _get_kwargs(
    key: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/feature-flags/{key}".format(
            key=quote(str(key), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorModel | GetFeatureFlagResponseBody:
    if response.status_code == 200:
        response_200 = GetFeatureFlagResponseBody.from_dict(response.json())

        return response_200

    response_default = ErrorModel.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorModel | GetFeatureFlagResponseBody]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    key: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ErrorModel | GetFeatureFlagResponseBody]:
    """Get feature flag value

     Get the current value of a feature flag. Returns the flag value if enabled, or a default falsey
    value if disabled.

    Args:
        key (str): The feature flag key Example: schedules-enabled.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | GetFeatureFlagResponseBody]
    """

    kwargs = _get_kwargs(
        key=key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    key: str,
    *,
    client: AuthenticatedClient | Client,
) -> ErrorModel | GetFeatureFlagResponseBody | None:
    """Get feature flag value

     Get the current value of a feature flag. Returns the flag value if enabled, or a default falsey
    value if disabled.

    Args:
        key (str): The feature flag key Example: schedules-enabled.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | GetFeatureFlagResponseBody
    """

    return sync_detailed(
        key=key,
        client=client,
    ).parsed


async def asyncio_detailed(
    key: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ErrorModel | GetFeatureFlagResponseBody]:
    """Get feature flag value

     Get the current value of a feature flag. Returns the flag value if enabled, or a default falsey
    value if disabled.

    Args:
        key (str): The feature flag key Example: schedules-enabled.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorModel | GetFeatureFlagResponseBody]
    """

    kwargs = _get_kwargs(
        key=key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    key: str,
    *,
    client: AuthenticatedClient | Client,
) -> ErrorModel | GetFeatureFlagResponseBody | None:
    """Get feature flag value

     Get the current value of a feature flag. Returns the flag value if enabled, or a default falsey
    value if disabled.

    Args:
        key (str): The feature flag key Example: schedules-enabled.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorModel | GetFeatureFlagResponseBody
    """

    return (
        await asyncio_detailed(
            key=key,
            client=client,
        )
    ).parsed
