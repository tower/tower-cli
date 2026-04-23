"""Unit tests for tower._snowflake.

Covers DDL renderers, Snowflake URL parsing, the permission-check role walker
against a mocked Snowflake cursor, and the sync_catalog orchestrator. Crypto
layout is covered by tests/tower/test_crypto.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tower import _snowflake as sf
from tower._snowflake import (
    CatalogConfig,
    PermissionCheck,
    PermissionReport,
    SnowflakeConnectionError,
    SnowflakePermissionError,
    SyncResult,
    _has_privilege,
    _parse_snowflake_url,
    check_permissions,
    create_catalog_integration,
    create_external_volume,
    create_iceberg_tables,
    render_catalog_integration_ddl,
    render_external_volume_ddl,
    render_iceberg_table_ddl,
    sync_catalog,
)


@pytest.fixture
def polaris_config() -> CatalogConfig:
    return CatalogConfig(
        name="default",
        type="snowflake-open-catalog",
        environment="default",
        catalog_uri="https://jhhgkvi-tower.snowflakecomputing.com/polaris/api/catalog",
        catalog_name="tower-lakehouse-001",
        default_namespace="default",
        oauth_client_id="CLIENT_ID",
        oauth_client_secret="CLIENT_SECRET",
        storage_base_url="s3://tower-lakehouse-001/",
        storage_region="eu-central-1",
        aws_role_arn="arn:aws:iam::248189900669:role/tower-lakehouse-001-snowflake-role",
        aws_external_id="ABC123",
    )


# ---------------------------------------------------------------------------
# DDL renderers
# ---------------------------------------------------------------------------


class TestRenderers:
    def test_external_volume_if_not_exists_by_default(self, polaris_config):
        ddl = render_external_volume_ddl(
            polaris_config, name="tower_default_external_volume"
        )
        assert ddl.startswith("CREATE EXTERNAL VOLUME IF NOT EXISTS tower_default_external_volume")
        assert "ALLOW_WRITES = FALSE" in ddl
        assert "NAME = 'tower-lakehouse-001-eu-central-1'" in ddl
        assert "STORAGE_PROVIDER = 'S3'" in ddl
        assert "STORAGE_BASE_URL = 's3://tower-lakehouse-001/'" in ddl
        assert "STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::248189900669:role/tower-lakehouse-001-snowflake-role'" in ddl
        assert "STORAGE_AWS_EXTERNAL_ID = 'ABC123'" in ddl

    def test_external_volume_force_uses_or_replace(self, polaris_config):
        ddl = render_external_volume_ddl(polaris_config, name="vol", force=True)
        assert ddl.startswith("CREATE OR REPLACE EXTERNAL VOLUME vol")

    def test_catalog_integration_default_namespace(self, polaris_config):
        ddl = render_catalog_integration_ddl(polaris_config, name="tower_default_catalog")
        assert ddl.startswith("CREATE CATALOG INTEGRATION IF NOT EXISTS tower_default_catalog")
        assert "CATALOG_SOURCE = POLARIS" in ddl
        assert "TABLE_FORMAT = ICEBERG" in ddl
        assert "CATALOG_NAMESPACE = 'default'" in ddl
        assert "CATALOG_URI = 'https://jhhgkvi-tower.snowflakecomputing.com/polaris/api/catalog'" in ddl
        assert "CATALOG_NAME = 'tower-lakehouse-001'" in ddl
        assert "OAUTH_CLIENT_ID = 'CLIENT_ID'" in ddl
        assert "OAUTH_CLIENT_SECRET = 'CLIENT_SECRET'" in ddl
        assert "OAUTH_ALLOWED_SCOPES = ( 'PRINCIPAL_ROLE:ALL' )" in ddl
        assert "ENABLED = TRUE" in ddl

    def test_catalog_integration_override_namespace(self, polaris_config):
        ddl = render_catalog_integration_ddl(
            polaris_config, name="integ", catalog_namespace="prod"
        )
        assert "CATALOG_NAMESPACE = 'prod'" in ddl

    def test_iceberg_table_if_not_exists(self):
        ddl = render_iceberg_table_ddl(
            fully_qualified_table="PRODUCT_USAGE_RAW.users",
            catalog_integration="tower_default_catalog",
            external_volume="tower_default_external_volume",
            catalog_namespace="prod.product_usage_raw",
            catalog_table_name="users",
        )
        assert ddl.startswith("CREATE ICEBERG TABLE IF NOT EXISTS PRODUCT_USAGE_RAW.users")
        assert "CATALOG = 'tower_default_catalog'" in ddl
        assert "CATALOG_NAMESPACE = 'prod.product_usage_raw'" in ddl
        assert "CATALOG_TABLE_NAME = 'users'" in ddl
        assert "REFRESH_INTERVAL_SECONDS = 3600" in ddl
        assert "AUTO_REFRESH = TRUE" in ddl
        assert "EXTERNAL_VOLUME = 'tower_default_external_volume'" in ddl

    def test_iceberg_table_force_and_auto_refresh_off(self):
        ddl = render_iceberg_table_ddl(
            fully_qualified_table="db.schema.t",
            catalog_integration="c",
            external_volume="v",
            catalog_namespace="ns",
            catalog_table_name="t",
            auto_refresh=False,
            refresh_interval_seconds=300,
            force=True,
        )
        assert ddl.startswith("CREATE OR REPLACE ICEBERG TABLE db.schema.t")
        assert "AUTO_REFRESH = FALSE" in ddl
        assert "REFRESH_INTERVAL_SECONDS = 300" in ddl

    def test_identifier_escaping(self, polaris_config):
        # Hyphens force quoting; embedded quotes get doubled.
        ddl = render_external_volume_ddl(polaris_config, name='weird"name')
        assert '"weird""name"' in ddl

    def test_sql_string_escaping(self, polaris_config):
        cfg = CatalogConfig(
            name="default",
            type="snowflake-open-catalog",
            environment="default",
            catalog_uri="https://example.com/it's",
            catalog_name="c",
            default_namespace="n",
            oauth_client_id="id",
            oauth_client_secret="sec",
            storage_base_url="s3://b/",
            storage_region="r",
            aws_role_arn="arn",
            aws_external_id="x",
        )
        ddl = render_catalog_integration_ddl(cfg, name="integ")
        assert "CATALOG_URI = 'https://example.com/it''s'" in ddl


# ---------------------------------------------------------------------------
# Snowflake URL parsing
# ---------------------------------------------------------------------------


class TestUrlParsing:
    def test_basic_url(self):
        kw = _parse_snowflake_url(
            "snowflake://user:pass@acct/db/sch?warehouse=WH&role=R"
        )
        assert kw == {
            "user": "user",
            "password": "pass",
            "account": "acct",
            "database": "db",
            "schema": "sch",
            "warehouse": "WH",
            "role": "R",
        }

    def test_url_requires_snowflake_scheme(self):
        with pytest.raises(SnowflakeConnectionError):
            _parse_snowflake_url("postgres://u:p@h/d")

    def test_url_requires_account(self):
        with pytest.raises(SnowflakeConnectionError):
            _parse_snowflake_url("snowflake:///")

    def test_url_percent_decodes(self):
        kw = _parse_snowflake_url("snowflake://u%40x:p%40ss@acct")
        assert kw["user"] == "u@x"
        assert kw["password"] == "p@ss"


# ---------------------------------------------------------------------------
# Permission checks
# ---------------------------------------------------------------------------


class FakeCursor:
    """Minimal shape mimicking snowflake.connector cursor for our needs."""

    def __init__(self, scripted: list[tuple[list[str], list[tuple]]]):
        # scripted: list of (columns, rows) replies per execute() call, in order.
        self._scripted = list(scripted)
        self.description: list[tuple] | None = None
        self._current_rows: list[tuple] = []
        self.executed: list[str] = []

    def execute(self, sql: str) -> None:
        self.executed.append(sql)
        if not self._scripted:
            raise AssertionError(f"unexpected execute: {sql!r}")
        cols, rows = self._scripted.pop(0)
        self.description = [(c,) for c in cols] if cols else None
        self._current_rows = list(rows)

    def fetchone(self):
        return self._current_rows[0] if self._current_rows else None

    def fetchall(self):
        rows, self._current_rows = self._current_rows, []
        return rows

    def close(self):
        pass


def _fake_conn(cursor: FakeCursor):
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


class TestPermissionChecks:
    def _call(self, cursor: FakeCursor, **kwargs) -> PermissionReport:
        with patch.object(sf, "_connect", return_value=_fake_conn(cursor)):
            return check_permissions("snowflake://u:p@acct", **kwargs)

    def test_accountadmin_short_circuits_everything(self):
        cursor = FakeCursor(
            [
                # SELECT CURRENT_ACCOUNT(), CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE()
                (
                    ["account", "user", "role", "warehouse"],
                    [("ACC", "ADMIN", "ACCOUNTADMIN", "WH")],
                ),
                # SELECT CURRENT_ROLE() inside _fetch_effective_privileges
                (["role"], [("ACCOUNTADMIN",)]),
                # SHOW GRANTS TO ROLE ACCOUNTADMIN → contains USAGE ON ROLE ACCOUNTADMIN
                (
                    ["privilege", "granted_on", "name", "granted_to", "grantee_name"],
                    [
                        ("USAGE", "ROLE", "ACCOUNTADMIN", "ROLE", "ACCOUNTADMIN"),
                    ],
                ),
            ]
        )
        report = self._call(
            cursor,
            for_external_volume=True,
            for_catalog_integration=True,
            for_tables_in=["DB.SCHEMA"],
        )
        assert report.ok
        assert all(c.status == "ok" for c in report.checks)
        assert report.suggested_grants == []

    def test_missing_privileges_produce_grants(self):
        cursor = FakeCursor(
            [
                (
                    ["account", "user", "role", "warehouse"],
                    [("ACC", "U", "ROLE_LIMITED", "WH")],
                ),
                (["role"], [("ROLE_LIMITED",)]),
                # SHOW GRANTS TO ROLE ROLE_LIMITED returns only USAGE on DB
                (
                    ["privilege", "granted_on", "name", "granted_to", "grantee_name"],
                    [
                        ("USAGE", "DATABASE", "PROD", "ROLE", "ROLE_LIMITED"),
                    ],
                ),
            ]
        )
        report = self._call(
            cursor,
            for_external_volume=True,
            for_catalog_integration=True,
            for_tables_in=["PROD.MY_SCHEMA"],
        )
        assert not report.ok
        missing_privs = {c.privilege for c in report.checks if c.status == "missing"}
        assert "CREATE EXTERNAL VOLUME" in missing_privs
        assert "CREATE INTEGRATION" in missing_privs
        assert "USAGE" in missing_privs  # schema-level usage is missing
        assert "CREATE ICEBERG TABLE" in missing_privs
        joined = "\n".join(report.suggested_grants)
        assert "GRANT CREATE EXTERNAL VOLUME ON ACCOUNT TO ROLE ROLE_LIMITED;" in joined
        assert "GRANT CREATE INTEGRATION ON ACCOUNT TO ROLE ROLE_LIMITED;" in joined

    def test_role_inheritance_walked(self):
        cursor = FakeCursor(
            [
                (
                    ["account", "user", "role", "warehouse"],
                    [("ACC", "U", "CHILD", "WH")],
                ),
                (["role"], [("CHILD",)]),
                # CHILD inherits from PARENT via USAGE ON ROLE PARENT
                (
                    ["privilege", "granted_on", "name", "granted_to", "grantee_name"],
                    [("USAGE", "ROLE", "PARENT", "ROLE", "CHILD")],
                ),
                # PARENT has CREATE EXTERNAL VOLUME
                (
                    ["privilege", "granted_on", "name", "granted_to", "grantee_name"],
                    [("CREATE EXTERNAL VOLUME", "ACCOUNT", "ACCT", "ROLE", "PARENT")],
                ),
            ]
        )
        report = self._call(
            cursor,
            for_external_volume=True,
            for_catalog_integration=False,
            for_tables_in=None,
        )
        statuses = {c.privilege: c.status for c in report.checks}
        assert statuses["CREATE EXTERNAL VOLUME"] == "ok"


class TestHasPrivilege:
    def test_ownership_grants_anything(self):
        privs = {("OWNERSHIP", "SCHEMA", "DB.S")}
        assert _has_privilege(privs, "CREATE ICEBERG TABLE", "SCHEMA", "db.s")

    def test_case_insensitive_target(self):
        privs = {("USAGE", "DATABASE", "PROD")}
        assert _has_privilege(privs, "USAGE", "DATABASE", "prod")


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class TestSyncCatalog:
    @patch.object(sf, "_execute_and_classify", return_value=([0], []))
    @patch.object(sf, "_run_permission_check")
    @patch.object(sf, "_discover_tables")
    @patch.object(sf, "_fetch_catalog_config")
    def test_sync_catalog_happy_path(
        self,
        mock_fetch,
        mock_discover,
        mock_check,
        mock_execute,
        polaris_config,
    ):
        mock_fetch.return_value = polaris_config
        mock_discover.return_value = [("prod.product_usage_raw", "users")]
        mock_check.return_value = PermissionReport(
            account="ACC",
            user="U",
            role="R",
            warehouse="WH",
            checks=[],
            suggested_grants=[],
        )

        result = sync_catalog(
            catalog="default",
            snowflake_url="snowflake://u:p@acct",
        )

        assert isinstance(result, SyncResult)
        assert result.external_volume == "tower_default_external_volume"
        assert result.catalog_integration == "tower_default_catalog"
        assert result.tables_created == ["prod.product_usage_raw.users"]
        # Permission check should run BEFORE execute.
        mock_check.assert_called_once()
        mock_execute.assert_called_once()
        statements = mock_execute.call_args.args[1]
        assert statements[0].startswith("CREATE EXTERNAL VOLUME IF NOT EXISTS")
        assert statements[1].startswith("CREATE CATALOG INTEGRATION IF NOT EXISTS")
        assert statements[2].startswith("CREATE ICEBERG TABLE IF NOT EXISTS")

    @patch.object(sf, "_execute_and_classify")
    @patch.object(sf, "_discover_tables")
    @patch.object(sf, "_fetch_catalog_config")
    def test_sync_catalog_permission_failure_aborts_before_ddl(
        self,
        mock_fetch,
        mock_discover,
        mock_execute,
        polaris_config,
    ):
        mock_fetch.return_value = polaris_config
        mock_discover.return_value = [("n", "t")]

        bad_report = PermissionReport(
            account="A",
            user="U",
            role="R",
            warehouse=None,
            checks=[PermissionCheck("CREATE INTEGRATION", "ACCOUNT", "missing")],
            suggested_grants=["GRANT CREATE INTEGRATION ON ACCOUNT TO ROLE R;"],
        )
        with patch.object(sf, "check_permissions", return_value=bad_report):
            with pytest.raises(SnowflakePermissionError):
                sync_catalog(catalog="default", snowflake_url="snowflake://u:p@acct")

        mock_execute.assert_not_called()

    @patch.object(sf, "_discover_tables")
    @patch.object(sf, "_fetch_catalog_config")
    def test_sync_catalog_dry_run_emits_ddl_and_skips_connection(
        self, mock_fetch, mock_discover, polaris_config, capsys
    ):
        mock_fetch.return_value = polaris_config
        mock_discover.return_value = [("prod.ns", "users")]

        with patch.object(sf, "_connect") as mock_connect:
            result = sync_catalog(
                catalog="default",
                snowflake_url="snowflake://u:p@acct",
                dry_run=True,
            )

        mock_connect.assert_not_called()
        out = capsys.readouterr().out
        assert "CREATE EXTERNAL VOLUME IF NOT EXISTS" in out
        assert "CREATE CATALOG INTEGRATION IF NOT EXISTS" in out
        assert "CREATE ICEBERG TABLE IF NOT EXISTS" in out
        assert result.tables_created == ["prod.ns.users"]

    def test_sync_catalog_requires_snowflake_url(self):
        with pytest.raises(TypeError):
            sync_catalog(catalog="default")


class TestPerComponent:
    @patch.object(sf, "_execute")
    @patch.object(sf, "_run_permission_check")
    @patch.object(sf, "_fetch_catalog_config")
    def test_create_external_volume_checks_only_volume_grant(
        self, mock_fetch, mock_check, mock_execute, polaris_config
    ):
        mock_fetch.return_value = polaris_config
        name = create_external_volume(
            catalog="default", snowflake_url="snowflake://u:p@acct"
        )
        assert name == "tower_default_external_volume"
        kwargs = mock_check.call_args.kwargs
        assert kwargs["for_external_volume"] is True
        assert kwargs["for_catalog_integration"] is False
        assert kwargs["for_tables_in"] is None

    @patch.object(sf, "_execute")
    @patch.object(sf, "_run_permission_check")
    @patch.object(sf, "_fetch_catalog_config")
    def test_create_catalog_integration_checks_only_integration_grant(
        self, mock_fetch, mock_check, mock_execute, polaris_config
    ):
        mock_fetch.return_value = polaris_config
        name = create_catalog_integration(
            catalog="default", snowflake_url="snowflake://u:p@acct"
        )
        assert name == "tower_default_catalog"
        kwargs = mock_check.call_args.kwargs
        assert kwargs["for_external_volume"] is False
        assert kwargs["for_catalog_integration"] is True
        assert kwargs["for_tables_in"] is None

    @patch.object(sf, "_execute")
    @patch.object(sf, "_run_permission_check")
    @patch.object(sf, "_discover_tables")
    @patch.object(sf, "_fetch_catalog_config")
    def test_create_iceberg_tables_scopes_to_table_schemas(
        self,
        mock_fetch,
        mock_discover,
        mock_check,
        mock_execute,
        polaris_config,
    ):
        mock_fetch.return_value = polaris_config
        mock_discover.return_value = [
            ("prod.product_usage_raw", "users"),
            ("prod.product_usage_raw", "events"),
        ]
        names = create_iceberg_tables(
            catalog="default",
            snowflake_url="snowflake://u:p@acct",
            external_volume="vol",
            catalog_integration="integ",
        )
        assert names == [
            "prod.product_usage_raw.users",
            "prod.product_usage_raw.events",
        ]
        kwargs = mock_check.call_args.kwargs
        assert kwargs["for_external_volume"] is False
        assert kwargs["for_catalog_integration"] is False
        assert kwargs["for_tables_in"] == ["prod.product_usage_raw"]
