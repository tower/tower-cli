//! Tower's usage of DuckDB in one place: opening a session, running trusted
//! setup, locking the session down for untrusted SQL, and executing a query
//! into JSON rows with an optional row cap.
//!
//! The point of the crate is the hardened query path. Agent-issued SQL runs on
//! a customer's machine with their catalog credentials, so before it runs we
//! reject write/DDL and multi-statement input (the [`guard`] module), lock the
//! session down so a query cannot read the local filesystem, load community
//! extensions, or unwind the settings ([`Session::harden`]), and cap the rows a
//! result can carry back ([`Session::query`]). The adversarial tests exercise
//! each of these invariants directly.

use std::time::Instant;

use tower_telemetry::debug;

pub use duckdb::{params, Error, Params};

pub mod guard;

/// A tabular query result: column names, rows as positional JSON values, and a
/// flag set when rows were dropped to honour a caller-supplied cap.
#[derive(Debug, Clone)]
pub struct QueryResult {
    pub columns: Vec<String>,
    pub rows: Vec<Vec<serde_json::Value>>,
    /// Rows were dropped to honour the `max_rows` passed to [`Session::query`].
    pub truncated: bool,
}

/// The statements that lock a session down before untrusted SQL runs: no
/// local-filesystem access (so `read_csv('/etc/passwd')` and friends fail), no
/// community extensions, and a configuration lock so the query cannot unwind any
/// of it. These run after setup, because attaching a catalog is what installs
/// extensions and reaches the network. Only `LocalFileSystem` is disabled, so
/// httpfs and the object-store reads an attached Iceberg catalog depends on keep
/// working; this narrows the query surface without breaking those reads.
pub fn hardening_statements() -> Vec<String> {
    vec![
        "SET disabled_filesystems = 'LocalFileSystem'".to_string(),
        "SET allow_community_extensions = false".to_string(),
        "SET lock_configuration = true".to_string(),
    ]
}

/// An in-memory DuckDB connection Tower runs queries through.
///
/// The lifecycle is setup, then optionally harden, then query: [`run_setup`]
/// installs extensions and attaches catalogs (the access [`harden`] removes),
/// [`harden`] locks the session down, and [`query`] runs a single statement.
///
/// [`run_setup`]: Session::run_setup
/// [`harden`]: Session::harden
/// [`query`]: Session::query
pub struct Session {
    conn: duckdb::Connection,
}

impl Session {
    /// Open a fresh in-memory session.
    pub fn open() -> Result<Self, Error> {
        Ok(Self {
            conn: duckdb::Connection::open_in_memory()?,
        })
    }

    /// Run trusted setup statements one at a time. These may embed secrets
    /// (vended tokens, credentials), so their text is timed but never logged.
    pub fn run_setup(&self, statements: &[String]) -> Result<(), Error> {
        let start = Instant::now();
        for statement in statements {
            self.conn.execute_batch(statement)?;
        }
        debug!(
            "tower-duckdb: setup ({} statements) took {:?}",
            statements.len(),
            start.elapsed()
        );
        Ok(())
    }

    /// Lock the session down for untrusted SQL. Apply after [`run_setup`], since
    /// attaching a catalog needs the access this removes.
    ///
    /// [`run_setup`]: Session::run_setup
    pub fn harden(&self) -> Result<(), Error> {
        for statement in hardening_statements() {
            self.conn.execute_batch(&statement)?;
        }
        Ok(())
    }

    /// Execute a single query as a prepared statement with `params` bound. Values
    /// that fit a bind position should go through `params` rather than the query
    /// text. When `max_rows` is set, rows past it are dropped and the result is
    /// flagged truncated, so an untrusted caller cannot pull an unbounded table
    /// into memory or a model's context.
    pub fn query<P: Params>(
        &self,
        sql: &str,
        params: P,
        max_rows: Option<usize>,
    ) -> Result<QueryResult, Error> {
        let query_start = Instant::now();
        let mut stmt = self.conn.prepare(sql)?;
        let mut columns: Vec<String> = Vec::new();
        let mut rows = Vec::new();
        let mut truncated = false;

        {
            let mut result_rows = stmt.query(params)?;
            while let Some(row) = result_rows.next()? {
                if columns.is_empty() {
                    columns = row.as_ref().column_names();
                }
                if max_rows.is_some_and(|max| rows.len() >= max) {
                    truncated = true;
                    break;
                }
                let mut record = Vec::with_capacity(columns.len());
                for idx in 0..columns.len() {
                    let value: duckdb::types::Value = row.get(idx)?;
                    record.push(value_to_json(value));
                }
                rows.push(record);
            }
        }

        // A query with no result rows never populates columns above.
        if columns.is_empty() {
            columns = stmt.column_names();
        }

        debug!(
            "tower-duckdb: query took {:?} ({} rows): {}",
            query_start.elapsed(),
            rows.len(),
            sql
        );

        Ok(QueryResult {
            columns,
            rows,
            truncated,
        })
    }
}

/// Open a session, run `setup`, and execute `query`. Convenience for one-shot
/// callers that do not need to hold the session. Callers running untrusted SQL
/// should build a [`Session`] and call [`Session::harden`] between setup and
/// query instead.
pub fn run_query<P: Params>(
    setup: &[String],
    query: &str,
    params: P,
    max_rows: Option<usize>,
) -> Result<QueryResult, Error> {
    let session = Session::open()?;
    session.run_setup(setup)?;
    session.query(query, params, max_rows)
}

/// Converts a DuckDB value into a `serde_json::Value`. Integers that overflow an
/// f64 (HugeInt, Decimal) and temporal types are rendered as strings so no
/// precision is lost through JSON's number type.
pub fn value_to_json(value: duckdb::types::Value) -> serde_json::Value {
    use duckdb::types::{TimeUnit, Value};
    use serde_json::json;

    match value {
        Value::Null => serde_json::Value::Null,
        Value::Boolean(v) => json!(v),
        Value::TinyInt(v) => json!(v),
        Value::SmallInt(v) => json!(v),
        Value::Int(v) => json!(v),
        Value::BigInt(v) => json!(v),
        Value::HugeInt(v) => json!(v.to_string()),
        Value::UTinyInt(v) => json!(v),
        Value::USmallInt(v) => json!(v),
        Value::UInt(v) => json!(v),
        Value::UBigInt(v) => json!(v),
        Value::Float(v) => json!(v),
        Value::Double(v) => json!(v),
        Value::Decimal(v) => json!(v.to_string()),
        Value::Text(v) => json!(v),
        Value::Timestamp(unit, v) => {
            let micros = match unit {
                TimeUnit::Second => v.checked_mul(1_000_000),
                TimeUnit::Millisecond => v.checked_mul(1_000),
                TimeUnit::Microsecond => Some(v),
                TimeUnit::Nanosecond => Some(v / 1_000),
            };
            match micros.and_then(chrono::DateTime::from_timestamp_micros) {
                Some(ts) => json!(ts.naive_utc().to_string()),
                None => json!(format!("{:?}", Value::Timestamp(unit, v))),
            }
        }
        Value::Date32(days) => {
            let date = chrono::DateTime::from_timestamp(i64::from(days) * 86_400, 0);
            match date {
                Some(d) => json!(d.date_naive().to_string()),
                None => json!(format!("{:?}", Value::Date32(days))),
            }
        }
        Value::Time64(unit, v) => {
            let micros = match unit {
                TimeUnit::Second => v.checked_mul(1_000_000),
                TimeUnit::Millisecond => v.checked_mul(1_000),
                TimeUnit::Microsecond => Some(v),
                TimeUnit::Nanosecond => Some(v / 1_000),
            };
            let time = micros.and_then(|m| {
                chrono::NaiveTime::from_num_seconds_from_midnight_opt(
                    (m / 1_000_000) as u32,
                    ((m % 1_000_000) * 1_000) as u32,
                )
            });
            match time {
                Some(t) => json!(t.to_string()),
                None => json!(format!("{:?}", Value::Time64(unit, v))),
            }
        }
        Value::Enum(v) => json!(v),
        Value::List(items) | Value::Array(items) => {
            serde_json::Value::Array(items.into_iter().map(value_to_json).collect())
        }
        Value::Struct(fields) => serde_json::Value::Object(
            fields
                .iter()
                .map(|(name, value)| (name.clone(), value_to_json(value.clone())))
                .collect(),
        ),
        Value::Map(entries) => serde_json::Value::Object(
            entries
                .iter()
                .map(|(key, value)| {
                    (
                        stringify_key(&value_to_json(key.clone())),
                        value_to_json(value.clone()),
                    )
                })
                .collect(),
        ),
        Value::Union(inner) => value_to_json(*inner),
        other => json!(format!("{:?}", other)),
    }
}

/// Renders a JSON value as a plain string for use as a map key: strings pass
/// through unquoted, everything else uses its JSON form.
fn stringify_key(value: &serde_json::Value) -> String {
    match value {
        serde_json::Value::Null => String::new(),
        serde_json::Value::String(s) => s.clone(),
        other => other.to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::guard::{first_keyword, is_multi_statement, is_write_statement};
    use super::{hardening_statements, run_query, value_to_json, QueryResult};

    #[test]
    fn duckdb_values_convert_to_json() {
        use duckdb::types::{TimeUnit, Value};

        assert_eq!(value_to_json(Value::Null), serde_json::Value::Null);
        assert_eq!(value_to_json(Value::Boolean(true)), serde_json::json!(true));
        assert_eq!(value_to_json(Value::Int(7)), serde_json::json!(7));
        assert_eq!(
            value_to_json(Value::HugeInt(170141183460469231731687303715884105727)),
            serde_json::json!("170141183460469231731687303715884105727")
        );
        assert_eq!(
            value_to_json(Value::Text("hello".to_string())),
            serde_json::json!("hello")
        );
        assert_eq!(
            value_to_json(Value::Timestamp(TimeUnit::Microsecond, 0)),
            serde_json::json!("1970-01-01 00:00:00")
        );
        assert_eq!(
            value_to_json(Value::Date32(0)),
            serde_json::json!("1970-01-01")
        );
    }

    #[test]
    fn nested_values_convert_to_json_structures() {
        // Round-trip through DuckDB so the list/struct/map values are built the
        // way the engine builds them, rather than by hand.
        let result = run_query(
            &[],
            "SELECT [1, 2] AS l, {'a': 1, 'b': 'x'} AS s, MAP {'k': 2} AS m",
            [],
            None,
        )
        .expect("query should succeed");

        assert_eq!(result.columns, vec!["l", "s", "m"]);
        assert_eq!(
            result.rows[0],
            vec![
                serde_json::json!([1, 2]),
                serde_json::json!({"a": 1, "b": "x"}),
                serde_json::json!({"k": 2}),
            ]
        );
    }

    #[test]
    fn run_query_returns_columns_and_rows() {
        let setup = vec![
            "CREATE TABLE t (id INTEGER, name TEXT)".to_string(),
            "INSERT INTO t VALUES (1, 'a'), (2, 'b')".to_string(),
        ];
        let result = run_query(&setup, "SELECT id, name FROM t ORDER BY id", [], None)
            .expect("query should succeed");

        assert_eq!(result.columns, vec!["id", "name"]);
        assert_eq!(
            result.rows,
            vec![
                vec![serde_json::json!(1), serde_json::json!("a")],
                vec![serde_json::json!(2), serde_json::json!("b")],
            ]
        );
        assert!(!result.truncated);
    }

    #[test]
    fn run_query_reports_columns_for_empty_results() {
        let result =
            run_query(&[], "SELECT 1 AS x WHERE 1 = 0", [], None).expect("query should succeed");

        assert_eq!(result.columns, vec!["x"]);
        assert!(result.rows.is_empty());
    }

    #[test]
    fn run_query_caps_rows_and_flags_truncation() {
        let capped = run_query(&[], "SELECT * FROM range(5) AS t(i)", [], Some(3))
            .expect("query should succeed");
        assert_eq!(capped.rows.len(), 3);
        assert!(capped.truncated);

        let exact = run_query(&[], "SELECT * FROM range(3) AS t(i)", [], Some(3))
            .expect("query should succeed");
        assert_eq!(exact.rows.len(), 3);
        assert!(!exact.truncated);
    }

    // --- Guard gates -----------------------------------------------------

    #[test]
    fn multi_statement_ignores_separators_in_strings_and_comments() {
        assert!(!is_multi_statement("SELECT 1"));
        assert!(!is_multi_statement("SELECT 1;"));
        assert!(!is_multi_statement("  SELECT 1 ;  "));
        assert!(!is_multi_statement("SELECT 'a;b'"));
        assert!(!is_multi_statement("SELECT 1 -- ; not a statement"));
        assert!(!is_multi_statement("SELECT 1; -- trailing comment"));
        assert!(!is_multi_statement("SELECT /* ; */ 1"));

        assert!(is_multi_statement("SELECT 1; SELECT 2"));
        assert!(is_multi_statement("SELECT 1; DROP TABLE t"));
        assert!(is_multi_statement("SELECT 'a;b'; SELECT 2"));
    }

    #[test]
    fn write_statements_are_detected_through_case_and_comments() {
        assert_eq!(first_keyword("  SELECT 1"), "select");
        assert_eq!(first_keyword("/* c */ INSERT INTO t VALUES (1)"), "insert");
        assert_eq!(first_keyword("-- lead\nDELETE FROM t"), "delete");

        assert!(!is_write_statement("SELECT * FROM t"));
        assert!(!is_write_statement("WITH x AS (SELECT 1) SELECT * FROM x"));
        assert!(is_write_statement("insert into t values (1)"));
        assert!(is_write_statement("  DROP TABLE t"));
        assert!(is_write_statement("COPY t TO 'out.csv'"));
        assert!(is_write_statement("ATTACH 'x' AS y"));
    }

    #[test]
    fn harden_allows_selects_but_blocks_local_files_and_config_changes() {
        let setup = hardening_statements();

        let ok = run_query(&setup, "SELECT 1 AS x", [], None)
            .expect("a plain select should still run under the hardened session");
        assert_eq!(ok.columns, vec!["x"]);
        assert_eq!(ok.rows, vec![vec![serde_json::json!(1)]]);

        let fs_err = run_query(&setup, "SELECT * FROM read_csv('Cargo.toml')", [], None)
            .expect_err("local filesystem access should be blocked");
        assert!(
            fs_err.to_string().to_lowercase().contains("disabled"),
            "unexpected error: {fs_err}"
        );

        let cfg_err = run_query(&setup, "SET memory_limit = '1GB'", [], None)
            .expect_err("configuration should be locked");
        let cfg_msg = cfg_err.to_string().to_lowercase();
        assert!(
            cfg_msg.contains("lock") || cfg_msg.contains("configuration"),
            "unexpected error: {cfg_err}"
        );
    }

    /// Regression check against real Iceberg data. The other query tests use
    /// plain in-memory tables; this one writes a small Iceberg table with
    /// DuckDB's `COPY … (FORMAT iceberg)` (real metadata + manifests + parquet)
    /// and reads it back, so the iceberg reader and our column/row extraction are
    /// exercised end to end, NULLs and the row cap included. Needs the `iceberg`
    /// extension, fetched on first run and then cached.
    #[test]
    fn iceberg_scan_reads_written_table_through_run_query() {
        let dir = std::env::temp_dir().join(format!("tower_iceberg_test_{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);
        std::fs::create_dir_all(&dir).expect("create temp dir");
        let table = dir.join("events").to_string_lossy().replace('\'', "''");

        let conn = duckdb::Connection::open_in_memory().expect("open duckdb");
        conn.execute_batch("INSTALL iceberg").expect("install iceberg");
        conn.execute_batch("LOAD iceberg").expect("load iceberg");
        conn.execute_batch(&format!(
            "COPY (SELECT * FROM (VALUES (1, 'a'), (2, 'b'), (3, NULL)) AS t(id, name)) \
             TO '{table}' (FORMAT iceberg)"
        ))
        .expect("write iceberg table");

        let setup = vec!["INSTALL iceberg".to_string(), "LOAD iceberg".to_string()];

        let result = run_query(
            &setup,
            &format!("SELECT id, name FROM iceberg_scan('{table}') ORDER BY id"),
            [],
            None,
        )
        .expect("iceberg_scan should read the table");
        assert_eq!(result.columns, vec!["id", "name"]);
        assert_eq!(
            result.rows,
            vec![
                vec![serde_json::json!(1), serde_json::json!("a")],
                vec![serde_json::json!(2), serde_json::json!("b")],
                vec![serde_json::json!(3), serde_json::Value::Null],
            ]
        );
        assert!(!result.truncated);

        let capped = run_query(
            &setup,
            &format!("SELECT id FROM iceberg_scan('{table}') ORDER BY id"),
            [],
            Some(2),
        )
        .expect("iceberg_scan should read the table");
        assert_eq!(capped.rows.len(), 2);
        assert!(capped.truncated);

        let _ = std::fs::remove_dir_all(&dir);
    }

    // --- Adversarial regression suite ------------------------------------
    //
    // Each test encodes an attack an agent-issued query might attempt and
    // asserts the sandbox refuses it. These are the security invariants: if a
    // future change weakens the gates or the hardening, one of these fails.

    /// A statement run under the session hardening. Extensions are not loaded, so
    /// the attacks below must be blocked by the session lockdown alone.
    fn run_hardened(sql: &str) -> Result<QueryResult, duckdb::Error> {
        run_query(&hardening_statements(), sql, [], None)
    }

    #[test]
    fn sandbox_gate_rejects_data_tampering() {
        for sql in [
            "DROP TABLE runs",
            "DELETE FROM runs",
            "UPDATE runs SET id = 0",
            "INSERT INTO runs VALUES (1)",
            "CREATE TABLE evil AS SELECT 1",
            "ALTER TABLE runs ADD COLUMN x INTEGER",
            "TRUNCATE runs",
            "MERGE INTO runs USING x ON true WHEN MATCHED THEN DELETE",
            "COPY runs TO '/tmp/exfil.csv'",
            "ATTACH '/tmp/evil.db' AS e",
            "DETACH runs",
            "  drop   TABLE runs",
            "/* sneaky */ DELETE FROM runs",
        ] {
            assert!(is_write_statement(sql), "not rejected as write/DDL: {sql}");
        }
        for sql in [
            "SELECT * FROM runs",
            "WITH t AS (SELECT 1) SELECT * FROM t",
            "SELECT count(*) FROM runs",
        ] {
            assert!(!is_write_statement(sql), "legit read wrongly flagged: {sql}");
        }
    }

    #[test]
    fn sandbox_gate_rejects_statement_smuggling() {
        for sql in [
            "SELECT 1; DROP TABLE runs",
            "SELECT 1; DELETE FROM runs",
            "SELECT 'a;b'; DROP TABLE runs",
            "SELECT 1;\n-- c\nUPDATE runs SET id = 0",
        ] {
            assert!(is_multi_statement(sql), "smuggled statement not caught: {sql}");
        }
        assert!(!is_multi_statement("SELECT * FROM runs -- a trailing ; comment"));
    }

    #[test]
    fn sandbox_blocks_host_filesystem_reads() {
        for sql in [
            "SELECT * FROM read_csv('/etc/passwd')",
            "SELECT * FROM read_text('/etc/hostname')",
            "SELECT * FROM read_json('/etc/passwd')",
            "SELECT * FROM read_parquet('/tmp/x.parquet')",
            "SELECT * FROM read_csv('/etc/*')",
            "SELECT * FROM '/etc/passwd'",
        ] {
            assert!(run_hardened(sql).is_err(), "host file read NOT blocked: {sql}");
        }
        let err = run_hardened("SELECT * FROM read_csv('/etc/passwd')").unwrap_err();
        assert!(err.to_string().to_lowercase().contains("disabled"), "{err}");
    }

    #[test]
    fn sandbox_blocks_host_filesystem_writes() {
        for sql in [
            "COPY (SELECT 1) TO '/tmp/pwned.csv'",
            "COPY (SELECT 1) TO '/tmp/pwned.parquet' (FORMAT parquet)",
        ] {
            assert!(run_hardened(sql).is_err(), "host file write NOT blocked: {sql}");
        }
    }

    #[test]
    fn sandbox_blocks_configuration_escape() {
        for sql in [
            "SET disabled_filesystems = ''",
            "RESET disabled_filesystems",
            "SET enable_external_access = true",
            "SET allow_community_extensions = true",
            "SET lock_configuration = false",
            "PRAGMA disabled_filesystems=''",
        ] {
            assert!(run_hardened(sql).is_err(), "configuration escape NOT blocked: {sql}");
        }
    }

    #[test]
    fn sandbox_blocks_arbitrary_extension_loading() {
        for sql in [
            "LOAD '/tmp/evil.duckdb_extension'",
            "INSTALL some_untrusted_extension_xyz",
        ] {
            assert!(run_hardened(sql).is_err(), "extension load NOT blocked: {sql}");
        }
    }

    #[test]
    fn sandbox_blocks_network_ssrf_via_table_functions() {
        for sql in [
            "SELECT * FROM read_csv('http://169.254.169.254/latest/meta-data/')",
            "SELECT * FROM read_parquet('https://attacker.example/x.parquet')",
            "SELECT * FROM read_csv('http://localhost:8080/internal')",
        ] {
            assert!(run_hardened(sql).is_err(), "SSRF NOT blocked: {sql}");
        }
    }

    /// Polls MinIO's health endpoint over a raw socket until it answers 200.
    fn wait_for_minio(port: u16) -> bool {
        use std::io::{Read, Write};
        for _ in 0..60 {
            if let Ok(mut stream) = std::net::TcpStream::connect(("127.0.0.1", port)) {
                let _ = stream.set_read_timeout(Some(std::time::Duration::from_secs(2)));
                let request =
                    "GET /minio/health/live HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n";
                let mut response = String::new();
                if stream.write_all(request.as_bytes()).is_ok()
                    && stream.read_to_string(&mut response).is_ok()
                    && response.contains(" 200 ")
                {
                    return true;
                }
            }
            std::thread::sleep(std::time::Duration::from_millis(500));
        }
        false
    }

    /// The coverage the local-only tests can't give: it proves the hardening does
    /// NOT break a real object-store Iceberg read (the reader uses S3FileSystem,
    /// which the hardening leaves enabled) while local-filesystem access and
    /// configuration changes stay blocked in the same session. Starts a MinIO
    /// container via testcontainers and self-skips when no Docker daemon is
    /// available, so a plain `cargo test` still passes without Docker.
    #[test]
    fn sandbox_holds_over_object_store_iceberg() {
        use testcontainers::core::{IntoContainerPort, WaitFor};
        use testcontainers::runners::SyncRunner;
        use testcontainers::{GenericImage, ImageExt};

        let bucket = "warehouse";
        let image = GenericImage::new("minio/minio", "latest")
            .with_wait_for(WaitFor::seconds(1))
            .with_exposed_port(9000.tcp())
            .with_entrypoint("sh")
            .with_env_var("MINIO_ROOT_USER", "minioadmin")
            .with_env_var("MINIO_ROOT_PASSWORD", "minioadmin")
            .with_cmd([
                "-c".to_string(),
                format!("mkdir -p /data/{bucket} && exec minio server /data"),
            ]);

        let container = match image.start() {
            Ok(container) => container,
            Err(err) => {
                eprintln!(
                    "skipping sandbox_holds_over_object_store_iceberg (no Docker daemon?): {err}"
                );
                return;
            }
        };
        let port = container
            .get_host_port_ipv4(9000.tcp())
            .expect("mapped MinIO port");
        assert!(wait_for_minio(port), "MinIO did not become healthy");

        let secret = format!(
            "CREATE SECRET s3sec (TYPE s3, KEY_ID 'minioadmin', SECRET 'minioadmin', \
             ENDPOINT '127.0.0.1:{port}', URL_STYLE 'path', USE_SSL false, REGION 'us-east-1')"
        );
        let table = format!("s3://{bucket}/tbl");
        let extensions = || {
            vec![
                "INSTALL httpfs".to_string(),
                "LOAD httpfs".to_string(),
                "INSTALL iceberg".to_string(),
                "LOAD iceberg".to_string(),
            ]
        };

        let seed = duckdb::Connection::open_in_memory().expect("open duckdb");
        for stmt in extensions() {
            seed.execute_batch(&stmt).expect("load extension");
        }
        seed.execute_batch(&secret).expect("create s3 secret");
        seed.execute_batch(&format!(
            "COPY (SELECT * FROM (VALUES (1,'a'),(2,'b'),(3,NULL)) t(id,name)) \
             TO '{table}' (FORMAT iceberg)"
        ))
        .expect("seed iceberg table on object storage");

        let mut setup = extensions();
        setup.push(secret);
        setup.extend(hardening_statements());

        let read = run_query(
            &setup,
            &format!("SELECT id, name FROM iceberg_scan('{table}') ORDER BY id"),
            [],
            None,
        )
        .expect("hardening must not break object-store Iceberg reads");
        assert_eq!(read.columns, vec!["id", "name"]);
        assert_eq!(
            read.rows,
            vec![
                vec![serde_json::json!(1), serde_json::json!("a")],
                vec![serde_json::json!(2), serde_json::json!("b")],
                vec![serde_json::json!(3), serde_json::Value::Null],
            ]
        );

        let local = run_query(&setup, "SELECT * FROM read_csv('/etc/hostname')", [], None)
            .expect_err("local filesystem reads must stay blocked");
        assert!(
            local.to_string().to_lowercase().contains("disabled"),
            "unexpected error: {local}"
        );

        let cfg = run_query(&setup, "SET memory_limit = '1GB'", [], None)
            .expect_err("configuration must stay locked");
        let cfg = cfg.to_string().to_lowercase();
        assert!(
            cfg.contains("lock") || cfg.contains("configuration"),
            "unexpected error: {cfg}"
        );
    }
}
