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
