from __future__ import annotations

import hashlib
import logging
import time
from concurrent.futures import Future
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from pyiceberg.catalog import Catalog

from ._context import TowerContext
from .exceptions import (
    StorageConnectionError,
    StorageError,
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


@dataclass(frozen=True, slots=True)
class _AccessCacheKey:
    name: str
    mode: str


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
            f"{source} contains the {INVALID_CREDENTIAL_SENTINEL} placeholder, "
            "not a usable Tower credential."
        )
    if not token.strip():
        raise StorageMissingAuthenticationError(
            "No Tower authentication found. Set TOWER_API_KEY or TOWER_JWT."
        )

    return token, auth_header_name, prefix


def _new_tower_control_plane_client(
    *,
    base_url: str,
    token: str,
    auth_header_name: str,
    prefix: str,
    timeout: float,
) -> AuthenticatedClient:
    return AuthenticatedClient(
        verify_ssl=True,
        base_url=base_url,
        token=token,
        auth_header_name=auth_header_name,
        prefix=prefix,
        timeout=httpx.Timeout(timeout),
        raise_on_unexpected_status=True,
    )


def _auth_hash(token: str, auth_header_name: str, prefix: str) -> str:
    presented_auth = f"{auth_header_name}\0{prefix}\0{token}"
    return hashlib.sha256(presented_auth.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class _ResolvedCatalogAccess:
    target_environment: str
    catalog_environment: str
    catalog_name: str
    catalog_uri: str
    warehouse: str
    mode: str
    oauth_token: str = field(repr=False)
    expires_at: datetime

    def is_inherited(self) -> bool:
        return self.catalog_environment != self.target_environment

    def is_usable(self, now: datetime) -> bool:
        return self.expires_at - now > CREDENTIAL_REFRESH_WINDOW

    def to_credentials(self) -> CatalogCredentials:
        return CatalogCredentials(
            catalog_uri=self.catalog_uri,
            expires_at=self.expires_at,
            mode=self.mode,
            oauth_token=self.oauth_token,
            warehouse=self.warehouse,
        )


class _StorageResolver:
    """Private Tower configuration and authentication for catalog resolution."""

    def __init__(
        self,
        *,
        environment: str | None = None,
    ) -> None:
        context = TowerContext.build()

        if environment is not None and not isinstance(environment, str):
            raise TypeError("environment must be a string or None")

        if environment is not None and not environment.strip():
            raise ValueError("environment must not be blank")

        self._target_environment: str = (
            environment or context.environment or DEFAULT_ENVIRONMENT_NAME
        )
        self._base_url: str = _api_base_url(context.tower_url)

        self._token: str
        self._auth_header_name: str
        self._auth_prefix: str
        self._token, self._auth_header_name, self._auth_prefix = _auth_from_context(
            context
        )
        self._access_cache: dict[_AccessCacheKey, _ResolvedCatalogAccess] = {}
        self._access_flights: dict[_AccessCacheKey, Future[_ResolvedCatalogAccess]] = {}
        self._access_lock: Lock = Lock()

    def _new_client(self) -> AuthenticatedClient:
        return _new_tower_control_plane_client(
            base_url=self._base_url,
            token=self._token,
            auth_header_name=self._auth_header_name,
            prefix=self._auth_prefix,
            timeout=DEFAULT_STORAGE_TIMEOUT_SECONDS,
        )

    def _resolve_catalog_access(
        self,
        name: str,
        mode: str,
    ) -> _ResolvedCatalogAccess:
        mode = _normalize_mode(mode)
        target_environment = self._target_environment
        # Host, authentication, and target are fixed for this resolver.
        cache_key = _AccessCacheKey(name=name, mode=mode)

        with self._access_lock:
            cached = self._access_cache.get(cache_key)
            if cached is not None and cached.is_usable(datetime.now(timezone.utc)):
                return cached
            _ = self._access_cache.pop(cache_key, None)

            flight = self._access_flights.get(cache_key)
            if flight is None:
                flight = Future()
                self._access_flights[cache_key] = flight
                should_vend = True
            else:
                should_vend = False

        if not should_vend:
            return flight.result()

        try:
            response = _vend_with_default_catalog_fallback(
                self,
                name,
                mode,
            )
            credentials = response.credentials
            if credentials.mode != mode:
                raise StorageError(
                    f"Tower returned {credentials.mode} credentials after "
                    f"{mode} access was requested."
                )
            if response.environment not in (
                target_environment,
                DEFAULT_ENVIRONMENT_NAME,
            ):
                raise StorageError(
                    f"Tower resolved catalog {name} from unexpected environment "
                    f"{response.environment}."
                )

            access = _ResolvedCatalogAccess(
                target_environment=target_environment,
                catalog_environment=response.environment,
                catalog_name=name,
                catalog_uri=credentials.catalog_uri,
                warehouse=credentials.warehouse,
                mode=credentials.mode,
                oauth_token=credentials.oauth_token,
                expires_at=_ensure_aware(credentials.expires_at),
            )
            cacheable = access.is_usable(datetime.now(timezone.utc))
        except BaseException as error:
            with self._access_lock:
                flight.set_exception(error)
                _ = self._access_flights.pop(cache_key, None)
            raise

        with self._access_lock:
            if cacheable:
                self._access_cache[cache_key] = access
            flight.set_result(access)
            _ = self._access_flights.pop(cache_key, None)

        return access

    def _request_catalog_credentials(
        self,
        name: str,
        mode: str,
    ) -> ErrorModel | VendCatalogCredentialsResponse | None:
        body = VendCatalogCredentialsBody(mode=_vend_mode(mode))

        try:
            with self._new_client() as client:
                return vend_catalog_credentials_api.sync(
                    name=name,
                    client=client,
                    environment=self._target_environment,
                    body=body,
                )
        except httpx.RequestError as error:
            raise StorageConnectionError(
                f"Could not connect to Tower at {self._base_url}."
            ) from error


def _api_base_url(tower_url: str) -> str:
    try:
        url = httpx.URL(tower_url)
    except (TypeError, httpx.InvalidURL) as error:
        raise ValueError(f"Invalid Tower URL: {tower_url}") from error
    if not url.is_absolute_url or url.scheme not in ("http", "https"):
        raise ValueError(f"Invalid Tower URL: {tower_url}")
    return str(url.copy_with(path="/v1", query=None, fragment=None))


@dataclass(frozen=True, slots=True)
class _CatalogTypeCacheKey:
    base_url: str
    auth_hash: str
    name: str
    environment: str


@dataclass
class _CachedCatalogType:
    catalog_type: str | None
    retry_at: float | None = None


_catalog_type_cache: dict[_CatalogTypeCacheKey, _CachedCatalogType] = {}


def get_tower_catalog(
    name: str = DEFAULT_CATALOG_NAME,
    environment: str | None = None,
    mode: str = "read",
) -> Catalog:
    """
    Load a PyIceberg REST catalog using short-lived credentials vended by Tower.
    """
    credentials = get_tower_catalog_credentials(name, environment, mode)
    return load_vended_catalog(name, credentials)


def get_tower_catalog_credentials(
    name: str = DEFAULT_CATALOG_NAME,
    environment: str | None = None,
    mode: str = "read",
) -> CatalogCredentials:
    storage_resolver = _StorageResolver(environment=environment)
    access = storage_resolver._resolve_catalog_access(name, mode)
    return access.to_credentials()


def load_vended_catalog(name: str, credentials: CatalogCredentials) -> Catalog:
    from pyiceberg.catalog import load_catalog

    return load_catalog(
        name,
        type="rest",
        uri=credentials.catalog_uri,
        warehouse=credentials.warehouse,
        token=credentials.oauth_token,
    )


def _vend_with_default_catalog_fallback(
    storage_resolver: _StorageResolver,
    name: str,
    mode: str,
) -> VendCatalogCredentialsResponse:
    environment = storage_resolver._target_environment
    result = storage_resolver._request_catalog_credentials(name, mode)
    if not _is_not_found(result):
        return _unwrap_vend_result(result, name, environment)

    if name == DEFAULT_CATALOG_NAME and environment == DEFAULT_ENVIRONMENT_NAME:
        _ensure_legacy_default_catalog(storage_resolver)
        for delay in DEFAULT_CATALOG_PROVISION_RETRY_DELAYS:
            time.sleep(delay)
            result = storage_resolver._request_catalog_credentials(name, mode)
            if not _is_not_found(result):
                return _unwrap_vend_result(result, name, environment)
            _ensure_legacy_default_catalog(storage_resolver)

        return _unwrap_vend_result(result, name, environment)

    raise RuntimeError(
        f"Tower catalog {name} does not exist in environment {environment}."
    )


def _describe_tower_catalog_type(
    ctx: TowerContext, name: str, environment: str
) -> str | None:
    if ctx.jwt is None and ctx.api_key is None:
        return None

    token, auth_header_name, prefix = _auth_from_context(ctx)
    base_url = _api_base_url(ctx.tower_url)
    auth_hash = _auth_hash(token, auth_header_name, prefix)
    cache_key = _CatalogTypeCacheKey(
        base_url=base_url,
        auth_hash=auth_hash,
        name=name,
        environment=environment,
    )
    cached = _catalog_type_cache.get(cache_key)
    if cached is not None:
        if cached.retry_at is None:
            return cached.catalog_type

        if time.monotonic() < cached.retry_at:
            return None

        _catalog_type_cache.pop(cache_key, None)

    tower_client = _new_tower_control_plane_client(
        base_url=base_url,
        token=token,
        auth_header_name=auth_header_name,
        prefix=prefix,
        timeout=CATALOG_TYPE_DESCRIBE_TIMEOUT_SECONDS,
    )

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


def _ensure_legacy_default_catalog(storage_resolver: _StorageResolver) -> None:
    try:
        with storage_resolver._new_client() as client:
            describe_default_catalog_api.sync(client=client)
    except Exception:
        # The following vend retry will surface the actionable backend/auth error.
        return


def _unwrap_vend_result(
    result: ErrorModel | VendCatalogCredentialsResponse | None,
    name: str,
    environment: str,
) -> VendCatalogCredentialsResponse:
    if isinstance(result, VendCatalogCredentialsResponse):
        return result

    if isinstance(result, ErrorModel):
        detail = _error_text(result)
        raise RuntimeError(
            f"Failed to vend credentials for Tower catalog {name} "
            f"in environment {environment}: {detail}"
        )

    raise RuntimeError(
        f"Failed to vend credentials for Tower catalog {name} "
        f"in environment {environment}."
    )


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


def _clear_catalog_type_cache() -> None:
    _catalog_type_cache.clear()
