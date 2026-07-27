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

/// Functions refused wherever they appear, whatever the engine says about them.
///
/// Two kinds live here. The first executes SQL built at runtime, which would turn
/// this gate into an execution surface: `query`, `query_table`, and
/// `json_execute_serialized_sql` (the last one ships with the `json` extension
/// this crate enables for the parser, so the gate would otherwise supply its own
/// bypass). The second is effectful table functions, which the engine's
/// `has_side_effects` metadata does not cover because it is NULL for every table
/// function, so nothing but a list can catch them.
pub const ALWAYS_DENIED_FUNCTIONS: &[&str] = &[
    // Executes SQL assembled at runtime.
    "query",
    "query_table",
    "json_execute_serialized_sql",
    // Effectful table functions the engine cannot flag for us.
    "enable_logging",
    "disable_logging",
    "truncate_duckdb_logs",
    "checkpoint",
    "force_checkpoint",
    // Discloses vended credentials.
    "duckdb_secrets",
];

/// Table functions a catalog query may use. Anything else in `FROM` position is
/// refused.
///
/// This is the fail-closed half of the gate and the reason it does not rely on
/// naming every dangerous function. A catalog query reads base tables in the
/// attached catalog, which are not functions at all, so the legitimate
/// table-function surface is tiny. The `read_*`/`glob`/`*_scan` family is
/// deliberately absent: those are the file-read and network-egress vectors, and
/// they are not needed to query an attached catalog. A caller that genuinely
/// needs them can widen the set through [`classify_read_only_with`].
pub const ALLOWED_TABLE_FUNCTIONS: &[&str] = &[
    "range",
    "generate_series",
    "unnest",
    "iceberg_scan",
    "iceberg_metadata",
    "iceberg_snapshots",
];

/// What a caller will and will not allow in untrusted SQL.
#[derive(Debug, Clone)]
pub struct FunctionPolicy<'a> {
    /// Refused wherever they appear.
    pub always_denied: &'a [&'a str],
    /// The only table functions permitted in `FROM` position.
    pub allowed_table_functions: &'a [&'a str],
    /// Ask the engine which scalar functions have side effects and refuse those.
    /// Engine-sourced, so it keeps up with DuckDB rather than drifting.
    pub deny_side_effecting_scalars: bool,
}

impl Default for FunctionPolicy<'static> {
    fn default() -> Self {
        Self {
            always_denied: ALWAYS_DENIED_FUNCTIONS,
            allowed_table_functions: ALLOWED_TABLE_FUNCTIONS,
            deny_side_effecting_scalars: true,
        }
    }
}

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
    classify_read_only_with(conn, sql, &FunctionPolicy::default())
}

/// [`classify_read_only_on`] under an explicit [`FunctionPolicy`], for a caller
/// that needs to widen or narrow what functions are permitted. Names are matched
/// case-insensitively against the parsed tree, never the raw SQL text.
pub fn classify_read_only_with(
    conn: &duckdb::Connection,
    sql: &str,
    policy: &FunctionPolicy<'_>,
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

    let calls = collect_function_calls(&parsed);

    // 1. Names refused wherever they appear.
    if let Some(name) = calls
        .all
        .iter()
        .find(|name| policy.always_denied.iter().any(|d| d.eq_ignore_ascii_case(name)))
    {
        return Ok(ReadOnlyCheck::DeniedFunction(name.clone()));
    }

    // 2. Table functions are allowlisted, so an unknown one is refused rather
    //    than waved through. This is what keeps the gate fail-closed as DuckDB
    //    and its extensions add functions we have never heard of.
    if let Some(name) = calls.table_functions.iter().find(|name| {
        !policy
            .allowed_table_functions
            .iter()
            .any(|a| a.eq_ignore_ascii_case(name))
    }) {
        return Ok(ReadOnlyCheck::DeniedFunction(name.clone()));
    }

    // 3. Scalars are too numerous to allowlist, so ask the engine which ones have
    //    side effects. `has_side_effects` is NULL for table functions, which is
    //    why those are handled above instead.
    if policy.deny_side_effecting_scalars && !calls.all.is_empty() {
        let effectful = side_effecting_functions(conn)?;
        if let Some(name) = calls.all.iter().find(|name| effectful.contains(*name)) {
            return Ok(ReadOnlyCheck::DeniedFunction(name.clone()));
        }
    }

    Ok(ReadOnlyCheck::Allowed)
}

/// Function names used by a statement, split by the position they appear in.
#[derive(Default)]
struct FunctionCalls {
    /// Every function name in the statement, lowercased.
    all: std::collections::BTreeSet<String>,
    /// Just the ones in `FROM` position.
    table_functions: std::collections::BTreeSet<String>,
}

/// Walks the serialized parse tree collecting function names, noting which sit in
/// `FROM` position.
///
/// This reads typed nodes rather than pattern-matching JSON text, because the
/// serialized shape is not stable across DuckDB versions and a substring match on
/// raw SQL would be defeated by comments and quoting. A table function appears as
/// a `from_table` node of type `TABLE_FUNCTION` carrying a nested `function`; a
/// scalar is any other node with a `function_name`. If a future DuckDB renames
/// those keys this walk quietly stops matching, so every denial below is covered
/// by a test that fails loudly the moment it stops being refused.
fn collect_function_calls(node: &serde_json::Value) -> FunctionCalls {
    let mut calls = FunctionCalls::default();
    walk_function_calls(node, &mut calls);
    calls
}

fn walk_function_calls(node: &serde_json::Value, calls: &mut FunctionCalls) {
    match node {
        serde_json::Value::Object(fields) => {
            if fields.get("type").and_then(serde_json::Value::as_str) == Some("TABLE_FUNCTION") {
                if let Some(name) = fields
                    .get("function")
                    .and_then(|f| f.get("function_name"))
                    .and_then(serde_json::Value::as_str)
                {
                    calls.table_functions.insert(name.to_lowercase());
                }
            }
            if let Some(name) = fields.get("function_name").and_then(serde_json::Value::as_str) {
                calls.all.insert(name.to_lowercase());
            }
            for value in fields.values() {
                walk_function_calls(value, calls);
            }
        }
        serde_json::Value::Array(items) => {
            for item in items {
                walk_function_calls(item, calls);
            }
        }
        _ => {}
    }
}

/// The scalar functions DuckDB reports as having side effects, lowercased.
///
/// Sourcing this from the engine rather than a hand-kept list means a function
/// added by a future DuckDB is refused without us noticing it exists. It only
/// covers functions registered on `conn`, so a caller classifying against a
/// throwaway connection will not see extension-provided scalars; the
/// always-denied list carries the ones that matters for.
fn side_effecting_functions(
    conn: &duckdb::Connection,
) -> Result<std::collections::BTreeSet<String>, duckdb::Error> {
    let mut stmt = conn.prepare(
        "SELECT DISTINCT lower(function_name) FROM duckdb_functions() WHERE has_side_effects",
    )?;
    let mut names = std::collections::BTreeSet::new();
    let mut rows = stmt.query([])?;
    while let Some(row) = rows.next()? {
        names.insert(row.get::<_, String>(0)?);
    }
    Ok(names)
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
    fn table_functions_that_reach_a_file_or_a_url_are_refused_by_the_allowlist() {
        // These used to be Allowed here, on the reasoning that the session
        // hardening would refuse the read at execution time. That left the gate
        // depending on a filesystem setting to cover a network vector, so the
        // table-function position is now allowlisted and these are refused
        // outright, before anything runs.
        for (sql, func) in [
            ("SELECT * FROM read_csv('/etc/passwd')", "read_csv"),
            (
                "SELECT * FROM read_parquet('https://example.com/x.parquet')",
                "read_parquet",
            ),
            ("SELECT * FROM read_text('/etc/hostname')", "read_text"),
            ("SELECT * FROM read_blob('/etc/hostname')", "read_blob"),
            ("SELECT * FROM glob('/etc/*')", "glob"),
        ] {
            assert_eq!(
                check(sql),
                ReadOnlyCheck::DeniedFunction(func.to_string()),
                "should refuse {func} in: {sql}"
            );
        }
    }

    #[test]
    fn the_table_function_allowlist_still_permits_catalog_reads() {
        // The point of the allowlist is to refuse the unknown without getting in
        // the way of an ordinary catalog query. Base tables are not functions at
        // all, so the common case is untouched.
        for sql in [
            "SELECT * FROM runs",
            "SELECT * FROM \"default\".bronze.runs WHERE id > 0",
            "SELECT count(*) FROM range(10)",
            "SELECT * FROM generate_series(1, 5)",
            "WITH x AS (SELECT * FROM runs) SELECT count(*) FROM x",
        ] {
            assert_eq!(check(sql), ReadOnlyCheck::Allowed, "should allow: {sql}");
        }
    }

    #[test]
    fn an_unknown_table_function_is_refused_rather_than_waved_through() {
        // The fail-closed property: a function nobody has heard of, which a future
        // DuckDB or extension might add, is refused because it is not on the
        // allowlist. A denylist would have admitted it.
        assert_eq!(
            check("SELECT * FROM some_brand_new_table_function('x')"),
            ReadOnlyCheck::DeniedFunction("some_brand_new_table_function".to_string())
        );
    }

    #[test]
    fn the_json_executor_bundled_for_the_parser_cannot_be_used_as_a_bypass() {
        // This crate enables the `json` extension so the gate can parse SQL, and
        // that same extension ships `json_execute_serialized_sql`, which runs
        // whatever it is handed. The outer statement is a perfectly ordinary
        // SELECT, so only an explicit denial catches it.
        for sql in [
            "SELECT * FROM json_execute_serialized_sql(json_serialize_sql('SELECT 1'))",
            "SELECT json_execute_serialized_sql(json_serialize_sql('SELECT 1'))",
        ] {
            assert_eq!(
                check(sql),
                ReadOnlyCheck::DeniedFunction("json_execute_serialized_sql".to_string()),
                "the json executor must not be reachable: {sql}"
            );
        }
    }

    #[test]
    fn effectful_functions_are_refused_whether_or_not_the_engine_flags_them() {
        // `has_side_effects` is true for these scalars, so the engine tells us.
        for (sql, func) in [
            ("SELECT nextval('s')", "nextval"),
            ("SELECT currval('s')", "currval"),
            ("SELECT setseed(0.5)", "setseed"),
        ] {
            assert_eq!(
                check(sql),
                ReadOnlyCheck::DeniedFunction(func.to_string()),
                "engine-flagged effectful scalar should be refused: {sql}"
            );
        }
        // `has_side_effects` is NULL for every table function, so the engine
        // cannot help here and the explicit list has to.
        for (sql, func) in [
            ("SELECT * FROM enable_logging()", "enable_logging"),
            ("SELECT * FROM duckdb_secrets()", "duckdb_secrets"),
        ] {
            assert_eq!(
                check(sql),
                ReadOnlyCheck::DeniedFunction(func.to_string()),
                "effectful table function should be refused: {sql}"
            );
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


