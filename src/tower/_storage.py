"""Tower-vended Iceberg catalogs.

A Tower-managed catalog is a REST catalog reached with short-lived credentials
that Tower vends on demand. Read top to bottom: decide whether a catalog is
Tower-managed, vend credentials for it (cached until they near expiry), and
load a PyIceberg catalog from them. The one wrinkle is the default catalog,
which is provisioned lazily on first use and needs a short retry loop.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ._client import _env_client
from ._context import TowerContext
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
DEFAULT_CATALOG_PROVISION_RETRY_DELAYS = (0.25, 0.5, 1.0, 2.0)
DEFAULT_CATALOG_NAME = "default"
DEFAULT_ENVIRONMENT_NAME = "default"
TOWER_CATALOG_TYPE = "tower-catalog"

_credential_cache: dict[tuple, CatalogCredentials] = {}
_catalog_type_cache: dict[tuple, str | None] = {}


def tower_manages_catalog(ctx: TowerContext, name: str) -> bool:
    """Tower-managed catalogs vend credentials; bring-your-own catalogs such as
    S3 Tables keep the PyIceberg config the runner already injected."""
    catalog_type = _catalog_type(ctx, name)
    if catalog_type is not None:
        return catalog_type == TOWER_CATALOG_TYPE

    return not _has_pyiceberg_config(name)


def get_tower_catalog(
    name: str = DEFAULT_CATALOG_NAME,
    environment: Optional[str] = None,
    mode: str = "read",
) -> Any:
    """
    Load a PyIceberg REST catalog using short-lived credentials vended by Tower.
    """
    return load_vended_catalog(
        name, get_tower_catalog_credentials(name, environment, mode)
    )


def get_tower_catalog_credentials(
    name: str = DEFAULT_CATALOG_NAME,
    environment: Optional[str] = None,
    mode: str = "read",
) -> CatalogCredentials:
    if mode not in ("read", "read-write"):
        raise ValueError("mode must be 'read' or 'read-write'")

    ctx = TowerContext.build()
    environment = environment or ctx.environment or DEFAULT_ENVIRONMENT_NAME

    for stale in [key for key, creds in _credential_cache.items() if not _fresh(creds)]:
        del _credential_cache[stale]

    key = (ctx.tower_url, ctx.api_key or ctx.jwt or "", name, environment, mode)
    credentials = _credential_cache.get(key)
    if credentials is None:
        credentials = _vend(ctx, name, environment, mode)
        _credential_cache[key] = credentials
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


def _fresh(credentials: CatalogCredentials) -> bool:
    expires_at = credentials.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) < expires_at - CREDENTIAL_REFRESH_WINDOW


def _vend(
    ctx: TowerContext, name: str, environment: str, mode: str
) -> CatalogCredentials:
    credentials = _try_vend(ctx, name, environment, mode)
    if credentials is not None:
        return credentials

    if (name, environment) != (DEFAULT_CATALOG_NAME, DEFAULT_ENVIRONMENT_NAME):
        raise RuntimeError(
            f"Tower catalog {name!r} does not exist in environment {environment!r}."
        )

    # The default catalog is provisioned lazily on first use: describing it
    # kicks off provisioning, then we wait and try vending again.
    for delay in DEFAULT_CATALOG_PROVISION_RETRY_DELAYS:
        _provision_default_catalog(ctx)
        time.sleep(delay)
        credentials = _try_vend(ctx, name, environment, mode)
        if credentials is not None:
            return credentials

    raise RuntimeError(
        f"Tower catalog {name!r} could not be provisioned "
        f"in environment {environment!r}."
    )


def _try_vend(
    ctx: TowerContext, name: str, environment: str, mode: str
) -> Optional[CatalogCredentials]:
    """Ask Tower to vend credentials. None means the catalog does not exist (yet)."""
    if not (ctx.api_key or ctx.jwt):
        raise RuntimeError(
            "No Tower authentication found. Set TOWER_API_KEY or TOWER_JWT."
        )

    body_mode = (
        VendCatalogCredentialsBodyMode.READ_WRITE
        if mode == "read-write"
        else VendCatalogCredentialsBodyMode.READ
    )
    result = vend_catalog_credentials_api.sync(
        name=name,
        client=_env_client(ctx),
        environment=environment,
        body=VendCatalogCredentialsBody(mode=body_mode),
    )

    if isinstance(result, VendCatalogCredentialsResponse):
        return result.credentials
    if isinstance(result, ErrorModel) and result.status == 404:
        return None
    raise RuntimeError(
        f"Failed to vend credentials for Tower catalog {name!r} "
        f"in environment {environment!r}: {_error_text(result)}"
    )


def _provision_default_catalog(ctx: TowerContext) -> None:
    try:
        describe_default_catalog_api.sync_detailed(client=_env_client(ctx))
    except Exception:
        # The following vend retry will surface the actionable backend/auth error.
        pass


def _error_text(error: ErrorModel | None) -> str:
    if isinstance(error, ErrorModel):
        for value in (error.detail, error.title):
            if not isinstance(value, Unset) and value:
                return str(value)
        if error.status is not UNSET:
            return f"HTTP {error.status}"
    return "unknown error"


def _catalog_type(ctx: TowerContext, name: str) -> str | None:
    if not (ctx.api_key or ctx.jwt):
        return None

    key = (ctx.tower_url, name, ctx.environment)
    if key in _catalog_type_cache:
        return _catalog_type_cache[key]

    try:
        result = describe_catalog_api.sync(
            name=name,
            client=_env_client(ctx),
            environment=ctx.environment,
        )
    except Exception:
        return None

    catalog_type = (
        result.catalog.type_ if isinstance(result, DescribeCatalogResponse) else None
    )
    _catalog_type_cache[key] = catalog_type
    return catalog_type


def _has_pyiceberg_config(name: str) -> bool:
    try:
        from pyiceberg.catalog import _ENV_CONFIG

        if _ENV_CONFIG.get_catalog_config(name) is not None:
            return True
    except Exception:
        pass

    env_name = name.replace("-", "_").replace(".", "_").replace(":", "_").upper()
    prefix = f"PYICEBERG_CATALOG__{env_name}__"
    return any(key.upper().startswith(prefix) for key in os.environ)


def _clear_credential_cache() -> None:
    _credential_cache.clear()
    _catalog_type_cache.clear()
