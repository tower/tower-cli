//! Tower's usage of DuckDB in one place: opening a session, running trusted
//! setup, locking the session down for untrusted SQL, and executing a query
//! into JSON rows with an optional row cap.
//!
//! The point of the crate is the hardened query path. Agent-issued SQL runs on a
//! customer's machine with their catalog credentials, so it gets layered
//! treatment: reject anything that is not a single read-only SELECT using
//! DuckDB's own parser (the [`guard`] module), lock the session down so a query
//! cannot read the local filesystem, pull in extensions, or unwind the settings
//! ([`Hardening`]), and bound what a result may carry back in rows, bytes, and
//! wall-clock time ([`Limits`]). The adversarial tests exercise each of these
//! directly.
//!
//! None of that is the security boundary. The boundary is the engine-enforced
//! privilege: the caller vends read-only credentials and attaches the catalog
//! `READ_ONLY`, so a write is refused by the catalog no matter what this crate
//! concludes. Everything here is defence in depth in front of that, worth having
//! because it turns a confusing engine error into a clear refusal and closes
//! SELECT-shaped holes the credential alone would not.
//!
//! Two gaps are deliberate and worth knowing. Network egress is open: an attached
//! Iceberg catalog is made of S3 reads, so `enable_external_access` cannot be
//! turned off on that path, and a query can still reach a URL through a table
//! function. And the ceilings bound what this process holds, not what DuckDB
//! spends internally on a materializing plan. Closing either one needs controls
//! outside this crate: a network boundary, and [`Hardening::memory_limit`].

use std::time::Instant;

use tower_telemetry::debug;

pub use duckdb::{params, Error, Params};

pub mod guard;

/// Why a result stopped short of everything the query would have returned.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Truncation {
    /// Hit the row ceiling.
    Rows,
    /// Hit the byte ceiling. This is the one that catches a query which packs a
    /// whole table into a handful of rows.
    Bytes,
}

/// A tabular query result: column names, rows as positional JSON values, and why
/// it stopped early if it did.
#[derive(Debug, Clone)]
pub struct QueryResult {
    pub columns: Vec<String>,
    pub rows: Vec<Vec<serde_json::Value>>,
    /// Set when a [`Limits`] ceiling cut the result short.
    pub truncated: Option<Truncation>,
}

impl QueryResult {
    /// Whether a ceiling cut this result short.
    pub fn is_truncated(&self) -> bool {
        self.truncated.is_some()
    }
}

/// Ceilings applied while a result is read back.
///
/// Rows alone are a weak bound, because a query can compact a whole column into
/// one row (`string_agg`, `list`, `to_json`). `max_total_bytes` is what actually
/// limits how much data a single query carries back, so set both for untrusted
/// callers. `timeout` bounds how long the query may run: DuckDB has no statement
/// timeout of its own, so it is enforced by interrupting the connection.
#[derive(Debug, Clone, Default)]
pub struct Limits {
    pub max_rows: Option<usize>,
    pub max_total_bytes: Option<usize>,
    pub timeout: Option<std::time::Duration>,
}

impl Limits {
    /// No ceilings. For trusted, caller-authored SQL.
    pub fn none() -> Self {
        Self::default()
    }

    /// The ceilings for untrusted (agent-issued) SQL.
    pub fn agent() -> Self {
        Self {
            max_rows: Some(guard::AGENT_MAX_ROWS),
            max_total_bytes: Some(guard::AGENT_MAX_RESULT_BYTES),
            timeout: Some(guard::AGENT_QUERY_TIMEOUT),
        }
    }

    /// Only a row ceiling, for a caller that wants a readable result without a
    /// security budget.
    pub fn rows(max_rows: usize) -> Self {
        Self {
            max_rows: Some(max_rows),
            ..Self::default()
        }
    }
}

/// How to lock a session down before untrusted SQL runs.
///
/// The defaults are what a catalog query needs: local-filesystem access off (so
/// `read_csv('/etc/passwd')` and friends fail), no implicit extension
/// install/load, no community or unsigned extensions, secrets kept redacted, and
/// the configuration frozen so the query cannot unwind any of it.
///
/// Note what is deliberately *not* set: `enable_external_access = false`. It is
/// DuckDB's master switch and would be the stronger control, but it also blocks
/// the S3 reads an attached Iceberg catalog is made of, so a catalog query cannot
/// use it. Network egress is therefore not closed by this lockdown; a query can
/// still reach a URL through a table function. The read-only credential is what
/// bounds what that query can *read*, and closing egress needs a network boundary
/// outside this process. Callers that do not need object storage should set
/// `deny_external_access` and get the stronger guarantee.
#[derive(Debug, Clone, Default)]
pub struct Hardening {
    /// Refuse all external access, network and local files alike. Breaks attached
    /// object-store catalogs, so it is off by default.
    pub deny_external_access: bool,
    /// Engine memory ceiling, e.g. `"2GB"`. `None` keeps DuckDB's default.
    pub memory_limit: Option<String>,
    /// Ceiling on spill-to-disk, e.g. `"4GB"`. `None` keeps DuckDB's default.
    pub max_temp_directory_size: Option<String>,
}

impl Hardening {
    /// The lockdown for untrusted (agent-issued) SQL.
    ///
    /// Adds an engine memory ceiling on top of the default lockdown. [`Limits`]
    /// bounds what a result hands back, but a query can spend far more than that
    /// inside DuckDB before the first row appears (a large `ORDER BY`, or a
    /// `string_agg` over a whole column). Only the engine can bound that, so an
    /// untrusted caller should set it.
    pub fn agent() -> Self {
        Self {
            deny_external_access: false,
            memory_limit: Some("1GB".to_string()),
            max_temp_directory_size: Some("2GB".to_string()),
        }
    }

    /// The lockdown statements, in the order they must run.
    ///
    /// `lock_configuration` is last because it freezes every later `SET`. The
    /// whole sequence runs after setup, because attaching a catalog is what
    /// installs the extensions and reaches the network that this then takes away.
    pub fn statements(&self) -> Vec<String> {
        let mut statements = Vec::new();
        if self.deny_external_access {
            statements.push("SET enable_external_access = false".to_string());
        }
        statements.extend(
            [
                "SET disabled_filesystems = 'LocalFileSystem'",
                // Stop DuckDB reaching out for an extension mid-query. The ones a
                // catalog needs are already loaded by setup.
                "SET autoinstall_known_extensions = false",
                "SET autoload_known_extensions = false",
                "SET allow_community_extensions = false",
                "SET allow_unsigned_extensions = false",
                // Keep vended tokens redacted in duckdb_secrets().
                "SET allow_unredacted_secrets = false",
            ]
            .into_iter()
            .map(str::to_string),
        );
        if let Some(limit) = &self.memory_limit {
            statements.push(format!("SET memory_limit = '{}'", limit.replace('\'', "''")));
        }
        if let Some(limit) = &self.max_temp_directory_size {
            statements.push(format!(
                "SET max_temp_directory_size = '{}'",
                limit.replace('\'', "''")
            ));
        }
        statements.push("SET lock_configuration = true".to_string());
        statements
    }
}

/// The default lockdown statements, for callers that do not need to tune it.
pub fn hardening_statements() -> Vec<String> {
    Hardening::default().statements()
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
    pub fn harden(&self, hardening: &Hardening) -> Result<(), Error> {
        for statement in hardening.statements() {
            self.conn.execute_batch(&statement)?;
        }
        Ok(())
    }

    /// Execute a single query as a prepared statement with `params` bound. Values
    /// that fit a bind position should go through `params` rather than the query
    /// text.
    ///
    /// `limits` bound the result as it is read: rows and total bytes are counted
    /// as values come back and the read stops at either ceiling, so an untrusted
    /// caller cannot pull an unbounded table into memory or a model's context. A
    /// `timeout` interrupts the connection when the query outruns it.
    ///
    /// The ceilings bound what this process *holds*, which is not the same as
    /// what the engine does: a query whose plan materializes (a large `ORDER BY`
    /// or aggregate) spends that memory inside DuckDB before the first row is
    /// handed over. Use [`Hardening::memory_limit`] for that.
    pub fn query<P: Params>(
        &self,
        sql: &str,
        params: P,
        limits: &Limits,
    ) -> Result<QueryResult, Error> {
        let query_start = Instant::now();
        // Armed before prepare so a statement that hangs while binding (a remote
        // catalog read, say) is still interrupted. Disarms on drop.
        let _deadline = limits.timeout.map(|timeout| Deadline::arm(&self.conn, timeout));

        let mut stmt = self.conn.prepare(sql)?;
        let mut columns: Vec<String> = Vec::new();
        let mut rows = Vec::new();
        let mut truncated = None;
        let mut total_bytes = 0usize;

        {
            let mut result_rows = stmt.query(params)?;
            while let Some(row) = result_rows.next()? {
                if columns.is_empty() {
                    columns = row.as_ref().column_names();
                }
                if limits.max_rows.is_some_and(|max| rows.len() >= max) {
                    truncated = Some(Truncation::Rows);
                    break;
                }
                // Measured before the row is kept, so a row that would blow the
                // budget is discarded rather than returned and merely labelled
                // truncated. A single `string_agg` can carry an entire table in
                // one row, so admitting it and flagging it would leave the
                // ceiling doing nothing at all. A first row that is already over
                // budget yields an empty, truncated result, which is the honest
                // answer. The check runs per value, not per row, so conversion
                // stops at the first column that exceeds the budget instead of
                // materializing the rest of an oversized row. (The offending
                // value itself is still built once before it is measured — the
                // driver hands values over whole — so the engine's
                // `Hardening::memory_limit` is what bounds a query's spend,
                // while this bounds what the caller is handed.)
                let mut record = Vec::with_capacity(columns.len());
                // Counted as the row serializes: `[`…`]` plus a comma per
                // separator, and a comma joining it to the previous row.
                let mut record_bytes = 2 + usize::from(!rows.is_empty());
                let mut over_budget = false;
                for idx in 0..columns.len() {
                    let value: duckdb::types::Value = row.get(idx)?;
                    let value = value_to_json(value);
                    record_bytes += json_size(&value) + usize::from(idx > 0);
                    if limits
                        .max_total_bytes
                        .is_some_and(|max| total_bytes + record_bytes > max)
                    {
                        over_budget = true;
                        break;
                    }
                    record.push(value);
                }
                if over_budget {
                    truncated = Some(Truncation::Bytes);
                    break;
                }
                total_bytes += record_bytes;
                rows.push(record);
            }
        }

        // A query with no result rows never populates columns above.
        if columns.is_empty() {
            columns = stmt.column_names();
        }

        debug!(
            "tower-duckdb: query took {:?} ({} rows, {} bytes): {}",
            query_start.elapsed(),
            rows.len(),
            total_bytes,
            sql
        );

        Ok(QueryResult {
            columns,
            rows,
            truncated,
        })
    }
}

/// Interrupts a connection if it is still working when the deadline passes.
///
/// DuckDB has no statement timeout, so a wall-clock bound has to come from the
/// host. Interrupts are honoured at chunk boundaries, so this bounds a runaway
/// query rather than guaranteeing an exact deadline; a hard kill would need a
/// process boundary.
struct Deadline {
    expired: std::sync::Arc<std::sync::atomic::AtomicBool>,
    watcher: Option<std::thread::JoinHandle<()>>,
}

impl Deadline {
    fn arm(conn: &duckdb::Connection, timeout: std::time::Duration) -> Self {
        let handle = conn.interrupt_handle();
        let expired = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
        let done = expired.clone();
        let watcher = std::thread::spawn(move || {
            let deadline = Instant::now() + timeout;
            // Woken in slices so a finished query disarms promptly instead of
            // holding the thread for the whole timeout.
            while Instant::now() < deadline {
                if done.load(std::sync::atomic::Ordering::Relaxed) {
                    return;
                }
                std::thread::sleep(std::time::Duration::from_millis(25));
            }
            if !done.load(std::sync::atomic::Ordering::Relaxed) {
                handle.interrupt();
            }
        });
        Self {
            expired,
            watcher: Some(watcher),
        }
    }
}

impl Drop for Deadline {
    fn drop(&mut self) {
        self.expired
            .store(true, std::sync::atomic::Ordering::Relaxed);
        if let Some(watcher) = self.watcher.take() {
            let _ = watcher.join();
        }
    }
}

/// A shareable handle that stops a session's running query from another thread.
///
/// A session runs its query on a blocking thread, and the async caller that
/// spawned it can go away — an MCP request gets cancelled, its future dropped —
/// with no way to reach the connection. This is that way: create the handle
/// first, hand a clone to the blocking thread to [`attach`] to its session, and
/// [`cancel`] from anywhere. Cancelling before the attach is remembered
/// (`attach` reports it), so work queued behind a concurrency limit can be
/// abandoned before its query ever starts. Cancelling after the session
/// finished or closed is a documented no-op in the driver, so an unconditional
/// cancel-on-drop guard is safe.
///
/// Like [`Deadline`], this rides on `duckdb_interrupt`, which is honoured at
/// chunk boundaries: it stops a runaway query promptly rather than instantly.
///
/// [`attach`]: CancelHandle::attach
/// [`cancel`]: CancelHandle::cancel
#[derive(Clone, Default)]
pub struct CancelHandle {
    state: std::sync::Arc<std::sync::Mutex<CancelState>>,
}

#[derive(Default)]
struct CancelState {
    cancelled: bool,
    target: Option<std::sync::Arc<duckdb::InterruptHandle>>,
}

impl CancelHandle {
    pub fn new() -> Self {
        Self::default()
    }

    /// Interrupt the attached session's query, if one is running, and remember
    /// the cancellation so a later [`attach`](CancelHandle::attach) sees it.
    pub fn cancel(&self) {
        let target = {
            let mut state = self.state.lock().expect("cancel state poisoned");
            state.cancelled = true;
            state.target.clone()
        };
        if let Some(handle) = target {
            handle.interrupt();
        }
    }

    /// Bind this handle to `session`'s connection. Returns whether the handle
    /// was already cancelled; a caller seeing `true` should drop the session
    /// without running its query.
    #[must_use]
    pub fn attach(&self, session: &Session) -> bool {
        let mut state = self.state.lock().expect("cancel state poisoned");
        state.target = Some(session.conn.interrupt_handle());
        state.cancelled
    }
}

/// The exact number of bytes `value` occupies when serialized as compact JSON.
///
/// This is what the byte ceiling counts, so it must not undercount: an earlier
/// approximation ignored quotes, escapes, and separators, and a query shaped as
/// one deeply nested value (`list_transform(range(10000000), x -> '')`) slipped
/// a 100 MB serialized response under a 1 MiB ceiling. Exactness is asserted
/// against `serde_json::to_string` in the tests. Callers that serialize
/// pretty-printed pay whitespace on top of this, so they should serialize
/// bounded results compactly.
fn json_size(value: &serde_json::Value) -> usize {
    match value {
        serde_json::Value::Null => 4,
        serde_json::Value::Bool(b) => {
            if *b {
                4
            } else {
                5
            }
        }
        serde_json::Value::Number(n) => n.to_string().len(),
        serde_json::Value::String(s) => json_string_size(s),
        serde_json::Value::Array(items) => {
            2 + items.len().saturating_sub(1) + items.iter().map(json_size).sum::<usize>()
        }
        serde_json::Value::Object(fields) => {
            2 + fields.len().saturating_sub(1)
                + fields
                    .iter()
                    .map(|(key, value)| json_string_size(key) + 1 + json_size(value))
                    .sum::<usize>()
        }
    }
}

/// Serialized size of a JSON string: surrounding quotes plus per-byte escape
/// cost, mirroring serde_json's escaping (short escapes for the common control
/// characters, `\u00XX` for the rest, multi-byte UTF-8 passed through).
fn json_string_size(s: &str) -> usize {
    2 + s
        .bytes()
        .map(|b| match b {
            b'"' | b'\\' | 0x08 | 0x0c | b'\n' | b'\r' | b'\t' => 2,
            0x00..=0x1f => 6,
            _ => 1,
        })
        .sum::<usize>()
}

/// Open a session, run `setup`, and execute `query`. Convenience for one-shot
/// callers that do not need to hold the session. Callers running untrusted SQL
/// should build a [`Session`] and call [`Session::harden`] between setup and
/// query instead.
pub fn run_query<P: Params>(
    setup: &[String],
    query: &str,
    params: P,
    limits: &Limits,
) -> Result<QueryResult, Error> {
    let session = Session::open()?;
    session.run_setup(setup)?;
    session.query(query, params, limits)
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
    use super::guard::{classify_read_only, ReadOnlyCheck};
    use super::{
        hardening_statements, run_query, value_to_json, Hardening, Limits, QueryResult, Session,
        Truncation,
    };

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
            &Limits::none(),
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
        let result = run_query(&setup, "SELECT id, name FROM t ORDER BY id", [], &Limits::none())
            .expect("query should succeed");

        assert_eq!(result.columns, vec!["id", "name"]);
        assert_eq!(
            result.rows,
            vec![
                vec![serde_json::json!(1), serde_json::json!("a")],
                vec![serde_json::json!(2), serde_json::json!("b")],
            ]
        );
        assert!(!result.is_truncated());
    }

    #[test]
    fn run_query_reports_columns_for_empty_results() {
        let result =
            run_query(&[], "SELECT 1 AS x WHERE 1 = 0", [], &Limits::none()).expect("query should succeed");

        assert_eq!(result.columns, vec!["x"]);
        assert!(result.rows.is_empty());
    }

    #[test]
    fn run_query_caps_rows_and_flags_truncation() {
        let capped = run_query(&[], "SELECT * FROM range(5) AS t(i)", [], &Limits::rows(3))
            .expect("query should succeed");
        assert_eq!(capped.rows.len(), 3);
        assert_eq!(capped.truncated, Some(Truncation::Rows));

        let exact = run_query(&[], "SELECT * FROM range(3) AS t(i)", [], &Limits::rows(3))
            .expect("query should succeed");
        assert_eq!(exact.rows.len(), 3);
        assert!(!exact.is_truncated());
    }

    /// The reason a row cap is not enough on its own: one row can carry a whole
    /// column. A row-only ceiling lets this through; the byte ceiling catches it.
    #[test]
    fn a_byte_ceiling_catches_what_a_row_ceiling_misses() {
        let packed = "SELECT string_agg(i::VARCHAR, ',') AS all_rows FROM range(20000) AS t(i)";

        let row_capped = run_query(&[], packed, [], &Limits::rows(1000))
            .expect("query should succeed");
        assert_eq!(row_capped.rows.len(), 1);
        assert!(
            !row_capped.is_truncated(),
            "a row ceiling cannot see a single oversized row"
        );
        let packed_bytes = row_capped.rows[0][0].as_str().map_or(0, str::len);
        assert!(
            packed_bytes > 64 * 1024,
            "expected a large packed value, got {packed_bytes} bytes"
        );

        let byte_capped = run_query(
            &[],
            packed,
            [],
            &Limits {
                max_rows: Some(1000),
                max_total_bytes: Some(4096),
                timeout: None,
            },
        )
        .expect("query should succeed");
        assert_eq!(
            byte_capped.truncated,
            Some(Truncation::Bytes),
            "the byte ceiling should have cut this short"
        );
        // The ceiling has to *withhold* the oversized row, not hand it over with a
        // label on it. Returning it and calling it truncated would leave the bound
        // doing nothing.
        let returned: usize = byte_capped
            .rows
            .iter()
            .flat_map(|row| row.iter())
            .map(|value| value.as_str().map_or(0, str::len))
            .sum();
        assert!(
            returned <= 4096,
            "budget was 4096 bytes but {returned} bytes came back"
        );
    }

    /// A single row larger than the whole budget is refused outright, leaving an
    /// empty truncated result. That is deliberately blunt: the alternative is
    /// admitting an arbitrarily large row, which is what the ceiling exists to
    /// prevent.
    #[test]
    fn one_row_bigger_than_the_whole_budget_is_withheld() {
        let result = run_query(
            &[],
            "SELECT repeat('x', 5000000) AS pad",
            [],
            &Limits {
                max_rows: None,
                max_total_bytes: Some(1024 * 1024),
                timeout: None,
            },
        )
        .expect("query should succeed");

        assert_eq!(result.truncated, Some(Truncation::Bytes));
        assert!(
            result.rows.is_empty(),
            "a row over the whole budget must not be returned, got {} row(s)",
            result.rows.len()
        );
        // Columns are still reported so the caller can see the shape of what it
        // asked for.
        assert_eq!(result.columns, vec!["pad"]);
    }

    /// Many small rows trip the byte ceiling too, so the bound holds however the
    /// result is shaped.
    #[test]
    fn the_byte_ceiling_also_bounds_many_small_rows() {
        let result = run_query(
            &[],
            "SELECT repeat('x', 512) AS pad FROM range(10000)",
            [],
            &Limits {
                max_rows: None,
                max_total_bytes: Some(16 * 1024),
                timeout: None,
            },
        )
        .expect("query should succeed");

        assert_eq!(result.truncated, Some(Truncation::Bytes));
        assert!(
            result.rows.len() < 10_000,
            "should have stopped early, got {} rows",
            result.rows.len()
        );
    }

    /// The byte counter must be exact for the serialized form, or a value shaped
    /// to exploit the gap walks under the ceiling: an array of empty strings used
    /// to count ~0 bytes while serializing to 3 bytes per element, letting a
    /// 100 MB response through a 1 MiB ceiling.
    #[test]
    fn json_size_matches_serialized_length_exactly() {
        for value in [
            serde_json::json!(null),
            serde_json::json!(true),
            serde_json::json!(false),
            serde_json::json!(0),
            serde_json::json!(-12345.678),
            serde_json::json!(""),
            serde_json::json!("plain"),
            serde_json::json!("quote\" backslash\\ newline\n tab\t nul\u{0} unicode\u{1F600}é"),
            serde_json::json!([]),
            serde_json::json!(["", "", ""]),
            serde_json::json!([1, [2, [3, "x\ny"]], {"k": null}]),
            serde_json::json!({}),
            serde_json::json!({"a": 1, "b\"": ["c", {"d": false}]}),
        ] {
            let serialized = serde_json::to_string(&value).expect("serialize");
            assert_eq!(
                super::json_size(&value),
                serialized.len(),
                "json_size disagrees with serde_json for {serialized}"
            );
        }
    }

    /// The nested-value bypass, end to end: one row holding a large list of
    /// empty strings must be withheld by the byte ceiling, not returned with
    /// `truncated: false`.
    #[test]
    fn a_nested_value_cannot_walk_under_the_byte_ceiling() {
        let result = run_query(
            &[],
            "SELECT list_transform(range(1000000), x -> '') AS xs",
            [],
            &Limits {
                max_rows: Some(1000),
                max_total_bytes: Some(1024 * 1024),
                timeout: None,
            },
        )
        .expect("query should succeed");

        assert_eq!(result.truncated, Some(Truncation::Bytes));
        assert!(
            result.rows.is_empty(),
            "an oversized nested row must be withheld, got {} row(s)",
            result.rows.len()
        );
    }

    /// Whatever comes back under a byte ceiling must actually serialize inside
    /// it — the counted size is the serialized size, so this holds for any
    /// result shape, nested or flat.
    #[test]
    fn returned_rows_serialize_within_the_byte_ceiling() {
        let budget = 64 * 1024;
        let result = run_query(
            &[],
            "SELECT list_transform(range(200), x -> 'padding \"quoted\"') AS xs, \
             repeat('y', 500) AS pad FROM range(1000)",
            [],
            &Limits {
                max_rows: None,
                max_total_bytes: Some(budget),
                timeout: None,
            },
        )
        .expect("query should succeed");

        assert_eq!(result.truncated, Some(Truncation::Bytes));
        let serialized = serde_json::to_string(&result.rows).expect("serialize rows");
        assert!(
            serialized.len() <= budget,
            "budget was {budget} bytes but rows serialize to {} bytes",
            serialized.len()
        );
    }

    /// A cancel handle stops a running query from another thread — the path an
    /// MCP cancellation takes when the request future is dropped mid-query.
    #[test]
    fn a_cancel_handle_interrupts_a_running_query() {
        let cancel = super::CancelHandle::new();
        let worker_cancel = cancel.clone();
        let started = std::time::Instant::now();
        let worker = std::thread::spawn(move || {
            let session = Session::open().expect("open session");
            if worker_cancel.attach(&session) {
                panic!("handle cancelled before the query started");
            }
            session.query(
                "SELECT count(*) FROM range(1000000000000) AS t(i) WHERE i % 7 = 0",
                [],
                &Limits::none(),
            )
        });

        std::thread::sleep(std::time::Duration::from_millis(300));
        cancel.cancel();
        let result = worker.join().expect("worker should not panic");
        assert!(result.is_err(), "cancelled query should return an error");
        assert!(
            started.elapsed() < std::time::Duration::from_secs(60),
            "cancel took too long: {:?}",
            started.elapsed()
        );
    }

    /// Cancelling before the session exists must be remembered: `attach` reports
    /// it so a caller queued behind the concurrency limit never starts work for
    /// a request that already went away.
    #[test]
    fn a_cancel_before_attach_is_remembered() {
        let cancel = super::CancelHandle::new();
        cancel.cancel();
        let session = Session::open().expect("open session");
        assert!(
            cancel.attach(&session),
            "attach must report a cancellation that happened first"
        );
        // And cancelling after a session is gone is a safe no-op.
        drop(session);
        cancel.cancel();
    }

    /// DuckDB has no statement timeout, so a runaway query is bounded by
    /// interrupting the connection from the host. `range(1e12)` would run
    /// effectively forever; it must come back as an error, not hang the test.
    #[test]
    fn a_runaway_query_is_interrupted_by_the_timeout() {
        let started = std::time::Instant::now();
        let result = run_query(
            &[],
            "SELECT count(*) FROM range(1000000000000) AS t(i) WHERE i % 7 = 0",
            [],
            &Limits {
                max_rows: None,
                max_total_bytes: None,
                timeout: Some(std::time::Duration::from_secs(2)),
            },
        );

        assert!(result.is_err(), "runaway query should have been interrupted");
        assert!(
            started.elapsed() < std::time::Duration::from_secs(60),
            "interrupt took too long: {:?}",
            started.elapsed()
        );
    }

    /// The timeout must not fire on a query that finishes inside it, and the
    /// watcher must not outlive the call.
    #[test]
    fn a_fast_query_is_unaffected_by_an_armed_timeout() {
        let result = run_query(
            &[],
            "SELECT 1 AS x",
            [],
            &Limits {
                max_rows: None,
                max_total_bytes: None,
                timeout: Some(std::time::Duration::from_secs(30)),
            },
        )
        .expect("a fast query should not be interrupted");
        assert_eq!(result.rows, vec![vec![serde_json::json!(1)]]);
    }

    /// `lock_configuration` freezes every later `SET`, so it has to be issued
    /// last or the rest of the lockdown silently fails to apply.
    #[test]
    fn lock_configuration_is_always_the_last_hardening_statement() {
        for hardening in [
            Hardening::default(),
            Hardening {
                deny_external_access: true,
                memory_limit: Some("2GB".to_string()),
                max_temp_directory_size: Some("4GB".to_string()),
            },
        ] {
            let statements = hardening.statements();
            let last = statements.last().expect("hardening should not be empty");
            assert!(
                last.contains("lock_configuration"),
                "lock_configuration must be last, got: {last}"
            );
            assert_eq!(
                statements
                    .iter()
                    .filter(|s| s.contains("lock_configuration"))
                    .count(),
                1
            );
        }
    }

    /// The stricter lockdown a caller with no object-store catalog can take. It
    /// closes network egress, which the default cannot, because an attached
    /// Iceberg catalog is made of S3 reads.
    #[test]
    fn deny_external_access_closes_the_network_the_default_leaves_open() {
        let strict = Hardening {
            deny_external_access: true,
            ..Hardening::default()
        };
        assert!(strict
            .statements()
            .iter()
            .any(|s| s.contains("enable_external_access")));
        assert!(
            !Hardening::default()
                .statements()
                .iter()
                .any(|s| s.contains("enable_external_access")),
            "the default must leave object-store reads working"
        );

        let session = Session::open().expect("open session");
        session.harden(&strict).expect("harden");
        let err = session
            .query(
                "SELECT * FROM read_csv('https://example.com/x.csv')",
                [],
                &Limits::none(),
            )
            .expect_err("external access should be refused");
        let message = err.to_string().to_lowercase();
        assert!(
            message.contains("disabled") || message.contains("permission"),
            "unexpected error: {err}"
        );
    }

    // The read-only gate is unit-tested in `guard.rs`. This helper backs the
    // adversarial suite below, which exercises the gate alongside the hardening.
    fn check(sql: &str) -> ReadOnlyCheck {
        classify_read_only(sql).expect("parser should run")
    }

    #[test]
    fn harden_allows_selects_but_blocks_local_files_and_config_changes() {
        let setup = hardening_statements();

        let ok = run_query(&setup, "SELECT 1 AS x", [], &Limits::none())
            .expect("a plain select should still run under the hardened session");
        assert_eq!(ok.columns, vec!["x"]);
        assert_eq!(ok.rows, vec![vec![serde_json::json!(1)]]);

        let fs_err = run_query(&setup, "SELECT * FROM read_csv('Cargo.toml')", [], &Limits::none())
            .expect_err("local filesystem access should be blocked");
        assert!(
            fs_err.to_string().to_lowercase().contains("disabled"),
            "unexpected error: {fs_err}"
        );

        let cfg_err = run_query(&setup, "SET memory_limit = '1GB'", [], &Limits::none())
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
    /// exercised end to end, NULLs and the row cap included. The `iceberg`
    /// extension is not bundled, so it is fetched on first run and cached; the
    /// test self-skips where that install cannot happen (some CI has no writable
    /// extension directory), the same way the object-store test skips without
    /// Docker.
    #[test]
    fn iceberg_scan_reads_written_table_through_run_query() {
        let conn = duckdb::Connection::open_in_memory().expect("open duckdb");
        // The iceberg extension is fetched at runtime, so a machine that cannot
        // install it (no writable extension directory, no network) is a legitimate
        // skip. Anything else is a real failure: matching on the install error
        // keeps a broken build from turning this into a silent pass.
        if let Err(err) = conn.execute_batch("INSTALL iceberg; LOAD iceberg;") {
            let message = err.to_string().to_lowercase();
            let unavailable = message.contains("install")
                || message.contains("download")
                || message.contains("network")
                || message.contains("access is denied")
                || message.contains("no such file");
            assert!(
                unavailable,
                "iceberg failed for a reason other than being unavailable: {err}"
            );
            eprintln!("skipping iceberg_scan test (iceberg extension unavailable): {err}");
            return;
        }

        let dir = std::env::temp_dir().join(format!("tower_iceberg_test_{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);
        std::fs::create_dir_all(&dir).expect("create temp dir");
        let table = dir.join("events").to_string_lossy().replace('\'', "''");

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
            &Limits::none(),
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
        assert!(!result.is_truncated());

        let capped = run_query(
            &setup,
            &format!("SELECT id FROM iceberg_scan('{table}') ORDER BY id"),
            [],
            &Limits::rows(2),
        )
        .expect("iceberg_scan should read the table");
        assert_eq!(capped.rows.len(), 2);
        assert_eq!(capped.truncated, Some(Truncation::Rows));

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
        run_query(&hardening_statements(), sql, [], &Limits::none())
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
            assert_eq!(check(sql), ReadOnlyCheck::NotReadOnly, "not rejected: {sql}");
        }
        for sql in [
            "SELECT * FROM runs",
            "WITH t AS (SELECT 1) SELECT * FROM t",
            "SELECT count(*) FROM runs",
        ] {
            assert_eq!(check(sql), ReadOnlyCheck::Allowed, "legit read rejected: {sql}");
        }
    }

    #[test]
    fn sandbox_gate_rejects_statement_smuggling() {
        // A trailing statement of any kind is refused: an all-SELECT pair counts
        // as Multiple, a mixed one trips the SELECT-only parser first.
        for sql in [
            "SELECT 1; DROP TABLE runs",
            "SELECT 1; DELETE FROM runs",
            "SELECT 'a;b'; DROP TABLE runs",
            "SELECT 1;\n-- c\nUPDATE runs SET id = 0",
            "SELECT 1; SELECT 2",
        ] {
            assert_ne!(check(sql), ReadOnlyCheck::Allowed, "smuggled statement allowed: {sql}");
        }
        assert_eq!(
            check("SELECT * FROM runs -- a trailing ; comment"),
            ReadOnlyCheck::Allowed
        );
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

    /// Proves no request leaves the process, by counting connections to a listener
    /// we control rather than trusting an error message.
    ///
    /// The earlier version of this test ran through a helper that never loaded
    /// `httpfs`, so it passed for a reason production does not share: with no HTTP
    /// filesystem registered there was nothing to block. This one loads the same
    /// extensions `attach_statements` does before hardening, so it fails if the
    /// sandbox ever stops covering the real configuration.
    #[test]
    fn no_query_can_reach_the_network_under_production_hardening() {
        use std::io::{Read, Write};
        use std::sync::atomic::{AtomicUsize, Ordering};
        use std::sync::Arc;

        let connections = Arc::new(AtomicUsize::new(0));
        let listener = std::net::TcpListener::bind("127.0.0.1:0").expect("bind probe listener");
        let port = listener.local_addr().expect("listener addr").port();
        let counter = connections.clone();
        std::thread::spawn(move || {
            for stream in listener.incoming() {
                counter.fetch_add(1, Ordering::SeqCst);
                if let Ok(mut stream) = stream {
                    let mut buf = [0u8; 1024];
                    let _ = stream.read(&mut buf);
                    let body = "col\nreached\n";
                    let _ = stream.write_all(
                        format!(
                            "HTTP/1.1 200 OK\r\nContent-Length: {}\r\nAccept-Ranges: bytes\r\nConnection: close\r\n\r\n{}",
                            body.len(),
                            body
                        )
                        .as_bytes(),
                    );
                }
            }
        });

        // A control run proves the listener and the URL are reachable at all, so a
        // later "no connections" result means the sandbox stopped it rather than
        // the probe being broken.
        let control = duckdb::Connection::open_in_memory().expect("open duckdb");
        let extensions_available = control.execute_batch("INSTALL httpfs; LOAD httpfs;").is_ok();
        if !extensions_available {
            eprintln!("skipping SSRF test: httpfs extension unavailable");
            return;
        }
        let url = format!("http://127.0.0.1:{port}/probe.csv");
        let reached_without_hardening = control
            .query_row(
                &format!("SELECT count(*) FROM read_csv('{url}')"),
                [],
                |row| row.get::<_, i64>(0),
            )
            .is_ok();
        assert!(
            reached_without_hardening && connections.load(Ordering::SeqCst) > 0,
            "control failed: the probe listener was never reached even unhardened, so this test would pass vacuously"
        );

        let baseline = connections.load(Ordering::SeqCst);
        for sql in [
            "SELECT count(*) FROM read_csv('URL')",
            "SELECT count(*) FROM read_text('URL')",
            "SELECT count(*) FROM read_blob('URL')",
            "SELECT count(*) FROM read_json_auto('URL')",
            "SELECT count(*) FROM 'URL'",
            "SELECT count(*) FROM iceberg_scan('URL')",
            "SELECT count(*) FROM read_csv('http://169.254.169.254/latest/meta-data/')",
        ] {
            let sql = sql.replace("URL", &url);

            // Production runs the gate first and never executes what it refuses,
            // so the test has to as well. Executing regardless would measure the
            // hardening alone, which is not a layer that closes egress: see
            // `hardening_alone_does_not_close_network_egress`.
            let verdict = classify_read_only(&sql).expect("gate should run");
            assert_ne!(
                verdict,
                ReadOnlyCheck::Allowed,
                "the gate must refuse a query that can reach a URL: {sql}"
            );

            let conn = duckdb::Connection::open_in_memory().expect("open duckdb");
            conn.execute_batch("INSTALL httpfs; LOAD httpfs;")
                .expect("load httpfs");
            let _ = conn.execute_batch("INSTALL iceberg; LOAD iceberg;");
            for statement in hardening_statements() {
                conn.execute_batch(&statement).expect("harden session");
            }
            if verdict == ReadOnlyCheck::Allowed {
                let _ = conn.query_row(&sql, [], |row| row.get::<_, i64>(0));
            }
        }

        assert_eq!(
            connections.load(Ordering::SeqCst),
            baseline,
            "a query that survived the gate reached the network"
        );
    }

    /// The layer that is *not* load-bearing here, recorded so nobody assumes it is.
    ///
    /// The session hardening does not close network egress: it cannot, because an
    /// attached Iceberg catalog is made of S3 reads, so `enable_external_access`
    /// has to stay on. On macOS it happens to block HTTP reads anyway, because
    /// disabling LocalFileSystem breaks path resolution before the HTTP filesystem
    /// is consulted. On Linux it does not, and the request goes out. Relying on
    /// that accident is exactly the mistake this test exists to prevent: the
    /// read-only gate's table-function allowlist is what actually stops these.
    #[test]
    fn hardening_alone_does_not_close_network_egress() {
        let conn = duckdb::Connection::open_in_memory().expect("open duckdb");
        if conn.execute_batch("INSTALL httpfs; LOAD httpfs;").is_err() {
            eprintln!("skipping: httpfs extension unavailable");
            return;
        }
        for statement in hardening_statements() {
            conn.execute_batch(&statement).expect("harden session");
        }

        // Whether this reaches the network is platform-dependent, so assert only
        // the part that holds everywhere: hardening does not *refuse* the
        // statement the way the gate does. The error, if any, comes from the read
        // failing, not from the sandbox declining to try.
        let hardened_error = conn
            .query_row(
                "SELECT count(*) FROM read_csv('http://127.0.0.1:9/nothing')",
                [],
                |row| row.get::<_, i64>(0),
            )
            .err()
            .map(|err| err.to_string().to_lowercase());
        if let Some(message) = &hardened_error {
            assert!(
                !message.contains("not allowed") && !message.contains("denied function"),
                "hardening is not the layer that refuses this; the gate is: {message}"
            );
        }

        // The gate is. That is the invariant worth depending on.
        assert_ne!(
            classify_read_only("SELECT count(*) FROM read_csv('http://127.0.0.1:9/nothing')")
                .expect("gate should run"),
            ReadOnlyCheck::Allowed
        );
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

    /// MinIO pinned to an immutable release tag rather than `latest`.
    ///
    /// A floating tag lets a new upstream image change this test's behaviour, or
    /// break it into a skip, without anyone choosing that. A security regression
    /// test should only change when someone means it. Bump deliberately and re-run.
    const MINIO_IMAGE_TAG: &str = "RELEASE.2025-09-07T16-13-09Z";

    /// Whether a container runtime that can run this image is reachable.
    ///
    /// Used to tell an environment that cannot run the test, which is a legitimate
    /// skip, from a container that failed to start, which is a failure worth
    /// surfacing. Treating both as a skip is how a security test quietly becomes a
    /// no-op.
    ///
    /// Windows is excluded outright: MinIO publishes Linux images only, and
    /// Windows CI runs Windows containers, so the pull can never succeed there.
    /// That is a property of the image, not a transient problem, so it is decided
    /// here rather than inferred from a pull error.
    fn can_run_linux_containers() -> bool {
        if cfg!(windows) {
            return false;
        }
        std::process::Command::new("docker")
            .args(["info", "--format", "{{.OSType}}"])
            .output()
            .map(|out| {
                out.status.success() && String::from_utf8_lossy(&out.stdout).trim() == "linux"
            })
            .unwrap_or(false)
    }

    /// The coverage the local-only tests can't give: it proves the hardening does
    /// NOT break a real object-store Iceberg read (the reader uses S3FileSystem,
    /// which the hardening leaves enabled) while local-filesystem access and
    /// configuration changes stay blocked in the same session.
    ///
    /// Skips only when no container runtime is reachable. If Docker is present and
    /// the container will not start, that is a failure, not a skip, so a broken
    /// image or a registry problem cannot turn this into a silent pass.
    #[test]
    fn sandbox_holds_over_object_store_iceberg() {
        use testcontainers::core::{IntoContainerPort, WaitFor};
        use testcontainers::runners::SyncRunner;
        use testcontainers::{GenericImage, ImageExt};

        if !can_run_linux_containers() {
            eprintln!(
                "skipping sandbox_holds_over_object_store_iceberg: no Linux container runtime"
            );
            return;
        }

        let bucket = "warehouse";
        let image = GenericImage::new("minio/minio", MINIO_IMAGE_TAG)
            .with_wait_for(WaitFor::seconds(1))
            .with_exposed_port(9000.tcp())
            .with_entrypoint("sh")
            .with_env_var("MINIO_ROOT_USER", "minioadmin")
            .with_env_var("MINIO_ROOT_PASSWORD", "minioadmin")
            .with_cmd([
                "-c".to_string(),
                format!("mkdir -p /data/{bucket} && exec minio server /data"),
            ]);

        // Docker answered `info` above, so a failure here is a real problem (a bad
        // image, a registry outage, a broken container config) and must fail the
        // test rather than quietly skip it.
        let container = image
            .start()
            .expect("MinIO container failed to start despite a reachable Docker daemon");
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
            &Limits::none(),
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

        let local = run_query(&setup, "SELECT * FROM read_csv('/etc/hostname')", [], &Limits::none())
            .expect_err("local filesystem reads must stay blocked");
        assert!(
            local.to_string().to_lowercase().contains("disabled"),
            "unexpected error: {local}"
        );

        let cfg = run_query(&setup, "SET memory_limit = '1GB'", [], &Limits::none())
            .expect_err("configuration must stay locked");
        let cfg = cfg.to_string().to_lowercase();
        assert!(
            cfg.contains("lock") || cfg.contains("configuration"),
            "unexpected error: {cfg}"
        );
    }
}

