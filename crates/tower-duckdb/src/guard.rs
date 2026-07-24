//! Read-only gate on untrusted SQL, applied before a statement runs. It is
//! defence in depth on top of read-only credentials and the session hardening:
//! it rejects anything that is not a single `SELECT`, and caps how many rows an
//! agent query may pull back.
//!
//! The check runs the SQL through DuckDB's own parser via `json_serialize_sql`,
//! which parses (but does not execute) a statement and serializes only `SELECT`
//! statements, erroring on everything else. Using the engine's parser rather
//! than scanning keywords is what makes this safe: a keyword denylist misses
//! comment tricks (a `--` comment ends at `\r` as well as `\n` in DuckDB, so a
//! `-- x\rDROP …` payload looks empty to a naive scanner but parses as a DROP)
//! and statements that start with an allowed keyword but still mutate (a `WITH …`
//! CTE, for one). The parser sees them the way the executor will.

/// Row cap for agent-issued queries. Rows past this are dropped and the result
/// is flagged truncated, so a model cannot pull an unbounded table into memory
/// or its context.
pub const AGENT_MAX_ROWS: usize = 1_000;

/// The verdict for a piece of untrusted SQL.
#[derive(Debug, PartialEq, Eq, Clone, Copy)]
pub enum ReadOnlyCheck {
    /// Exactly one `SELECT` statement. Safe to run under a read-only session.
    Allowed,
    /// No statement at all (blank or comment-only input).
    Empty,
    /// More than one statement. Rejected: duckdb-rs `prepare` executes every
    /// statement but the last as a side effect, so a second statement must never
    /// reach it.
    Multiple,
    /// Parses as something other than a single `SELECT` (a write, DDL, `PRAGMA`,
    /// `SET`, `COPY`, `ATTACH`, …) or does not parse at all. Rejected fail-closed.
    NotReadOnly,
}

/// Classify untrusted `sql` for the read-only path using DuckDB's parser. Opens a
/// throwaway in-memory connection with no catalog attached, so the parse cannot
/// touch customer data even in principle. Returns a `duckdb::Error` only if the
/// parser query itself cannot run; a response it cannot make sense of is treated
/// as [`ReadOnlyCheck::NotReadOnly`] (fail closed).
pub fn classify_read_only(sql: &str) -> Result<ReadOnlyCheck, duckdb::Error> {
    let conn = duckdb::Connection::open_in_memory()?;
    classify_read_only_on(&conn, sql)
}

/// [`classify_read_only`] against a caller-supplied connection, so a long-lived
/// caller (an MCP server) can reuse one connection instead of opening a fresh one
/// per query. The connection is only used to run `json_serialize_sql`, which does
/// not execute `sql`.
pub fn classify_read_only_on(
    conn: &duckdb::Connection,
    sql: &str,
) -> Result<ReadOnlyCheck, duckdb::Error> {
    // `json_serialize_sql` parses and serializes SELECT statements to JSON and
    // errors on anything else. The SQL is bound as a parameter, never spliced
    // into this query.
    let serialized: String =
        conn.query_row("SELECT json_serialize_sql(CAST(? AS VARCHAR))", [sql], |row| {
            row.get(0)
        })?;

    let parsed: serde_json::Value = match serde_json::from_str(&serialized) {
        Ok(value) => value,
        // DuckDB always returns valid JSON here; an unparseable response means
        // something we don't understand, so refuse it rather than guess.
        Err(_) => return Ok(ReadOnlyCheck::NotReadOnly),
    };

    // `error: true` covers both non-SELECT statements ("Only SELECT statements
    // can be serialized to json!") and malformed SQL.
    if parsed
        .get("error")
        .and_then(serde_json::Value::as_bool)
        .unwrap_or(true)
    {
        return Ok(ReadOnlyCheck::NotReadOnly);
    }

    let statements = parsed
        .get("statements")
        .and_then(serde_json::Value::as_array)
        .map_or(0, Vec::len);

    Ok(match statements {
        0 => ReadOnlyCheck::Empty,
        1 => ReadOnlyCheck::Allowed,
        _ => ReadOnlyCheck::Multiple,
    })
}
