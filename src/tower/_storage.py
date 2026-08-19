from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

from ._context import TowerContext
from .exceptions import (
    StorageConnectionError,
    StorageInvalidCredentialError,
    StorageMissingAuthenticationError,
)
from .tower_api_client import AuthenticatedClient
from .tower_api_client.api.default import describe_catalog as describe_catalog_api
from .tower_api_client.api.default import (
    describe_default_catalog as describe_default_catalog_api,
)
from .tower_api_client.api.default import (
    vend_catalog_credentials as vend_catalog_credentials_api,
)
from .tower_api_client.models import (
    CatalogCredentials,
    DescribeCatalogResponse,
    ErrorModel,
    VendCatalogCredentialsBody,
    VendCatalogCredentialsBodyMode,
    VendCatalogCredentialsResponse,
)
from .tower_api_client.types import UNSET, Unset

CREDENTIAL_REFRESH_WINDOW = timedelta(minutes=5)
# how long to wait for a catalog type describe request to complete
CATALOG_TYPE_DESCRIBE_TIMEOUT_SECONDS = 2.0
# only cache failed catalog type describe requests for this long
# retry only after this period
CATALOG_TYPE_FAILURE_CACHE_TTL_SECONDS = 30.0
DEFAULT_STORAGE_TIMEOUT_SECONDS = 30.0
DEFAULT_CATALOG_PROVISION_RETRY_DELAYS = (0.25, 0.5, 1.0, 2.0)
DEFAULT_CATALOG_NAME = "default"
DEFAULT_ENVIRONMENT_NAME = "default"
TOWER_CATALOG_TYPE = "tower-catalog"
INVALID_CREDENTIAL_SENTINEL = "<redacted>"
logger = logging.getLogger("tower.storage")


def _auth_from_context(context: TowerContext) -> tuple[str, str, str]:
    if context.jwt is not None:
        token = context.jwt
        auth_header_name = "Authorization"
        prefix = "Bearer"
        source = "TOWER_JWT"
    elif context.api_key is not None:
        token = context.api_key
        auth_header_name = "X-API-Key"
        prefix = ""
        source = "TOWER_API_KEY"
    else:
        raise StorageMissingAuthenticationError(
            "No Tower authentication found. Set TOWER_API_KEY or TOWER_JWT."
        )

    if token.strip() == INVALID_CREDENTIAL_SENTINEL:
        raise StorageInvalidCredentialError(
            f"{source} contains the {INVALID_CREDENTIAL_SENTINEL!r} placeholder, "
            "not a usable Tower credential."
        )
    if not token.strip():
        raise StorageMissingAuthenticationError(
            "No Tower authentication found. Set TOWER_API_KEY or TOWER_JWT."
        )

    return token, auth_header_name, prefix


def _build_tower_control_plane_client(
    *,
    context: TowerContext,
    tower_url: str,
    timeout: float,
    verify_tls: bool,
) -> tuple[str, str, AuthenticatedClient]:
    token, auth_header_name, prefix = _auth_from_context(context)
    base_url = _api_base_url(tower_url)
    # hash whatever auth token was provided so we can cache catalogs tokens per account.
    auth_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    client = AuthenticatedClient(
        verify_ssl=verify_tls,
        base_url=base_url,
        token=token,
        auth_header_name=auth_header_name,
        prefix=prefix,
        timeout=httpx.Timeout(timeout),
        raise_on_unexpected_status=True,
    )
    return base_url, auth_hash, client


class StorageClient:
    """Configuration and authenticated Tower Storage-specific client.

    This remains an internal foundation until the public catalog-loading surface is
    added. It intentionally does not alter the clients used by unrelated SDK calls.
    """

    def __init__(
        self,
        *,
        tower_url: str | None = None,
        environment: str | None = None,
        timeout: float = DEFAULT_STORAGE_TIMEOUT_SECONDS,
        verify_tls: bool = True,
    ) -> None:
        context = TowerContext.build()

        if tower_url is not None and not isinstance(tower_url, str):
            raise TypeError("tower_url must be a string or None")

        if tower_url is not None and not tower_url.strip():
            raise ValueError("tower_url must not be blank")

        if environment is not None and not isinstance(environment, str):
            raise TypeError("environment must be a string or None")

        if environment is not None and not environment.strip():
            raise ValueError("environment must not be blank")

        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise TypeError("timeout must be a positive number")

        if not 0 < float(timeout) < float("inf"):
            raise ValueError("timeout must be a positive finite number")

        if not isinstance(verify_tls, bool):
            raise TypeError("verify_tls must be a bool")

        self.tower_url = tower_url or context.tower_url
        self.environment = (
            environment or context.environment or DEFAULT_ENVIRONMENT_NAME
        )
        self.timeout = float(timeout)
        self.verify_tls = verify_tls
        self._base_url, self._auth_hash, self._tower_client = (
            _build_tower_control_plane_client(
                context=context,
                tower_url=self.tower_url,
                timeout=self.timeout,
                verify_tls=self.verify_tls,
            )
        )

    def _request_catalog_credentials(
        self,
        name: str,
        mode: str,
    ) -> ErrorModel | VendCatalogCredentialsResponse | None:
        body = VendCatalogCredentialsBody(mode=_vend_mode(mode))

        try:
            return vend_catalog_credentials_api.sync(
                name=name,
                client=self._tower_client,
                environment=self.environment,
                body=body,
            )
        except httpx.RequestError as error:
            raise StorageConnectionError(
                f"Could not connect to Tower at {self._base_url!r}."
            ) from error


def _api_base_url(tower_url: str) -> str:
    try:
        url = httpx.URL(tower_url)
    except (TypeError, httpx.InvalidURL) as error:
        raise ValueError(f"Invalid Tower URL: {tower_url!r}") from error
    if not url.is_absolute_url or url.scheme not in ("http", "https"):
        raise ValueError(f"Invalid Tower URL: {tower_url!r}")
    return str(url.copy_with(path="/v1", query=None, fragment=None)).rstrip("/")


@dataclass
class _CachedCredentials:
    credentials: CatalogCredentials

    def is_usable(self, now: datetime) -> bool:
        expires_at = _ensure_aware(self.credentials.expires_at)
        return now < expires_at - CREDENTIAL_REFRESH_WINDOW


@dataclass
class _CachedCatalogType:
    catalog_type: str | None
    retry_at: float | None = None


_credential_cache: dict[tuple[str, str, str, str, str], _CachedCredentials] = {}
_catalog_type_cache: dict[tuple[str, str, str, str], _CachedCatalogType] = {}


def get_tower_catalog(
    name: str = DEFAULT_CATALOG_NAME,
    environment: Optional[str] = None,
    mode: str = "read",
) -> Any:
    """
    Load a PyIceberg REST catalog using short-lived credentials vended by Tower.
    """
    credentials = get_tower_catalog_credentials(name, environment, mode)
    return load_vended_catalog(name, credentials)


def get_tower_catalog_credentials(
    name: str = DEFAULT_CATALOG_NAME,
    environment: Optional[str] = None,
    mode: str = "read",
) -> CatalogCredentials:
    storage_client = StorageClient(environment=environment)
    mode = _normalize_mode(mode)
    cache_key = _cache_key(storage_client, name, mode)

    now = datetime.now(timezone.utc)
    _prune_credential_cache(now)
    cached = _credential_cache.get(cache_key)
    if cached is not None and cached.is_usable(now):
        return cached.credentials

    with storage_client._tower_client:
        credentials = _vend_with_default_catalog_fallback(storage_client, name, mode)
    _credential_cache[cache_key] = _CachedCredentials(credentials)
    return credentials


def load_vended_catalog(name: str, credentials: CatalogCredentials) -> Any:
    from pyiceberg.catalog import load_catalog

    return load_catalog(
        name,
        type="rest",
        uri=credentials.catalog_uri,
        warehouse=credentials.warehouse,
        token=credentials.oauth_token,
    )


def _vend_with_default_catalog_fallback(
    storage_client: StorageClient,
    name: str,
    mode: str,
) -> CatalogCredentials:
    environment = storage_client.environment
    result = storage_client._request_catalog_credentials(name, mode)
    if not _is_not_found(result):
        return _unwrap_vend_result(result, name, environment)

    if name == DEFAULT_CATALOG_NAME and environment == DEFAULT_ENVIRONMENT_NAME:
        _ensure_legacy_default_catalog(storage_client)
        for delay in DEFAULT_CATALOG_PROVISION_RETRY_DELAYS:
            time.sleep(delay)
            result = storage_client._request_catalog_credentials(name, mode)
            if not _is_not_found(result):
                return _unwrap_vend_result(result, name, environment)
            _ensure_legacy_default_catalog(storage_client)

        return _unwrap_vend_result(result, name, environment)

    raise RuntimeError(
        f"Tower catalog {name!r} does not exist in environment {environment!r}."
    )


def _describe_tower_catalog_type(
    ctx: TowerContext, name: str, environment: str
) -> str | None:
    if ctx.jwt is None and ctx.api_key is None:
        return None

    base_url, auth_hash, tower_client = _build_tower_control_plane_client(
        context=ctx,
        tower_url=ctx.tower_url,
        timeout=CATALOG_TYPE_DESCRIBE_TIMEOUT_SECONDS,
        verify_tls=True,
    )
    cache_key = (base_url, auth_hash, name, environment)
    cached = _catalog_type_cache.get(cache_key)
    if cached is not None:
        if cached.retry_at is None:
            return cached.catalog_type

        if time.monotonic() < cached.retry_at:
            return None

        _catalog_type_cache.pop(cache_key, None)

    try:
        with tower_client:
            result = describe_catalog_api.sync(
                name=name,
                client=tower_client,
                environment=environment,
            )
    except Exception:
        logger.debug(
            "Failed to describe Tower catalog %r in environment %r; "
            "falling back to PyIceberg catalog configuration detection.",
            name,
            environment,
            exc_info=True,
        )
        _catalog_type_cache[cache_key] = _failed_catalog_type_cache_entry()
        return None

    if isinstance(result, DescribeCatalogResponse):
        catalog_type = result.catalog.type_
        _catalog_type_cache[cache_key] = _CachedCatalogType(catalog_type=catalog_type)
        return catalog_type

    if isinstance(result, ErrorModel):
        logger.debug(
            "Tower catalog describe for %r in environment %r returned %s; "
            "falling back to PyIceberg catalog configuration detection.",
            name,
            environment,
            _error_text(result),
        )

    _catalog_type_cache[cache_key] = _failed_catalog_type_cache_entry()
    return None


def _failed_catalog_type_cache_entry() -> _CachedCatalogType:
    return _CachedCatalogType(
        catalog_type=None,
        retry_at=time.monotonic() + CATALOG_TYPE_FAILURE_CACHE_TTL_SECONDS,
    )


def _ensure_legacy_default_catalog(storage_client: StorageClient) -> None:
    try:
        describe_default_catalog_api.sync(client=storage_client._tower_client)
    except Exception:
        # The following vend retry will surface the actionable backend/auth error.
        return


def _unwrap_vend_result(
    result: ErrorModel | VendCatalogCredentialsResponse | None,
    name: str,
    environment: str,
) -> CatalogCredentials:
    if isinstance(result, VendCatalogCredentialsResponse):
        return result.credentials

    if isinstance(result, ErrorModel):
        detail = _error_text(result)
        raise RuntimeError(
            f"Failed to vend credentials for Tower catalog {name!r} "
            f"in environment {environment!r}: {detail}"
        )

    raise RuntimeError(
        f"Failed to vend credentials for Tower catalog {name!r} "
        f"in environment {environment!r}."
    )


def _cache_key(
    storage_client: StorageClient,
    name: str,
    mode: str,
) -> tuple[str, str, str, str, str]:
    return (
        storage_client._base_url,
        storage_client._auth_hash,
        name,
        storage_client.environment,
        mode,
    )


def _prune_credential_cache(now: datetime) -> None:
    expired_keys = [
        key for key, cached in _credential_cache.items() if not cached.is_usable(now)
    ]
    for key in expired_keys:
        _credential_cache.pop(key, None)


def _normalize_mode(mode: str) -> str:
    if mode not in ("read", "read-write"):
        raise ValueError("mode must be 'read' or 'read-write'")
    return mode


def _vend_mode(mode: str) -> VendCatalogCredentialsBodyMode:
    return (
        VendCatalogCredentialsBodyMode.READ_WRITE
        if mode == "read-write"
        else VendCatalogCredentialsBodyMode.READ
    )


def _is_not_found(result: ErrorModel | VendCatalogCredentialsResponse | None) -> bool:
    return isinstance(result, ErrorModel) and result.status == 404


def _error_text(error: ErrorModel) -> str:
    for value in (error.detail, error.title):
        if not isinstance(value, Unset) and value:
            return str(value)
    return f"HTTP {error.status}" if error.status is not UNSET else "unknown error"


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _clear_credential_cache() -> None:
    _credential_cache.clear()
    _catalog_type_cache.clear()
