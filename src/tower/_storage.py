from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import Any, Optional

from ._client import _env_client
from ._context import TowerContext
from .tower_api_client.api.default import (
    describe_default_catalog as describe_default_catalog_api,
)
from .tower_api_client.api.default import (
    vend_catalog_credentials as vend_catalog_credentials_api,
)
from .tower_api_client.models import (
    CatalogCredentials,
    ErrorModel,
    VendCatalogCredentialsBody,
    VendCatalogCredentialsBodyMode,
    VendCatalogCredentialsResponse,
)
from .tower_api_client.types import UNSET, Unset

CREDENTIAL_REFRESH_WINDOW = timedelta(minutes=5)
DEFAULT_CATALOG_PROVISION_RETRY_DELAYS = (0.25, 0.5, 1.0, 2.0)
DEFAULT_CATALOG_NAME = "default"
DEFAULT_ENVIRONMENT_NAME = "default"


@dataclass
class _CachedCredentials:
    credentials: CatalogCredentials

    def is_usable(self, now: datetime) -> bool:
        expires_at = _ensure_aware(self.credentials.expires_at)
        return now < expires_at - CREDENTIAL_REFRESH_WINDOW


_credential_cache: dict[tuple[str, str, str, str, str], _CachedCredentials] = {}


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
    ctx = TowerContext.build()
    environment = environment or ctx.environment or DEFAULT_ENVIRONMENT_NAME
    mode = _normalize_mode(mode)
    cache_key = _cache_key(ctx, name, environment, mode)

    now = datetime.now(timezone.utc)
    _prune_credential_cache(now)
    cached = _credential_cache.get(cache_key)
    if cached is not None and cached.is_usable(now):
        return cached.credentials

    credentials = _vend_with_default_catalog_fallback(ctx, name, environment, mode)
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
    ctx: TowerContext, name: str, environment: str, mode: str
) -> CatalogCredentials:
    result = _vend_catalog_credentials(ctx, name, environment, mode)
    if not _is_not_found(result):
        return _unwrap_vend_result(result, name, environment)

    if name == DEFAULT_CATALOG_NAME and environment == DEFAULT_ENVIRONMENT_NAME:
        _ensure_legacy_default_catalog(ctx)
        for delay in DEFAULT_CATALOG_PROVISION_RETRY_DELAYS:
            time.sleep(delay)
            result = _vend_catalog_credentials(ctx, name, environment, mode)
            if not _is_not_found(result):
                return _unwrap_vend_result(result, name, environment)
            _ensure_legacy_default_catalog(ctx)

        return _unwrap_vend_result(result, name, environment)

    raise RuntimeError(
        f"Tower catalog {name!r} does not exist in environment {environment!r}."
    )


def _vend_catalog_credentials(
    ctx: TowerContext, name: str, environment: str, mode: str
) -> ErrorModel | VendCatalogCredentialsResponse | None:
    _ensure_tower_auth(ctx)
    body = VendCatalogCredentialsBody(mode=_vend_mode(mode))
    return vend_catalog_credentials_api.sync(
        name=name,
        client=_env_client(ctx),
        environment=environment,
        body=body,
    )


def _ensure_legacy_default_catalog(ctx: TowerContext) -> None:
    try:
        response = describe_default_catalog_api.sync_detailed(client=_env_client(ctx))
        if response.status_code not in (HTTPStatus.OK, HTTPStatus.ACCEPTED):
            return
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


def _ensure_tower_auth(ctx: TowerContext) -> None:
    if ctx.api_key or ctx.jwt:
        return

    raise RuntimeError("No Tower authentication found. Set TOWER_API_KEY or TOWER_JWT.")


def _cache_key(
    ctx: TowerContext, name: str, environment: str, mode: str
) -> tuple[str, str, str, str, str]:
    token = ctx.api_key or ctx.jwt or ""
    principal_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return (ctx.tower_url, principal_hash, name, environment, mode)


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
