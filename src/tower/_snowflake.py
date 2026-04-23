"""
Snowflake integration for Tower catalogs.

This module automates the Snowflake DDL needed to consume a Tower-hosted
Polaris catalog: external volume, catalog integration, and per-table Iceberg
table definitions.

Public surface:

    tower.snowflake.get_catalog_config(catalog, environment="default")
    tower.snowflake.check_permissions(snowflake_url, ...)
    tower.snowflake.create_external_volume(catalog, *, snowflake_url, ...)
    tower.snowflake.create_catalog_integration(catalog, *, snowflake_url, ...)
    tower.snowflake.create_iceberg_tables(catalog, *, snowflake_url, ...)
    tower.snowflake.sync_catalog(catalog, snowflake_url, ...)

See TOW-1871 and the acceptance criteria on that ticket for behavior details.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Iterable
from urllib.parse import parse_qsl, unquote, urlparse

from ._context import TowerContext
from .tower_api_client import AuthenticatedClient
from .tower_api_client.api.default import export_catalogs as export_catalogs_api
from .tower_api_client.models import (
    ExportCatalogsParams,
    ExportCatalogsResponse,
)
from .tower_api_client.models.error_model import ErrorModel
from .tower_api_client.models.exported_catalog import ExportedCatalog
from .utils import crypto as _crypto

logger = logging.getLogger(__name__)

SUPPORTED_CATALOG_TYPE = "snowflake-open-catalog"

# Expected property names on a Polaris-backed Tower catalog. These map to
# fields on CatalogConfig. If the Tower API stores them under different names,
# update this dict (or pass the actual name as a keyword to the internal
# helpers). The probe script recommended in TOW-1871 should confirm these.
_POLARIS_PROPERTY_NAMES: dict[str, str] = {
    "catalog_uri": "catalog_uri",
    "catalog_name": "catalog_name",
    "default_namespace": "default_namespace",
    "oauth_client_id": "oauth_client_id",
    "oauth_client_secret": "oauth_client_secret",
    "storage_base_url": "storage_base_url",
    "storage_region": "storage_region",
    "aws_role_arn": "aws_role_arn",
    "aws_external_id": "aws_external_id",
}

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class SnowflakeError(Exception):
    """Base class for errors raised by tower.snowflake."""


class SnowflakeConnectionError(SnowflakeError):
    """Raised when the Snowflake URL can't be parsed or connected to."""


class SnowflakePermissionError(SnowflakeError):
    """Raised when a pre-flight permission check fails."""

    def __init__(self, report: "PermissionReport"):
        self.report = report
        missing = [c for c in report.checks if c.status == "missing"]
        msg = (
            f"Missing {len(missing)} Snowflake privilege(s) for role "
            f"{report.role!r}. Run the following to grant them:\n"
            + "\n".join(report.suggested_grants)
        )
        super().__init__(msg)


class CatalogConfigError(SnowflakeError):
    """Raised when the Tower catalog config can't be fetched or decrypted."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CatalogConfig:
    """Decrypted Tower catalog configuration, ready for DDL rendering."""

    name: str
    type: str
    environment: str
    # Polaris-specific fields. Populated when type == "snowflake-open-catalog".
    catalog_uri: str = ""
    catalog_name: str = ""
    default_namespace: str = ""
    oauth_client_id: str = ""
    oauth_client_secret: str = ""
    storage_base_url: str = ""
    storage_region: str = ""
    aws_role_arn: str = ""
    aws_external_id: str = ""


@dataclass(frozen=True)
class PermissionCheck:
    privilege: str
    on_object: str
    status: str  # "ok" | "missing" | "inconclusive"
    detail: str | None = None


@dataclass(frozen=True)
class PermissionReport:
    account: str
    user: str
    role: str
    warehouse: str | None
    checks: list[PermissionCheck]
    suggested_grants: list[str]

    @property
    def ok(self) -> bool:
        return not any(c.status == "missing" for c in self.checks)


@dataclass
class SyncResult:
    external_volume: str
    catalog_integration: str
    tables_created: list[str] = field(default_factory=list)
    tables_skipped: list[str] = field(default_factory=list)
    drift_warnings: list[str] = field(default_factory=list)
    permission_report: PermissionReport | None = None


def _env_client(ctx: TowerContext) -> AuthenticatedClient:
    # Mirrors _client._env_client so we don't have to import a private helper.
    tower_url = ctx.tower_url
    if not tower_url.endswith("/v1"):
        tower_url = tower_url.rstrip("/") + "/v1"

    if ctx.jwt is not None:
        return AuthenticatedClient(
            verify_ssl=False,
            base_url=tower_url,
            token=ctx.jwt,
            auth_header_name="Authorization",
            prefix="Bearer",
            raise_on_unexpected_status=True,
        )
    return AuthenticatedClient(
        verify_ssl=False,
        base_url=tower_url,
        token=ctx.api_key,
        auth_header_name="X-API-Key",
        prefix="",
        raise_on_unexpected_status=True,
    )


def _find_catalog(
    response: ExportCatalogsResponse, name: str
) -> ExportedCatalog | None:
    for c in response.catalogs:
        if c.name == name:
            return c
    return None


def _fetch_catalog_config(catalog: str, environment: str) -> CatalogConfig:
    ctx = TowerContext.build()
    client = _env_client(ctx)

    private_key, pem = _crypto.generate_keypair()

    page = 1
    found: ExportedCatalog | None = None
    while True:
        body = ExportCatalogsParams(
            public_key=pem,
            environment=environment,
            page=page,
            page_size=50,
        )
        result = export_catalogs_api.sync(client=client, body=body)
        if isinstance(result, ErrorModel):
            raise CatalogConfigError(
                f"Tower API error fetching catalogs: {result.detail or result.title}"
            )
        if result is None:
            raise CatalogConfigError("Tower API returned no response")

        found = _find_catalog(result, catalog)
        if found is not None:
            break
        if page >= result.pages.num_pages:
            break
        page += 1

    if found is None:
        raise CatalogConfigError(
            f"Catalog {catalog!r} not found in environment {environment!r}"
        )

    if found.type_ != SUPPORTED_CATALOG_TYPE:
        raise CatalogConfigError(
            f"Catalog {catalog!r} has type {found.type_!r}; only "
            f"{SUPPORTED_CATALOG_TYPE!r} is supported by tower.snowflake in v1"
        )

    decrypted: dict[str, str] = {}
    for prop in found.properties:
        try:
            decrypted[prop.name] = _crypto.decrypt(private_key, prop.encrypted_value)
        except _crypto.CryptoError as exc:
            raise CatalogConfigError(
                f"failed to decrypt property {prop.name!r}: {exc}"
            ) from exc

    def _get(field_name: str) -> str:
        api_name = _POLARIS_PROPERTY_NAMES[field_name]
        if api_name not in decrypted:
            raise CatalogConfigError(
                f"catalog {catalog!r} is missing expected property {api_name!r} "
                f"(have: {sorted(decrypted)})"
            )
        return decrypted[api_name]

    return CatalogConfig(
        name=found.name,
        type=found.type_,
        environment=found.environment,
        catalog_uri=_get("catalog_uri"),
        catalog_name=_get("catalog_name"),
        default_namespace=_get("default_namespace"),
        oauth_client_id=_get("oauth_client_id"),
        oauth_client_secret=_get("oauth_client_secret"),
        storage_base_url=_get("storage_base_url"),
        storage_region=_get("storage_region"),
        aws_role_arn=_get("aws_role_arn"),
        aws_external_id=_get("aws_external_id"),
    )


# ---------------------------------------------------------------------------
# Snowflake connection
# ---------------------------------------------------------------------------


def _parse_snowflake_url(url: str) -> dict[str, Any]:
    """Turn a SQLAlchemy-style URL into kwargs for snowflake.connector.connect."""
    parsed = urlparse(url)
    if parsed.scheme != "snowflake":
        raise SnowflakeConnectionError(
            f"snowflake_url must start with 'snowflake://', got scheme {parsed.scheme!r}"
        )

    kwargs: dict[str, Any] = {}
    if parsed.username:
        kwargs["user"] = unquote(parsed.username)
    if parsed.password:
        kwargs["password"] = unquote(parsed.password)
    if parsed.hostname:
        kwargs["account"] = parsed.hostname

    path = parsed.path.strip("/")
    if path:
        parts = path.split("/", 1)
        kwargs["database"] = parts[0]
        if len(parts) == 2 and parts[1]:
            kwargs["schema"] = parts[1]

    for k, v in parse_qsl(parsed.query):
        kwargs[k] = v

    if "account" not in kwargs:
        raise SnowflakeConnectionError("snowflake_url missing account (hostname)")
    return kwargs


def _connect(snowflake_url: str):
    try:
        import snowflake.connector
    except ImportError as exc:
        raise SnowflakeConnectionError(
            "snowflake-connector-python is required; install with "
            "`pip install \"tower[snowflake]\"`"
        ) from exc

    try:
        return snowflake.connector.connect(**_parse_snowflake_url(snowflake_url))
    except SnowflakeConnectionError:
        raise
    except Exception as exc:
        raise SnowflakeConnectionError(f"failed to connect to Snowflake: {exc}") from exc


# ---------------------------------------------------------------------------
# Identifier helpers
# ---------------------------------------------------------------------------

_UNQUOTED_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def _quote_ident(name: str) -> str:
    """Return a Snowflake identifier, quoting if it's not a plain bare word."""
    if _UNQUOTED_IDENT.match(name):
        return name
    return '"' + name.replace('"', '""') + '"'


def _quote_qualified(qualified: str) -> str:
    """Quote each dotted segment of a DB.SCHEMA[.TABLE] name."""
    return ".".join(_quote_ident(p) for p in qualified.split("."))


def _sql_string(value: str) -> str:
    """Return a Snowflake single-quoted string literal."""
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def _create_clause(force: bool, object_kind: str) -> str:
    return f"CREATE OR REPLACE {object_kind}" if force else f"CREATE {object_kind} IF NOT EXISTS"


# ---------------------------------------------------------------------------
# DDL renderers
# ---------------------------------------------------------------------------


def _storage_location_name(cfg: CatalogConfig) -> str:
    """Derive a human-friendly storage location name."""
    bucket = cfg.storage_base_url.removeprefix("s3://").rstrip("/").split("/")[0]
    if cfg.storage_region:
        return f"{bucket}-{cfg.storage_region}"
    return bucket or "tower-storage"


def render_external_volume_ddl(
    cfg: CatalogConfig, *, name: str, force: bool = False
) -> str:
    location = _storage_location_name(cfg)
    head = _create_clause(force, "EXTERNAL VOLUME")
    return (
        f"{head} {_quote_ident(name)}\n"
        f"    ALLOW_WRITES = FALSE\n"
        f"    STORAGE_LOCATIONS =\n"
        f"      (\n"
        f"         (\n"
        f"            NAME = {_sql_string(location)}\n"
        f"            STORAGE_PROVIDER = 'S3'\n"
        f"            STORAGE_BASE_URL = {_sql_string(cfg.storage_base_url)}\n"
        f"            STORAGE_AWS_ROLE_ARN = {_sql_string(cfg.aws_role_arn)}\n"
        f"            STORAGE_AWS_EXTERNAL_ID = {_sql_string(cfg.aws_external_id)}\n"
        f"         )\n"
        f"      )"
    )


def render_catalog_integration_ddl(
    cfg: CatalogConfig,
    *,
    name: str,
    catalog_namespace: str | None = None,
    force: bool = False,
) -> str:
    namespace = catalog_namespace or cfg.default_namespace
    head = _create_clause(force, "CATALOG INTEGRATION")
    return (
        f"{head} {_quote_ident(name)}\n"
        f"    CATALOG_SOURCE = POLARIS\n"
        f"    TABLE_FORMAT = ICEBERG\n"
        f"    CATALOG_NAMESPACE = {_sql_string(namespace)}\n"
        f"    REST_CONFIG = (\n"
        f"        CATALOG_URI = {_sql_string(cfg.catalog_uri)}\n"
        f"        CATALOG_NAME = {_sql_string(cfg.catalog_name)}\n"
        f"    )\n"
        f"    REST_AUTHENTICATION = (\n"
        f"        TYPE = OAUTH\n"
        f"        OAUTH_CLIENT_ID = {_sql_string(cfg.oauth_client_id)}\n"
        f"        OAUTH_CLIENT_SECRET = {_sql_string(cfg.oauth_client_secret)}\n"
        f"        OAUTH_ALLOWED_SCOPES = ( 'PRINCIPAL_ROLE:ALL' )\n"
        f"    )\n"
        f"    ENABLED = TRUE"
    )


def render_iceberg_table_ddl(
    *,
    fully_qualified_table: str,
    catalog_integration: str,
    external_volume: str,
    catalog_namespace: str,
    catalog_table_name: str,
    refresh_interval_seconds: int = 3600,
    auto_refresh: bool = True,
    force: bool = False,
) -> str:
    head = _create_clause(force, "ICEBERG TABLE")
    auto = "TRUE" if auto_refresh else "FALSE"
    return (
        f"{head} {_quote_qualified(fully_qualified_table)}\n"
        f"    CATALOG = {_sql_string(catalog_integration)}\n"
        f"    CATALOG_NAMESPACE = {_sql_string(catalog_namespace)}\n"
        f"    CATALOG_TABLE_NAME = {_sql_string(catalog_table_name)}\n"
        f"    REFRESH_INTERVAL_SECONDS = {int(refresh_interval_seconds)}\n"
        f"    AUTO_REFRESH = {auto}\n"
        f"    EXTERNAL_VOLUME = {_sql_string(external_volume)}"
    )


# ---------------------------------------------------------------------------
# Permission checks
# ---------------------------------------------------------------------------

_CHECK_INCONCLUSIVE_DETAIL = (
    "could not verify — role hierarchy traversal was incomplete or this "
    "privilege may be granted via FUTURE or a secondary role"
)


def _fetch_effective_privileges(cursor) -> tuple[set[tuple[str, str, str]], list[str]]:
    """Walk the current role's hierarchy via SHOW GRANTS.

    Returns (privileges, inconclusive_reasons). Each privilege is a tuple of
    (privilege, granted_on, name_upper). name_upper is uppercased so callers
    can compare case-insensitively.
    """
    privileges: set[tuple[str, str, str]] = set()
    inconclusive: list[str] = []

    cursor.execute("SELECT CURRENT_ROLE()")
    row = cursor.fetchone()
    starting_role = row[0] if row else None
    if not starting_role:
        inconclusive.append("no active role (CURRENT_ROLE() returned NULL)")
        return privileges, inconclusive

    visited: set[str] = set()
    queue: list[str] = [starting_role]

    while queue:
        role = queue.pop()
        role_key = role.upper()
        if role_key in visited:
            continue
        visited.add(role_key)

        try:
            cursor.execute(f"SHOW GRANTS TO ROLE {_quote_ident(role)}")
            grants = cursor.fetchall()
        except Exception as exc:  # pragma: no cover - defensive
            inconclusive.append(f"cannot SHOW GRANTS TO ROLE {role}: {exc}")
            continue

        columns = [c[0].lower() for c in cursor.description]
        for row in grants:
            record = dict(zip(columns, row))
            privilege = str(record.get("privilege", "")).upper()
            granted_on = str(record.get("granted_on", "")).upper()
            name = str(record.get("name", "")).upper()
            granted_to = str(record.get("granted_to", "")).upper()
            grantee_name = str(record.get("grantee_name", "")).upper()
            if not privilege:
                continue
            privileges.add((privilege, granted_on, name))
            # USAGE on a role = role inheritance; follow it.
            if (
                privilege == "USAGE"
                and granted_on == "ROLE"
                and granted_to == "ROLE"
                and grantee_name.upper() == role_key
            ):
                queue.append(record.get("name", ""))

    return privileges, inconclusive


def _has_privilege(
    privileges: set[tuple[str, str, str]],
    privilege: str,
    granted_on: str,
    name_upper: str | None,
) -> bool:
    """Return True if the role holds the privilege (or OWNERSHIP) on the target."""
    privilege = privilege.upper()
    granted_on = granted_on.upper()
    for p, on, n in privileges:
        if on != granted_on:
            continue
        if name_upper is not None and n != name_upper.upper():
            continue
        if p == privilege or p == "OWNERSHIP":
            return True
    return False


def _has_accountadmin(privileges: set[tuple[str, str, str]]) -> bool:
    # ACCOUNTADMIN itself shows up as USAGE ON ROLE ACCOUNTADMIN during walk.
    return any(n == "ACCOUNTADMIN" and on == "ROLE" for _, on, n in privileges)


def check_permissions(
    snowflake_url: str,
    *,
    for_external_volume: bool = True,
    for_catalog_integration: bool = True,
    for_tables_in: Iterable[str] | None = None,
) -> PermissionReport:
    """Verify the connection has the privileges needed to sync a catalog.

    See the TOW-1871 ticket for the exact privilege list. Raises
    SnowflakeConnectionError on auth/network failures — those are distinct
    from permission issues.
    """
    conn = _connect(snowflake_url)
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT CURRENT_ACCOUNT(), CURRENT_USER(), CURRENT_ROLE(), "
                "CURRENT_WAREHOUSE()"
            )
            account, user, role, warehouse = cur.fetchone()

            privileges, inconclusive_reasons = _fetch_effective_privileges(cur)
        finally:
            cur.close()
    finally:
        conn.close()

    checks: list[PermissionCheck] = []
    grants: list[str] = []
    role_ident = _quote_ident(role) if role else "<ROLE>"
    short_circuit = _has_accountadmin(privileges)

    def _record(privilege: str, target: str, on: str, name: str | None) -> None:
        if short_circuit:
            checks.append(PermissionCheck(privilege, target, "ok"))
            return
        if _has_privilege(privileges, privilege, on, name):
            checks.append(PermissionCheck(privilege, target, "ok"))
            return
        if inconclusive_reasons:
            checks.append(
                PermissionCheck(
                    privilege, target, "inconclusive", "; ".join(inconclusive_reasons)
                )
            )
            return
        checks.append(PermissionCheck(privilege, target, "missing"))
        target_clause = f"ON {target}" if target else ""
        grants.append(
            f"GRANT {privilege} {target_clause} TO ROLE {role_ident};".strip()
        )

    if for_external_volume:
        _record("CREATE EXTERNAL VOLUME", "ACCOUNT", "ACCOUNT", None)
    if for_catalog_integration:
        _record("CREATE INTEGRATION", "ACCOUNT", "ACCOUNT", None)
    for fq in for_tables_in or []:
        parts = fq.split(".")
        if len(parts) != 2:
            raise ValueError(
                f"for_tables_in entries must be DB.SCHEMA, got {fq!r}"
            )
        db, schema = parts
        db_up, schema_up = db.upper(), f"{db}.{schema}".upper()
        _record("USAGE", f"DATABASE {_quote_ident(db)}", "DATABASE", db_up)
        _record(
            "USAGE",
            f"SCHEMA {_quote_ident(db)}.{_quote_ident(schema)}",
            "SCHEMA",
            schema_up,
        )
        _record(
            "CREATE ICEBERG TABLE",
            f"SCHEMA {_quote_ident(db)}.{_quote_ident(schema)}",
            "SCHEMA",
            schema_up,
        )

    return PermissionReport(
        account=account or "",
        user=user or "",
        role=role or "",
        warehouse=warehouse,
        checks=checks,
        suggested_grants=grants,
    )


def _run_permission_check(
    snowflake_url: str,
    *,
    for_external_volume: bool,
    for_catalog_integration: bool,
    for_tables_in: Iterable[str] | None,
    skip: bool,
) -> PermissionReport | None:
    if skip:
        return None
    report = check_permissions(
        snowflake_url,
        for_external_volume=for_external_volume,
        for_catalog_integration=for_catalog_integration,
        for_tables_in=for_tables_in,
    )
    if not report.ok:
        raise SnowflakePermissionError(report)
    return report


# ---------------------------------------------------------------------------
# Public API — per-component and orchestrator
# ---------------------------------------------------------------------------


def get_catalog_config(
    catalog: str = "default", environment: str = "default"
) -> CatalogConfig:
    """Fetch and decrypt the Tower catalog config. No Snowflake needed."""
    return _fetch_catalog_config(catalog, environment)


def create_external_volume(
    catalog: str = "default",
    *,
    snowflake_url: str,
    name: str | None = None,
    environment: str = "default",
    force: bool = False,
    dry_run: bool = False,
    skip_permission_check: bool = False,
) -> str:
    """Create the Snowflake external volume backing this Tower catalog."""
    cfg = _fetch_catalog_config(catalog, environment)
    vol_name = name or f"tower_{catalog}_external_volume"
    ddl = render_external_volume_ddl(cfg, name=vol_name, force=force)

    if dry_run:
        print(ddl + ";")
        return vol_name

    _run_permission_check(
        snowflake_url,
        for_external_volume=True,
        for_catalog_integration=False,
        for_tables_in=None,
        skip=skip_permission_check,
    )

    _execute(snowflake_url, [ddl])
    return vol_name


def create_catalog_integration(
    catalog: str = "default",
    *,
    snowflake_url: str,
    name: str | None = None,
    environment: str = "default",
    catalog_namespace: str | None = None,
    force: bool = False,
    dry_run: bool = False,
    skip_permission_check: bool = False,
) -> str:
    """Create the Snowflake catalog integration pointing at this Tower catalog."""
    cfg = _fetch_catalog_config(catalog, environment)
    int_name = name or f"tower_{catalog}_catalog"
    ddl = render_catalog_integration_ddl(
        cfg, name=int_name, catalog_namespace=catalog_namespace, force=force
    )

    if dry_run:
        print(ddl + ";")
        return int_name

    _run_permission_check(
        snowflake_url,
        for_external_volume=False,
        for_catalog_integration=True,
        for_tables_in=None,
        skip=skip_permission_check,
    )

    _execute(snowflake_url, [ddl])
    return int_name


def create_iceberg_tables(
    catalog: str = "default",
    *,
    snowflake_url: str,
    external_volume: str,
    catalog_integration: str,
    environment: str = "default",
    namespaces: Iterable[str] | None = None,
    tables: Iterable[str] | None = None,
    refresh_interval_seconds: int = 3600,
    auto_refresh: bool = True,
    target_schema: str | None = None,
    force: bool = False,
    dry_run: bool = False,
    skip_permission_check: bool = False,
) -> list[str]:
    """Create Snowflake ICEBERG TABLE definitions for every table in the catalog.

    `target_schema` (``"DB.SCHEMA"``) is where the tables are created on the
    Snowflake side. When omitted, the Iceberg namespace is used verbatim as
    ``DB.SCHEMA`` — matching the shape in the TOW-1871 example.
    """
    cfg = _fetch_catalog_config(catalog, environment)
    wanted_namespaces = set(namespaces) if namespaces is not None else None
    wanted_tables = set(tables) if tables is not None else None

    iceberg_tables = _discover_tables(cfg, wanted_namespaces, wanted_tables)

    # Where do the tables land on the Snowflake side? By default, treat the
    # Iceberg namespace as DB.SCHEMA. Caller can override with target_schema.
    statements: list[str] = []
    fq_names: list[str] = []
    for namespace_str, table_name in iceberg_tables:
        if target_schema is not None:
            sf_qualified = f"{target_schema}.{table_name}"
        else:
            sf_qualified = f"{namespace_str}.{table_name}"
        statements.append(
            render_iceberg_table_ddl(
                fully_qualified_table=sf_qualified,
                catalog_integration=catalog_integration,
                external_volume=external_volume,
                catalog_namespace=namespace_str,
                catalog_table_name=table_name,
                refresh_interval_seconds=refresh_interval_seconds,
                auto_refresh=auto_refresh,
                force=force,
            )
        )
        fq_names.append(sf_qualified)

    if dry_run:
        for s in statements:
            print(s + ";")
        return fq_names

    tables_in = _schemas_for_tables(fq_names)
    _run_permission_check(
        snowflake_url,
        for_external_volume=False,
        for_catalog_integration=False,
        for_tables_in=tables_in,
        skip=skip_permission_check,
    )

    _execute(snowflake_url, statements)
    return fq_names


def sync_catalog(
    catalog: str = "default",
    snowflake_url: str | None = None,
    *,
    environment: str = "default",
    catalog_integration_name: str | None = None,
    external_volume_name: str | None = None,
    namespaces: Iterable[str] | None = None,
    tables: Iterable[str] | None = None,
    refresh_interval_seconds: int = 3600,
    auto_refresh: bool = True,
    target_schema: str | None = None,
    force: bool = False,
    dry_run: bool = False,
    skip_permission_check: bool = False,
) -> SyncResult:
    """Idempotently sync a Tower catalog into Snowflake.

    Creates the external volume, catalog integration, and per-table Iceberg
    table definitions. By default, re-runs are no-ops (CREATE IF NOT EXISTS).
    Pass force=True to flip to CREATE OR REPLACE.
    """
    if snowflake_url is None:
        raise TypeError("sync_catalog requires snowflake_url")

    cfg = _fetch_catalog_config(catalog, environment)
    vol = external_volume_name or f"tower_{catalog}_external_volume"
    integ = catalog_integration_name or f"tower_{catalog}_catalog"

    wanted_namespaces = set(namespaces) if namespaces is not None else None
    wanted_tables = set(tables) if tables is not None else None

    # Discover first so we can scope the permission check to the right schemas.
    iceberg_tables = _discover_tables(cfg, wanted_namespaces, wanted_tables)
    fq_names: list[str] = []
    table_ddls: list[str] = []
    for namespace_str, table_name in iceberg_tables:
        sf_qualified = (
            f"{target_schema}.{table_name}"
            if target_schema is not None
            else f"{namespace_str}.{table_name}"
        )
        fq_names.append(sf_qualified)
        table_ddls.append(
            render_iceberg_table_ddl(
                fully_qualified_table=sf_qualified,
                catalog_integration=integ,
                external_volume=vol,
                catalog_namespace=namespace_str,
                catalog_table_name=table_name,
                refresh_interval_seconds=refresh_interval_seconds,
                auto_refresh=auto_refresh,
                force=force,
            )
        )

    volume_ddl = render_external_volume_ddl(cfg, name=vol, force=force)
    integration_ddl = render_catalog_integration_ddl(cfg, name=integ, force=force)

    if dry_run:
        for s in [volume_ddl, integration_ddl, *table_ddls]:
            print(s + ";")
        return SyncResult(
            external_volume=vol,
            catalog_integration=integ,
            tables_created=fq_names,
        )

    report = _run_permission_check(
        snowflake_url,
        for_external_volume=True,
        for_catalog_integration=True,
        for_tables_in=_schemas_for_tables(fq_names),
        skip=skip_permission_check,
    )

    created, skipped = _execute_and_classify(
        snowflake_url, [volume_ddl, integration_ddl] + table_ddls, len(table_ddls)
    )
    # created/skipped above only tracks tables; volume and integration are
    # always listed in the result.
    tables_created = [fq_names[i] for i in created]
    tables_skipped = [fq_names[i] for i in skipped]

    return SyncResult(
        external_volume=vol,
        catalog_integration=integ,
        tables_created=tables_created,
        tables_skipped=tables_skipped,
        permission_report=report,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _schemas_for_tables(fq_names: list[str]) -> list[str]:
    schemas: set[str] = set()
    for fq in fq_names:
        parts = fq.split(".")
        if len(parts) >= 2:
            schemas.add(f"{parts[0]}.{parts[1]}")
    return sorted(schemas)


def _discover_tables(
    cfg: CatalogConfig,
    namespaces: set[str] | None,
    tables: set[str] | None,
) -> list[tuple[str, str]]:
    """Return [(namespace_str, table_name), ...] discovered via pyiceberg.

    The namespace string is rendered with '.' as the separator — matching
    Polaris conventions and the example in TOW-1871.
    """
    try:
        from pyiceberg.catalog import load_catalog as _load_catalog
    except ImportError as exc:
        raise SnowflakeError(
            "pyiceberg is required to enumerate tables; install with "
            "`pip install \"tower[snowflake]\"`"
        ) from exc

    ice_catalog = _load_catalog(
        cfg.name,
        **{
            "type": "rest",
            "uri": cfg.catalog_uri,
            "warehouse": cfg.catalog_name,
            "credential": f"{cfg.oauth_client_id}:{cfg.oauth_client_secret}",
        },
    )

    result: list[tuple[str, str]] = []
    for ns_tuple in ice_catalog.list_namespaces():
        ns_str = ".".join(ns_tuple)
        if namespaces is not None and ns_str not in namespaces:
            continue
        for tbl_tuple in ice_catalog.list_tables(ns_tuple):
            table_name = tbl_tuple[-1]
            if tables is not None and table_name not in tables:
                continue
            result.append((ns_str, table_name))
    return result


def _execute(snowflake_url: str, statements: list[str]) -> None:
    conn = _connect(snowflake_url)
    try:
        cur = conn.cursor()
        try:
            for s in statements:
                logger.info("executing Snowflake DDL: %s", s.splitlines()[0])
                cur.execute(s)
        finally:
            cur.close()
    finally:
        conn.close()


def _execute_and_classify(
    snowflake_url: str, statements: list[str], num_tables: int
) -> tuple[list[int], list[int]]:
    """Execute statements, returning (created_table_indices, skipped_table_indices).

    The first ``len(statements) - num_tables`` statements are the volume +
    integration DDLs; the remainder are table DDLs. Snowflake returns status
    text like ``"Table <name> successfully created."`` on creation, or an
    ``"... already exists, statement succeeded."`` notice when IF NOT EXISTS
    matched an existing object. We classify tables by reading the first
    column of the result set.
    """
    prefix = len(statements) - num_tables
    created: list[int] = []
    skipped: list[int] = []

    conn = _connect(snowflake_url)
    try:
        cur = conn.cursor()
        try:
            for idx, stmt in enumerate(statements):
                logger.info("executing Snowflake DDL: %s", stmt.splitlines()[0])
                cur.execute(stmt)
                if idx < prefix:
                    continue
                row = cur.fetchone() if cur.description else None
                status = str(row[0]).lower() if row else ""
                table_idx = idx - prefix
                if "already exists" in status:
                    skipped.append(table_idx)
                else:
                    created.append(table_idx)
        finally:
            cur.close()
    finally:
        conn.close()

    return created, skipped
