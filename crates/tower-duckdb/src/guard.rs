//! Read-only gate on untrusted SQL, applied before a statement runs.
//!
//! This gate is defence in depth, not the security boundary. The load-bearing
//! control is the engine-enforced privilege: `catalogs query` vends read-only
//! credentials and attaches the catalog `READ_ONLY`, so a write is refused by the
//! catalog regardless of what this module concludes. The gate exists to refuse
//! bad input early, with a clear message, and to narrow the gap between "the
//! credential is read-only" and "the statement is a read".
//!
//! The check runs the SQL through DuckDB's own parser via `json_serialize_sql`,
//! which parses (but does not execute) and serializes only `SELECT` statements,
//! erroring on everything else. Using the engine's parser rather than scanning
//! keywords is what makes this workable: a keyword denylist misses comment tricks
//! (a `--` comment ends at `\r` as well as `\n` in DuckDB, so a `-- x\rDROP …`
//! payload looks empty to a naive scanner but parses as a DROP) and statements
//! that open with an allowed keyword but still mutate. The parser sees the
//! statement the way the executor will.
//!
//! Parsing as a `SELECT` is a statement *shape*, not a read-only property, so
//! shape alone is not enough. Two classes of SELECT-shaped statement still act:
//! functions that mutate engine state (`nextval` advances a sequence) and
//! functions that execute dynamically-built SQL (`query`, `query_table`). Those
//! are refused by name from the parsed tree, see [`MUTATING_OR_DYNAMIC_FUNCTIONS`].
//! A `SELECT` that reads a file or a URL through a table function is still
//! allowed here; the session hardening is what refuses that read at execution.
//!
//! Every judgement in this module is pinned by tests against the DuckDB build we
//! ship, because both the grammar and the serialized JSON shape change between
//! versions. Re-run them on every DuckDB upgrade.

/// Row cap for agent-issued queries. Rows past this are dropped and the result
/// is flagged truncated.
///
/// A row cap alone bounds very little: `SELECT string_agg(email, ',') FROM users`
/// returns a whole column in one row. Pair it with [`AGENT_MAX_RESULT_BYTES`],
/// which is what actually bounds how much data a query carries back.
pub const AGENT_MAX_ROWS: usize = 1_000;

/// Byte ceiling on a whole agent result set, measured as values are read. This is
/// the cap that survives aggregation tricks (`string_agg`, `list`, `to_json`)
/// that pack many rows into few.
pub const AGENT_MAX_RESULT_BYTES: usize = 1 << 20;

/// Wall-clock ceiling on a single agent query. DuckDB has no statement timeout of
/// its own, so this is enforced from the host by interrupting the connection.
pub const AGENT_QUERY_TIMEOUT: std::time::Duration = std::time::Duration::from_secs(60);

/// Functions refused even inside an otherwise valid `SELECT`.
///
/// `nextval`/`currval` mutate sequence state, so they are writes wearing a
/// SELECT's clothes. `query`/`query_table` hand a string to DuckDB's execution
/// pipeline, which turns this gate's allowlist into an execution surface. None of
/// them have a legitimate use in a catalog data query.
///
/// This deliberately excludes the `read_*`/`glob`/`*_scan` family: those are how a
/// catalog query legitimately reads Parquet and Iceberg over object storage.
/// Reaching the *local* filesystem through them is refused by the session
/// hardening instead.
pub const MUTATING_OR_DYNAMIC_FUNCTIONS: &[&str] = &["nextval", "currval", "query", "query_table"];

/// The verdict for a piece of untrusted SQL.
#[derive(Debug, PartialEq, Eq, Clone)]
pub enum ReadOnlyCheck {
    /// Exactly one `SELECT` statement, calling nothing from the denied set.
    Allowed,
    /// No statement at all (blank or comment-only input).
    Empty,
    /// More than one statement. Rejected because duckdb-rs `prepare` executes
    /// every statement but the last as a side effect: preparing
    /// `DELETE FROM t; SELECT 1` deletes the rows and hands back the SELECT, so a
    /// second statement must never reach it. Verified against the DuckDB build we
    /// ship, in `prepare_executes_all_but_the_last_statement`.
    Multiple,
    /// Parses as something other than a single `SELECT` (a write, DDL, `PRAGMA`,
    /// `SET`, `COPY`, `ATTACH`, …) or does not parse at all. Rejected fail-closed.
    NotReadOnly,
    /// Parses as a `SELECT` but calls a function that mutates state or executes
    /// dynamically-built SQL. Carries the offending name for the error message.
    DeniedFunction(String),
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
    classify_read_only_with(conn, sql, MUTATING_OR_DYNAMIC_FUNCTIONS)
}

/// [`classify_read_only_on`] with an explicit set of denied function names, for a
/// caller that wants to refuse more than the default (an agent path with no
/// business reading object storage might also deny the `read_*` family). Names are
/// matched case-insensitively against the parsed tree, never the raw SQL text.
pub fn classify_read_only_with(
    conn: &duckdb::Connection,
    sql: &str,
    denied_functions: &[&str],
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

    match statements {
        0 => return Ok(ReadOnlyCheck::Empty),
        1 => {}
        _ => return Ok(ReadOnlyCheck::Multiple),
    }

    if let Some(name) = find_denied_function(&parsed, denied_functions) {
        return Ok(ReadOnlyCheck::DeniedFunction(name));
    }
    Ok(ReadOnlyCheck::Allowed)
}

/// Walks the serialized parse tree for a call to any denied function, scalar or
/// table-valued, at any depth.
///
/// This reads `function_name` values out of the tree rather than pattern-matching
/// JSON text, because the serialized shape is not stable across DuckDB versions
/// and a substring match on raw SQL would be defeated by comments and quoting. If
/// a future DuckDB renames that key this walk silently stops matching, so each
/// denial is covered by a test that fails loudly when it stops being refused.
fn find_denied_function(node: &serde_json::Value, denied: &[&str]) -> Option<String> {
    match node {
        serde_json::Value::Object(fields) => {
            if let Some(serde_json::Value::String(name)) = fields.get("function_name") {
                if denied.iter().any(|d| d.eq_ignore_ascii_case(name)) {
                    return Some(name.to_lowercase());
                }
            }
            fields
                .values()
                .find_map(|value| find_denied_function(value, denied))
        }
        serde_json::Value::Array(items) => items
            .iter()
            .find_map(|item| find_denied_function(item, denied)),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::{classify_read_only, classify_read_only_on, ReadOnlyCheck};

    fn check(sql: &str) -> ReadOnlyCheck {
        classify_read_only(sql).expect("the parser query should run")
    }

    #[test]
    fn allows_a_single_select_in_its_many_shapes() {
        // Everything DuckDB parses as one read: plain SELECTs, CTEs, set
        // operations, subqueries, and the SELECT-sugar forms an agent might emit.
        for sql in [
            "SELECT 1",
            "select 1",
            "  SELECT 1  ",
            "SELECT * FROM runs WHERE id > 0",
            "SELECT count(*) FROM runs",
            "WITH x AS (SELECT 1) SELECT * FROM x",
            "WITH RECURSIVE t(n) AS (SELECT 1 UNION SELECT n + 1 FROM t WHERE n < 3) SELECT * FROM t",
            "SELECT 1 UNION SELECT 2",
            "(SELECT 1)",
            "VALUES (1), (2)",
            "TABLE runs",
            "FROM runs",
            "DESCRIBE SELECT 1",
            "SUMMARIZE SELECT 1",
            "SHOW TABLES",
            "SHOW ALL TABLES",
        ] {
            assert_eq!(check(sql), ReadOnlyCheck::Allowed, "should allow: {sql}");
        }
    }

    #[test]
    fn leading_comments_and_whitespace_do_not_change_the_verdict() {
        for sql in [
            "-- a comment\nSELECT 1",
            "/* a comment */ SELECT 1",
            "\n\t  SELECT 1",
            "SELECT 1 -- trailing line comment",
            "SELECT 1 /* trailing block comment */",
        ] {
            assert_eq!(check(sql), ReadOnlyCheck::Allowed, "should allow: {sql}");
        }
    }

    #[test]
    fn semicolons_inside_literals_and_comments_are_not_separators() {
        // A single statement whose text merely contains `;` in a string, a
        // dollar-quoted string, or a comment stays a single statement.
        for sql in [
            "SELECT 'a;b'",
            "SELECT $$a;b$$",
            "SELECT 1 -- ; not a separator",
            "SELECT /* ; */ 1",
            "SELECT 1;",
            "SELECT 1 ;  ",
            "SELECT 1 \t ; \n ",
            "SELECT 1;;",
        ] {
            assert_eq!(check(sql), ReadOnlyCheck::Allowed, "should allow: {sql}");
        }
    }

    #[test]
    fn rejects_writes_and_ddl() {
        for sql in [
            "INSERT INTO runs VALUES (1)",
            "insert into runs values (1)",
            "UPDATE runs SET id = 0",
            "DELETE FROM runs",
            "MERGE INTO runs USING x ON true WHEN MATCHED THEN DELETE",
            "CREATE TABLE evil AS SELECT 1",
            "CREATE OR REPLACE TABLE runs AS SELECT 1",
            "DROP TABLE runs",
            "ALTER TABLE runs ADD COLUMN x INTEGER",
            "TRUNCATE runs",
            "COPY runs TO '/tmp/exfil.csv'",
            "ATTACH '/tmp/evil.db' AS e",
            "DETACH runs",
        ] {
            assert_eq!(check(sql), ReadOnlyCheck::NotReadOnly, "should reject: {sql}");
        }
    }

    #[test]
    fn rejects_config_transaction_and_meta_statements() {
        // Statements that are neither writes nor plain SELECTs still must not run
        // on the read-only path: they can change session state or the plan.
        for sql in [
            "SET memory_limit = '1GB'",
            "RESET memory_limit",
            "PRAGMA database_list",
            "PRAGMA disable_verification",
            "BEGIN",
            "COMMIT",
            "ROLLBACK",
            "PREPARE p AS SELECT 1",
            "EXECUTE p",
            "CALL pragma_version()",
            "EXPLAIN SELECT 1",
        ] {
            assert_eq!(check(sql), ReadOnlyCheck::NotReadOnly, "should reject: {sql}");
        }
    }

    #[test]
    fn a_leading_select_does_not_launder_a_trailing_mutation() {
        // The bypass class the gate exists for: a statement that opens with an
        // allowed keyword but carries a write. A first-keyword denylist would let
        // these through; the parser does not.
        for sql in [
            // A `--` comment ends at a carriage return in DuckDB, so this parses
            // as a DROP even though it opens with a full-line comment.
            "-- harmless\rDROP TABLE runs",
            // A data-modifying CTE.
            "WITH x AS (DELETE FROM runs RETURNING *) SELECT * FROM x",
        ] {
            assert_eq!(check(sql), ReadOnlyCheck::NotReadOnly, "should reject: {sql}");
        }
        // The same shapes without the mutation stay allowed.
        assert_eq!(check("-- harmless\r\nSELECT 1"), ReadOnlyCheck::Allowed);
        assert_eq!(
            check("WITH x AS (SELECT 1) SELECT * FROM x"),
            ReadOnlyCheck::Allowed
        );
    }

    #[test]
    fn rejects_multiple_statements() {
        // Two statements must never reach the query path: duckdb-rs `prepare`
        // runs every statement but the last as a side effect. An all-SELECT pair
        // is Multiple; a mix trips the SELECT-only parser first.
        assert_eq!(check("SELECT 1; SELECT 2"), ReadOnlyCheck::Multiple);
        assert_eq!(check("SELECT 'a;b'; SELECT 2"), ReadOnlyCheck::Multiple);
        for sql in [
            "SELECT 1; DROP TABLE runs",
            "SELECT 1; DELETE FROM runs",
            "SELECT 1;\n-- c\nUPDATE runs SET id = 0",
        ] {
            assert_ne!(check(sql), ReadOnlyCheck::Allowed, "smuggled write allowed: {sql}");
        }
    }

    #[test]
    fn empty_and_comment_only_input_is_empty_not_allowed() {
        for sql in ["", "   ", "\n\t  ", "-- just a comment", "/* only a block */"] {
            assert_eq!(check(sql), ReadOnlyCheck::Empty, "should be empty: {sql:?}");
        }
    }

    #[test]
    fn unparseable_input_is_rejected_fail_closed() {
        for sql in ["not valid sql at all", "SELECT FROM WHERE", "SELECT ((("] {
            assert_eq!(check(sql), ReadOnlyCheck::NotReadOnly, "should reject: {sql}");
        }
    }

    #[test]
    fn rejects_functions_that_mutate_state_or_build_sql_dynamically() {
        // These parse as perfectly good SELECTs, so the parser alone would let
        // them through. `nextval` really does advance a sequence (see
        // `nextval_is_a_select_that_mutates`), and `query`/`query_table` hand a
        // string to the execution pipeline.
        for (sql, expected) in [
            ("SELECT nextval('s')", "nextval"),
            ("SELECT NEXTVAL('s')", "nextval"),
            ("SELECT currval('s')", "currval"),
            ("SELECT * FROM query('SELECT 1')", "query"),
            ("SELECT * FROM query_table('t')", "query_table"),
            // Nested well below the top level, to prove the walk is not shallow.
            (
                "WITH x AS (SELECT nextval('s') AS n) SELECT sum(n) FROM x",
                "nextval",
            ),
            ("SELECT (SELECT max(v) FROM (SELECT nextval('s') v))", "nextval"),
        ] {
            assert_eq!(
                check(sql),
                ReadOnlyCheck::DeniedFunction(expected.to_string()),
                "should deny {expected} in: {sql}"
            );
        }
    }

    #[test]
    fn a_denied_name_used_as_an_identifier_is_not_a_call() {
        // The denial matches parsed function calls, not text, so a column or alias
        // that happens to share the name is still a fine read.
        for sql in [
            "SELECT query FROM runs",
            "SELECT 1 AS nextval",
            "SELECT 'nextval(x)' AS literal_text",
            "SELECT * FROM runs -- nextval('s')",
        ] {
            assert_eq!(check(sql), ReadOnlyCheck::Allowed, "should allow: {sql}");
        }
    }

    /// Pins the reason `nextval` is on the denylist: it is a SELECT that writes.
    /// If a DuckDB upgrade ever made this non-mutating the denial could be
    /// revisited, and if the denial is dropped while this still mutates, the test
    /// above starts failing.
    #[test]
    fn nextval_is_a_select_that_mutates() {
        let conn = duckdb::Connection::open_in_memory().expect("open duckdb");
        conn.execute_batch("CREATE SEQUENCE s START 1")
            .expect("create sequence");
        let first: i64 = conn
            .query_row("SELECT nextval('s')", [], |row| row.get(0))
            .expect("nextval");
        let second: i64 = conn
            .query_row("SELECT nextval('s')", [], |row| row.get(0))
            .expect("nextval");
        assert_ne!(
            first, second,
            "nextval no longer mutates; revisit MUTATING_OR_DYNAMIC_FUNCTIONS"
        );
    }

    /// Pins the reason multi-statement input is refused, and guards the claim in
    /// `ReadOnlyCheck::Multiple`. duckdb-rs `prepare` runs every statement but the
    /// last, so the leading statement takes effect even though only the final one
    /// is returned. If a future duckdb-rs changes this to a hard error the test
    /// fails and the doc comment needs updating, but the gate stays correct.
    #[test]
    fn prepare_executes_all_but_the_last_statement() {
        let conn = duckdb::Connection::open_in_memory().expect("open duckdb");
        conn.execute_batch("CREATE TABLE t(id INTEGER); INSERT INTO t VALUES (1), (2)")
            .expect("seed table");

        let _ = conn.prepare("DELETE FROM t; SELECT 1");

        let remaining: i64 = conn
            .query_row("SELECT count(*) FROM t", [], |row| row.get(0))
            .expect("count");
        assert_eq!(
            remaining, 0,
            "prepare no longer executes leading statements; revisit the Multiple rationale"
        );
    }

    /// A DuckDB version canary. Data-modifying CTEs do not parse today ("A CTE
    /// needs a SELECT"), so they land in `NotReadOnly`. Upstream has work to allow
    /// DML as a CTE body; if that ships, these gain an outer SELECT and could
    /// start classifying as `Allowed` while still deleting rows. This test fails
    /// the moment that changes, which is the signal to add an explicit CTE check.
    #[test]
    fn data_modifying_ctes_do_not_parse_as_selects() {
        for sql in [
            "WITH x AS (DELETE FROM runs RETURNING *) SELECT * FROM x",
            "WITH x AS (INSERT INTO runs VALUES (9) RETURNING *) SELECT * FROM x",
            "WITH x AS (UPDATE runs SET id = 5 RETURNING *) SELECT * FROM x",
        ] {
            assert_eq!(
                check(sql),
                ReadOnlyCheck::NotReadOnly,
                "DML-in-CTE now parses as a SELECT; the gate needs an explicit check: {sql}"
            );
        }
    }

    #[test]
    fn table_functions_reaching_the_host_are_a_matter_for_the_hardening_not_the_gate() {
        // The gate only classifies statement shape. A SELECT that reads a local
        // file or a URL is a valid SELECT and is Allowed here; the session
        // hardening (disabled_filesystems, no external access) is what refuses the
        // actual read at execution time. This test documents that boundary so a
        // future reader does not mistake the gate for the filesystem defense.
        for sql in [
            "SELECT * FROM read_csv('/etc/passwd')",
            "SELECT * FROM read_parquet('https://example.com/x.parquet')",
        ] {
            assert_eq!(check(sql), ReadOnlyCheck::Allowed, "gate classifies shape only: {sql}");
        }
    }

    #[test]
    fn classify_on_a_shared_connection_matches_the_owning_variant() {
        // The reuse path an MCP server would take: one connection, many queries.
        let conn = duckdb::Connection::open_in_memory().expect("open duckdb");
        assert_eq!(
            classify_read_only_on(&conn, "SELECT 1").unwrap(),
            ReadOnlyCheck::Allowed
        );
        assert_eq!(
            classify_read_only_on(&conn, "DROP TABLE runs").unwrap(),
            ReadOnlyCheck::NotReadOnly
        );
        assert_eq!(
            classify_read_only_on(&conn, "SELECT 1; SELECT 2").unwrap(),
            ReadOnlyCheck::Multiple
        );
    }
}


