use clap::{value_parser, Arg, ArgAction, ArgMatches, Command};
use colored::Colorize;
use config::Config;
use futures_util::StreamExt;
use std::io::{IsTerminal, Read};
use std::time::{Duration, Instant};
use tower_api::models::{
    vend_catalog_credentials_body, CatalogCredentials, DescribeCatalogResponse,
};
use tower_telemetry::debug;

use crate::{api, beta, output, util::cmd};

const STORAGE_CATALOG_TYPE: &str = "tower-catalog";

/// Query-sandbox primitives for untrusted (agent) callers. These are the gates
/// and the DuckDB session lockdown a future MCP `tower_catalogs_query` tool will
/// apply to agent-issued SQL: reject write/DDL and multi-statement input, cap
/// the row count, and lock the session down so a query cannot read the local
/// filesystem, load community extensions, or unwind the settings. Nothing wires
/// these into the query path yet, so `dead_code` is allowed here; the
/// adversarial test suite exercises them directly.
#[allow(dead_code)]
mod sandbox {
    /// Row cap for agent-issued queries. Rows past this are dropped and the
    /// caller is told the set was truncated, so a model cannot pull an unbounded
    /// table into memory or its context.
    pub(super) const AGENT_MAX_ROWS: usize = 1_000;

    /// Leading keywords that write data or schema, or repoint the session. An
    /// agent query starting with one of these is refused, as defence in depth on
    /// top of the read-only credentials it is given.
    const WRITE_LEADING_KEYWORDS: &[&str] = &[
        "insert", "update", "delete", "merge", "create", "drop", "alter", "truncate", "replace",
        "copy", "attach", "detach",
    ];

    /// Statements that lock an attached DuckDB session down before an untrusted
    /// query runs: no local-filesystem access (so `read_csv('/etc/passwd')` and
    /// friends fail), no community extensions, and a configuration lock so the
    /// query cannot unwind any of it. These run after the catalog is attached,
    /// which is what installs extensions and reaches the network. Network access
    /// stays on because httpfs is how the attached Iceberg catalog reads its
    /// data, so this narrows but does not eliminate the query surface.
    pub(super) fn agent_hardening_statements() -> Vec<String> {
        vec![
            "SET disabled_filesystems = 'LocalFileSystem'".to_string(),
            "SET allow_community_extensions = false".to_string(),
            "SET lock_configuration = true".to_string(),
        ]
    }

    /// The leading SQL keyword, lowercased, after skipping leading whitespace and
    /// `--` / `/* */` comments.
    pub(super) fn first_sql_keyword(sql: &str) -> String {
        let mut s = sql.trim_start();
        loop {
            if let Some(rest) = s.strip_prefix("--") {
                match rest.find('\n') {
                    Some(nl) => s = rest[nl + 1..].trim_start(),
                    None => return String::new(),
                }
            } else if let Some(rest) = s.strip_prefix("/*") {
                match rest.find("*/") {
                    Some(end) => s = rest[end + 2..].trim_start(),
                    None => return String::new(),
                }
            } else {
                break;
            }
        }
        s.chars()
            .take_while(|c| c.is_ascii_alphabetic())
            .collect::<String>()
            .to_lowercase()
    }

    /// True when `sql` starts with a write/DDL keyword.
    pub(super) fn is_write_statement(sql: &str) -> bool {
        WRITE_LEADING_KEYWORDS.contains(&first_sql_keyword(sql).as_str())
    }

    /// True when `sql` holds more than one statement. A `;` inside a string
    /// literal or comment is data, not a separator, so those spans are skipped.
    /// This gate matters because duckdb-rs `prepare` runs every statement but the
    /// last as a side effect, so unguarded multi-statement SQL would execute its
    /// leading statements even though only the final one is returned.
    pub(super) fn contains_multiple_statements(sql: &str) -> bool {
        #[derive(PartialEq)]
        enum State {
            Normal,
            Single,
            Double,
            Line,
            Block,
        }

        let mut state = State::Normal;
        let mut statements = 0usize;
        let mut current_has_content = false;
        let mut chars = sql.chars().peekable();

        while let Some(c) = chars.next() {
            match state {
                State::Normal => match c {
                    '\'' => {
                        state = State::Single;
                        current_has_content = true;
                    }
                    '"' => {
                        state = State::Double;
                        current_has_content = true;
                    }
                    '-' if chars.peek() == Some(&'-') => {
                        chars.next();
                        state = State::Line;
                    }
                    '/' if chars.peek() == Some(&'*') => {
                        chars.next();
                        state = State::Block;
                    }
                    ';' => {
                        if current_has_content {
                            statements += 1;
                            if statements > 1 {
                                return true;
                            }
                        }
                        current_has_content = false;
                    }
                    c if c.is_whitespace() => {}
                    _ => current_has_content = true,
                },
                State::Single => {
                    if c == '\'' {
                        if chars.peek() == Some(&'\'') {
                            chars.next();
                        } else {
                            state = State::Normal;
                        }
                    }
                }
                State::Double => {
                    if c == '"' {
                        if chars.peek() == Some(&'"') {
                            chars.next();
                        } else {
                            state = State::Normal;
                        }
                    }
                }
                State::Line => {
                    if c == '\n' {
                        state = State::Normal;
                    }
                }
                State::Block => {
                    if c == '*' && chars.peek() == Some(&'/') {
                        chars.next();
                        state = State::Normal;
                    }
                }
            }
        }

        if current_has_content {
            statements += 1;
        }
        statements > 1
    }
}

pub fn catalogs_cmd() -> Command {
    Command::new("catalogs")
        .about(format!(
            "Interact with the catalogs in your Tower account (includes {})",
            beta::STORAGE.short_about("Storage")
        ))
        .after_help(beta::STORAGE.notice())
        .arg_required_else_help(true)
        .subcommand(
            Command::new("list")
                .arg(
                    Arg::new("environment")
                        .short('e')
                        .long("environment")
                        .default_value("default")
                        .value_parser(value_parser!(String))
                        .help("List catalogs in this environment")
                        .action(ArgAction::Set),
                )
                .arg(
                    Arg::new("all")
                        .short('a')
                        .long("all")
                        .help("List catalogs across all environments")
                        .action(ArgAction::SetTrue),
                )
                .arg(
                    Arg::new("type")
                        .long("type")
                        .value_parser(value_parser!(String))
                        .help("Filter catalogs by type, e.g. tower-catalog")
                        .action(ArgAction::Set),
                )
                .arg(
                    Arg::new("storage")
                        .long("storage")
                        .help(beta::STORAGE.short_about("List Tower-managed storage catalogs"))
                        .conflicts_with("type")
                        .action(ArgAction::SetTrue),
                )
                .about("List all of your catalogs"),
        )
        .subcommand(
            Command::new("show")
                .arg(
                    Arg::new("catalog_name")
                        .value_parser(value_parser!(String))
                        .index(1)
                        .required(true)
                        .help("Name of the catalog"),
                )
                .arg(
                    Arg::new("environment")
                        .short('e')
                        .long("environment")
                        .default_value("default")
                        .value_parser(value_parser!(String))
                        .help("Environment the catalog belongs to")
                        .action(ArgAction::Set),
                )
                .arg(
                    Arg::new("full")
                        .long("full")
                        .help("List each table's columns and their types")
                        .action(ArgAction::SetTrue),
                )
                .about("Show the details of a catalog, including its properties and tables"),
        )
        .subcommand(
            Command::new("credentials")
                .arg(
                    Arg::new("catalog_name")
                        .value_parser(value_parser!(String))
                        .index(1)
                        .required(true)
                        .help("Name of the catalog"),
                )
                .arg(
                    Arg::new("environment")
                        .short('e')
                        .long("environment")
                        .default_value("default")
                        .value_parser(value_parser!(String))
                        .help("Environment the catalog belongs to")
                        .action(ArgAction::Set),
                )
                .arg(
                    Arg::new("mode")
                        .long("mode")
                        .default_value("read")
                        .value_parser(["read", "read-write"])
                        .help("Credential access mode")
                        .action(ArgAction::Set),
                )
                .arg(
                    Arg::new("format")
                        .long("format")
                        .default_value("all")
                        .value_parser(["all", "pyiceberg", "spark", "duckdb", "dbt"])
                        .help("Snippet format to print")
                        .action(ArgAction::Set),
                )
                .arg(
                    Arg::new("show_token")
                        .long("show-token")
                        .help("Print the vended OAuth token in normal output")
                        .action(ArgAction::SetTrue),
                )
                .about(
                    beta::STORAGE
                        .short_about("Vend short-lived catalog credentials for external tools"),
                ),
        )
        .subcommand(
            Command::new("query")
                .arg(
                    Arg::new("catalog_name")
                        .value_parser(value_parser!(String))
                        .index(1)
                        .required(true)
                        .help("Name of the catalog to query"),
                )
                .arg(
                    Arg::new("sql")
                        .short('s')
                        .long("sql")
                        .value_parser(value_parser!(String))
                        .help("SQL statement to execute; read from stdin when omitted")
                        .action(ArgAction::Set),
                )
                .arg(
                    Arg::new("environment")
                        .short('e')
                        .long("environment")
                        .default_value("default")
                        .value_parser(value_parser!(String))
                        .help("Environment the catalog belongs to")
                        .action(ArgAction::Set),
                )
                .arg(
                    Arg::new("write")
                        .short('w')
                        .long("write")
                        .help("Allow write statements by vending read-write credentials; queries are read-only by default")
                        .action(ArgAction::SetTrue),
                )
                .about(beta::STORAGE.short_about("Run a SQL query against a catalog using DuckDB"))
                .after_help(
                    "Reference tables as <catalog>.<namespace>.<table>, e.g.:\n  tower catalogs query default --sql 'SELECT * FROM \"default\".my_namespace.my_table LIMIT 10'",
                ),
        )
}

pub async fn do_list(out: &output::Out, config: Config, args: &ArgMatches) {
    let all = cmd::get_bool_flag(args, "all");
    let env = cmd::get_string_flag(args, "environment");
    let catalog_type = if cmd::get_bool_flag(args, "storage") {
        Some(STORAGE_CATALOG_TYPE)
    } else {
        args.get_one::<String>("type").map(String::as_str)
    };

    if is_storage_catalog_type(catalog_type) {
        beta::notify_once(out, &beta::STORAGE);
    }

    let catalogs = out
        .with_spinner(
            "Listing catalogs",
            api::list_catalogs(&config, &env, all, catalog_type),
        )
        .await;

    let headers = vec!["Name", "Type", "Environment"]
        .into_iter()
        .map(str::to_string)
        .collect();
    let data = catalogs
        .iter()
        .map(|catalog| {
            vec![
                catalog.name.clone(),
                catalog.r#type.clone(),
                catalog.environment.clone(),
            ]
        })
        .collect();
    out.table(headers, data, Some(&catalogs));
}

pub async fn do_credentials(out: &output::Out, config: Config, args: &ArgMatches) {
    beta::notify_once(out, &beta::STORAGE);

    let name = args
        .get_one::<String>("catalog_name")
        .expect("catalog_name is required");
    let env = cmd::get_string_flag(args, "environment");
    let mode = args
        .get_one::<String>("mode")
        .map(String::as_str)
        .unwrap_or("read");
    let format = args
        .get_one::<String>("format")
        .map(String::as_str)
        .unwrap_or("all");
    let show_token = cmd::get_bool_flag(args, "show_token");

    let response = out
        .with_spinner(
            "Vending catalog credentials",
            api::vend_catalog_credentials(&config, name, &env, parse_mode(mode)),
        )
        .await;

    let human = credentials_text(
        name,
        &env,
        mode,
        config.tower_url.as_str(),
        &response.credentials,
        format,
        show_token,
    );
    out.text(&human, &response);
}

pub async fn do_show(out: &output::Out, config: Config, args: &ArgMatches) {
    let name = args
        .get_one::<String>("catalog_name")
        .expect("catalog_name is required");
    let env = cmd::get_string_flag(args, "environment");
    let full = cmd::get_bool_flag(args, "full");

    let response = match api::describe_catalog(&config, name, &env).await {
        Ok(response) => response,
        Err(err) => out.tower_error_and_die(err, "Fetching catalog details failed"),
    };

    let is_storage = is_storage_catalog_type(Some(&response.catalog.r#type));
    if is_storage {
        beta::notify_once(out, &beta::STORAGE);
    }

    let tables = if is_storage {
        Some(fetch_catalog_tables(out, &config, name, &env, full).await)
    } else {
        None
    };

    let mut human = catalog_details_text(&response);
    human.push('\n');
    human.push_str(&header_line("Tables"));
    match &tables {
        None => {
            human.push_str(&format!(
                "  Table listing is not supported for {} catalogs.\n",
                response.catalog.r#type
            ));
        }
        Some(Ok(result)) if result.rows.is_empty() => {
            human.push_str("  No tables found.\n");
        }
        Some(Ok(result)) if full => {
            for row in &result.rows {
                let namespace = json_value_to_cell(row.first().unwrap_or(&serde_json::Value::Null));
                let table = json_value_to_cell(row.get(1).unwrap_or(&serde_json::Value::Null));
                human.push_str(&header_line(&format!("{}.{}", namespace, table)));

                let names = json_array_to_strings(row.get(2));
                let types = json_array_to_strings(row.get(3));
                if names.is_empty() {
                    human.push_str("  No columns found.\n");
                } else {
                    let headers = vec!["Column".to_string(), "Type".to_string()];
                    let data = names
                        .iter()
                        .enumerate()
                        .map(|(i, n)| vec![n.clone(), types.get(i).cloned().unwrap_or_default()])
                        .collect();
                    human.push_str(&output::table_text(headers, data));
                }
                human.push('\n');
            }
        }
        Some(Ok(result)) => {
            let headers = vec!["Namespace".to_string(), "Table".to_string()];
            let data = result
                .rows
                .iter()
                .map(|row| row.iter().map(json_value_to_cell).collect())
                .collect();
            human.push_str(&output::table_text(headers, data));
        }
        Some(Err(err)) => {
            human.push_str(&format!("  Unable to list tables: {}\n", err));
        }
    }

    // `tables` is an array (possibly empty) on success and null otherwise;
    // `tables_error` distinguishes a failed listing (message) from a catalog
    // type that doesn't support listing (null).
    let (json_tables, tables_error) = match tables {
        None => (serde_json::Value::Null, None),
        Some(Err(err)) => (serde_json::Value::Null, Some(err)),
        Some(Ok(result)) => (
            serde_json::Value::Array(
                result
                    .rows
                    .iter()
                    .map(|row| {
                        let mut entry = serde_json::json!({
                            "namespace": row.first().cloned().unwrap_or(serde_json::Value::Null),
                            "table": row.get(1).cloned().unwrap_or(serde_json::Value::Null),
                        });
                        if full {
                            let names = json_array_to_strings(row.get(2));
                            let types = json_array_to_strings(row.get(3));
                            let columns = names
                                .iter()
                                .enumerate()
                                .map(|(i, n)| {
                                    serde_json::json!({
                                        "name": n,
                                        "type": types.get(i).cloned().unwrap_or_default(),
                                    })
                                })
                                .collect();
                            entry["columns"] = serde_json::Value::Array(columns);
                        }
                        entry
                    })
                    .collect(),
            ),
            None,
        ),
    };
    let json_data = serde_json::json!({
        "catalog": response.catalog,
        "tables": json_tables,
        "tables_error": tables_error,
    });
    out.text(&human, &json_data);
}

/// Lists the tables in a catalog by attaching it in DuckDB. Unlike the query
/// path this never exits: `show` should still render catalog details when the
/// tables can't be fetched.
async fn fetch_catalog_tables(
    out: &output::Out,
    config: &Config,
    name: &str,
    env: &str,
    full: bool,
) -> Result<QueryResult, String> {
    let mut spinner = out.spinner("Listing tables...");

    let response = match api::vend_catalog_credentials(
        config,
        name,
        env,
        vend_catalog_credentials_body::Mode::Read,
    )
    .await
    {
        Ok(response) => response,
        Err(err) => {
            spinner.failure(out);
            return Err(err.to_string());
        }
    };

    let token = response.credentials.oauth_token.clone();

    // `--full` needs every table's column schema. Going through DuckDB means a
    // `DESCRIBE` per table, each of which fully opens the Iceberg table (reading
    // manifests from object storage) — slow, and unbounded for tables with heavy
    // metadata. The Iceberg REST catalog's `loadTable` returns the schema
    // straight from table metadata with no manifest I/O, so `--full` talks to
    // the catalog directly. The plain listing stays on DuckDB.
    let result = if full {
        fetch_catalog_columns_via_rest(&response.credentials).await
    } else {
        let setup = attach_statements(
            name,
            &response.credentials,
            vend_catalog_credentials_body::Mode::Read,
        );
        let db_name = name.to_string();
        tokio::task::spawn_blocking(move || {
            run_duckdb_query(
                &setup,
                "SELECT \"schema\", name FROM (SHOW ALL TABLES) WHERE database = ? ORDER BY \"schema\", name",
                duckdb::params![db_name],
                None,
            )
        })
        .await
        .map_err(|err| err.to_string())
        .and_then(|inner| inner.map_err(|err| err.to_string()))
    };

    match result {
        Ok(query_result) => {
            spinner.success(out);
            Ok(query_result)
        }
        Err(err) => {
            spinner.failure(out);
            Err(redact_token(&err, &token))
        }
    }
}

/// DuckDB errors can echo the failing statement, and the setup batch contains
/// the vended OAuth token — scrub it before the message reaches any output.
fn redact_token(message: &str, token: &str) -> String {
    if token.is_empty() {
        return message.to_string();
    }
    message.replace(token, "[REDACTED]")
}

pub async fn do_query(out: &output::Out, config: Config, args: &ArgMatches) {
    beta::notify_once(out, &beta::STORAGE);

    let name = args
        .get_one::<String>("catalog_name")
        .expect("catalog_name is required");
    let env = cmd::get_string_flag(args, "environment");

    let sql = match args.get_one::<String>("sql") {
        Some(sql) => sql.clone(),
        None => read_sql_from_stdin(out),
    };
    let sql = sql.trim().to_string();
    if sql.is_empty() {
        out.die("No SQL statement provided. Pass one with --sql or pipe it via stdin.");
    }

    let response = match api::describe_catalog(&config, name, &env).await {
        Ok(response) => response,
        Err(err) => out.tower_error_and_die(err, "Fetching catalog details failed"),
    };
    if !is_storage_catalog_type(Some(&response.catalog.r#type)) {
        out.die(&format!(
            "Querying is only supported for {} catalogs; '{}' has type '{}'.",
            STORAGE_CATALOG_TYPE, name, response.catalog.r#type
        ));
    }

    let write = cmd::get_bool_flag(args, "write");
    let query_result = execute_catalog_query(out, &config, name, &env, sql, write).await;
    output_query_result(out, &query_result);
}

/// Vends credentials for the catalog, attaches it in an in-memory DuckDB, and
/// runs `sql` against it. Read-only unless `write` is set, in which case
/// read-write credentials are vended and the attach allows writes. Dies with a
/// user-facing error on failure.
async fn execute_catalog_query(
    out: &output::Out,
    config: &Config,
    name: &str,
    env: &str,
    sql: String,
    write: bool,
) -> QueryResult {
    let mode = if write {
        vend_catalog_credentials_body::Mode::ReadWrite
    } else {
        vend_catalog_credentials_body::Mode::Read
    };

    let mut spinner = out.spinner("Running query...");

    let response = match api::vend_catalog_credentials(config, name, env, mode).await {
        Ok(response) => response,
        Err(err) => {
            spinner.failure(out);
            out.tower_error_and_die(err, "Running query failed");
        }
    };

    let token = response.credentials.oauth_token.clone();
    let setup = attach_statements(name, &response.credentials, mode);
    let result = tokio::task::spawn_blocking(move || run_duckdb_query(&setup, &sql, [], None)).await;

    match result {
        Ok(Ok(query_result)) => {
            spinner.success(out);
            query_result
        }
        Ok(Err(err)) => {
            spinner.failure(out);
            out.die(&format!(
                "Query failed: {}",
                redact_token(&err.to_string(), &token)
            ));
        }
        Err(err) => {
            spinner.failure(out);
            out.die(&format!(
                "Query execution panicked: {}",
                redact_token(&err.to_string(), &token)
            ));
        }
    }
}

fn read_sql_from_stdin(out: &output::Out) -> String {
    let mut stdin = std::io::stdin();
    if stdin.is_terminal() {
        out.die("No SQL statement provided. Pass one with --sql or pipe it via stdin.");
    }
    let mut sql = String::new();
    if let Err(err) = stdin.read_to_string(&mut sql) {
        out.die(&format!("Failed reading SQL from stdin: {}", err));
    }
    sql
}

#[derive(Debug)]
struct QueryResult {
    columns: Vec<String>,
    rows: Vec<Vec<serde_json::Value>>,
    /// Rows were dropped to honour a caller-supplied row cap. Populated by
    /// `run_duckdb_query`; the reader lands with the agent query path, so it is
    /// exercised only by the sandbox tests today.
    #[allow(dead_code)]
    truncated: bool,
}

/// Statements that install the Iceberg support and attach the catalog under
/// its Tower name — mirrors `templates/duckdb.sql.tmpl`. The attach is
/// READ_ONLY unless read-write credentials were vended. No `USE`: DuckDB's
/// `USE` needs a `main` schema, which Iceberg catalogs don't have, so queries
/// must qualify tables as <catalog>.<namespace>.<table>.
fn attach_statements(
    name: &str,
    credentials: &CatalogCredentials,
    mode: vend_catalog_credentials_body::Mode,
) -> Vec<String> {
    let read_only = match mode {
        vend_catalog_credentials_body::Mode::Read => "READ_ONLY, ",
        vend_catalog_credentials_body::Mode::ReadWrite => "",
    };
    vec![
        "INSTALL httpfs".to_string(),
        "LOAD httpfs".to_string(),
        "INSTALL iceberg".to_string(),
        "LOAD iceberg".to_string(),
        "SET s3_region='eu-central-1'".to_string(),
        format!(
            "CREATE OR REPLACE SECRET tower_cat (TYPE iceberg, TOKEN {})",
            SqlLiteral(&credentials.oauth_token),
        ),
        format!(
            "ATTACH {warehouse} AS {name} (TYPE iceberg, {read_only}SECRET tower_cat, ENDPOINT {uri}, DEFAULT_REGION 'eu-central-1')",
            warehouse = SqlLiteral(&credentials.warehouse),
            name = SqlIdent(name),
            uri = SqlLiteral(&credentials.catalog_uri),
        ),
    ]
}

/// Runs `setup` statements one at a time, then `query` as a prepared statement
/// with `params` bound. Values that fit a bind position should go through
/// `params` rather than into the query text. When `max_rows` is set, rows past
/// it are dropped and the result is flagged truncated, so an untrusted caller
/// cannot pull an unbounded table into memory.
fn run_duckdb_query<P: duckdb::Params>(
    setup: &[String],
    query: &str,
    params: P,
    max_rows: Option<usize>,
) -> Result<QueryResult, duckdb::Error> {
    let conn = duckdb::Connection::open_in_memory()?;
    // Setup statements embed the vended OAuth token, so time them without logging
    // their text.
    let setup_start = Instant::now();
    for statement in setup {
        conn.execute_batch(statement)?;
    }
    debug!(
        "duckdb: setup ({} statements) took {:?}",
        setup.len(),
        setup_start.elapsed()
    );

    let query_start = Instant::now();
    let mut stmt = conn.prepare(query)?;
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
                record.push(duckdb_value_to_json(value));
            }
            rows.push(record);
        }
    }

    // A query with no result rows never populates columns above.
    if columns.is_empty() {
        columns = stmt.column_names();
    }

    debug!(
        "duckdb: query took {:?} ({} rows): {}",
        query_start.elapsed(),
        rows.len(),
        query
    );

    Ok(QueryResult {
        columns,
        rows,
        truncated,
    })
}

/// How many `loadTable` requests `--full` runs against the Iceberg REST catalog
/// at once. Each is a single metadata fetch; kept modest because Polaris rate
/// limits (HTTP 429) aggressive fan-out. Throttled requests are retried, so this
/// only tunes throughput, not correctness.
const CATALOG_LOADTABLE_CONCURRENCY: usize = 4;

/// How many times to retry a throttled or transient catalog request before
/// giving up on it.
const CATALOG_HTTP_MAX_RETRIES: usize = 4;

/// Fetches every table's column schema directly from the Iceberg REST catalog.
/// Discovers namespaces and tables through the catalog's list endpoints, then
/// `loadTable`s each table concurrently and reads its current schema — no DuckDB
/// attach and no manifest I/O, which is what makes `DESCRIBE` slow. Returns rows
/// shaped like the plain listing (`[namespace, table, [column names],
/// [column types]]`) so `do_show` renders both modes the same way. A table whose
/// `loadTable` fails is reported with no columns rather than failing the listing.
async fn fetch_catalog_columns_via_rest(
    credentials: &CatalogCredentials,
) -> Result<QueryResult, String> {
    let client = reqwest::Client::new();
    let base = credentials.catalog_uri.trim_end_matches('/');
    // The vended warehouse is the Polaris REST prefix (see `CatalogCredentials`).
    let prefix = credentials.warehouse.as_str();
    let token = credentials.oauth_token.as_str();

    let list_start = Instant::now();
    let namespaces = list_all_namespaces(&client, base, prefix, token).await?;
    let mut tables: Vec<(Vec<String>, String)> = Vec::new();
    for namespace in &namespaces {
        for table in list_tables(&client, base, prefix, token, namespace).await? {
            tables.push((namespace.clone(), table));
        }
    }
    debug!(
        "catalog rest: discovered {} tables across {} namespaces in {:?}",
        tables.len(),
        namespaces.len(),
        list_start.elapsed()
    );

    let load_start = Instant::now();
    let client = &client;
    let mut rows: Vec<Vec<serde_json::Value>> = futures_util::stream::iter(tables)
        .map(|(namespace, table)| async move {
            let display_ns = namespace.join(".");
            let started = Instant::now();
            let (names, types) =
                match load_table_columns(client, base, prefix, token, &namespace, &table).await {
                    Ok(columns) => {
                        debug!(
                            "catalog rest: loadTable {}.{} took {:?} ({} columns)",
                            display_ns,
                            table,
                            started.elapsed(),
                            columns.0.len()
                        );
                        columns
                    }
                    Err(err) => {
                        debug!(
                            "catalog rest: loadTable {}.{} failed after {:?}: {}",
                            display_ns,
                            table,
                            started.elapsed(),
                            err
                        );
                        (Vec::new(), Vec::new())
                    }
                };
            vec![
                serde_json::Value::String(display_ns),
                serde_json::Value::String(table),
                serde_json::Value::Array(names),
                serde_json::Value::Array(types),
            ]
        })
        .buffer_unordered(CATALOG_LOADTABLE_CONCURRENCY)
        .collect()
        .await;
    debug!(
        "catalog rest: loaded {} table schemas in {:?}",
        rows.len(),
        load_start.elapsed()
    );

    // `buffer_unordered` yields as each request finishes, so restore the
    // namespace/table ordering the plain listing produces.
    rows.sort_by(|a, b| {
        let key = |row: &[serde_json::Value]| {
            (
                row.first().and_then(|v| v.as_str()).unwrap_or("").to_owned(),
                row.get(1).and_then(|v| v.as_str()).unwrap_or("").to_owned(),
            )
        };
        key(a).cmp(&key(b))
    });

    Ok(QueryResult {
        columns: vec![
            "schema".to_string(),
            "name".to_string(),
            "column_names".to_string(),
            "column_types".to_string(),
        ],
        rows,
        truncated: false,
    })
}

/// Appends `segments` to the catalog base URL, percent-encoding each segment
/// (so a multi-level namespace joined by the Iceberg `\u{1f}` separator is
/// encoded as one path component). Preserves any path already on the base.
fn build_catalog_url(base: &str, segments: &[&str]) -> Result<reqwest::Url, String> {
    let mut url = reqwest::Url::parse(base).map_err(|err| err.to_string())?;
    {
        let mut path = url
            .path_segments_mut()
            .map_err(|_| format!("catalog uri is not a valid base: {}", base))?;
        for segment in segments {
            path.push(segment);
        }
    }
    Ok(url)
}

/// Issues an authenticated GET and parses the JSON body, retrying on throttling
/// (HTTP 429) and transient 5xx responses with backoff — Polaris rate limits
/// concurrent `loadTable`s, and an un-retried 429 would drop that table's
/// schema. The bearer token rides in the header, never the URL, so the URL is
/// safe to include in errors.
async fn catalog_get_json(
    client: &reqwest::Client,
    url: reqwest::Url,
    token: &str,
) -> Result<serde_json::Value, String> {
    let url_display = url.as_str().to_owned();
    let mut attempt = 0;
    loop {
        let response = client
            .get(url.clone())
            .bearer_auth(token)
            .send()
            .await
            .map_err(|err| err.to_string())?;
        let status = response.status();
        if status.is_success() {
            return response
                .json::<serde_json::Value>()
                .await
                .map_err(|err| format!("GET {} -> {}", url_display, err));
        }

        let retryable =
            status == reqwest::StatusCode::TOO_MANY_REQUESTS || status.is_server_error();
        if retryable && attempt < CATALOG_HTTP_MAX_RETRIES {
            // Honour Retry-After when present; otherwise exponential backoff.
            let backoff = retry_after(&response)
                .unwrap_or_else(|| Duration::from_millis(200 * (1 << attempt)));
            debug!(
                "catalog rest: {} returned HTTP {} (attempt {}), retrying in {:?}",
                url_display,
                status,
                attempt + 1,
                backoff
            );
            attempt += 1;
            tokio::time::sleep(backoff).await;
            continue;
        }

        let body: String = response
            .text()
            .await
            .unwrap_or_default()
            .chars()
            .take(200)
            .collect();
        return Err(format!("GET {} -> HTTP {}: {}", url_display, status, body));
    }
}

/// Parses a `Retry-After` header expressed in whole seconds, if present.
fn retry_after(response: &reqwest::Response) -> Option<Duration> {
    response
        .headers()
        .get(reqwest::header::RETRY_AFTER)?
        .to_str()
        .ok()?
        .trim()
        .parse::<u64>()
        .ok()
        .map(Duration::from_secs)
}

/// Walks the catalog's namespace tree breadth-first so nested namespaces are
/// included, not just the top level. Deduped in case a catalog also returns
/// descendants from the root listing.
async fn list_all_namespaces(
    client: &reqwest::Client,
    base: &str,
    prefix: &str,
    token: &str,
) -> Result<Vec<Vec<String>>, String> {
    let mut all: Vec<Vec<String>> = Vec::new();
    let mut frontier: Vec<Vec<String>> = vec![Vec::new()];
    while let Some(parent) = frontier.pop() {
        for child in list_namespaces(client, base, prefix, token, &parent).await? {
            if !all.contains(&child) {
                all.push(child.clone());
                frontier.push(child);
            }
        }
    }
    Ok(all)
}

/// Lists the immediate child namespaces of `parent` (the root when empty).
async fn list_namespaces(
    client: &reqwest::Client,
    base: &str,
    prefix: &str,
    token: &str,
    parent: &[String],
) -> Result<Vec<Vec<String>>, String> {
    let mut url = build_catalog_url(base, &["v1", prefix, "namespaces"])?;
    if !parent.is_empty() {
        url.query_pairs_mut()
            .append_pair("parent", &parent.join("\u{1f}"));
    }
    let json = catalog_get_json(client, url, token).await?;
    Ok(json
        .get("namespaces")
        .and_then(|v| v.as_array())
        .map(|list| {
            list.iter()
                .filter_map(|ns| ns.as_array())
                .map(|levels| {
                    levels
                        .iter()
                        .filter_map(|level| level.as_str().map(str::to_owned))
                        .collect()
                })
                .collect()
        })
        .unwrap_or_default())
}

/// Lists the table names in a single namespace.
async fn list_tables(
    client: &reqwest::Client,
    base: &str,
    prefix: &str,
    token: &str,
    namespace: &[String],
) -> Result<Vec<String>, String> {
    let ns = namespace.join("\u{1f}");
    let url = build_catalog_url(base, &["v1", prefix, "namespaces", &ns, "tables"])?;
    let json = catalog_get_json(client, url, token).await?;
    Ok(json
        .get("identifiers")
        .and_then(|v| v.as_array())
        .map(|list| {
            list.iter()
                .filter_map(|ident| ident.get("name").and_then(|n| n.as_str()))
                .map(str::to_owned)
                .collect()
        })
        .unwrap_or_default())
}

/// `loadTable`s one table and extracts its current schema as parallel
/// `(column names, column types)` vectors. Falls back to the first schema, and
/// to legacy single-`schema` metadata, when `current-schema-id` isn't matched.
async fn load_table_columns(
    client: &reqwest::Client,
    base: &str,
    prefix: &str,
    token: &str,
    namespace: &[String],
    table: &str,
) -> Result<(Vec<serde_json::Value>, Vec<serde_json::Value>), String> {
    let ns = namespace.join("\u{1f}");
    let url = build_catalog_url(base, &["v1", prefix, "namespaces", &ns, "tables", table])?;
    let json = catalog_get_json(client, url, token).await?;

    let metadata = json
        .get("metadata")
        .ok_or_else(|| "loadTable response missing `metadata`".to_string())?;
    let current = metadata.get("current-schema-id").and_then(|v| v.as_i64());
    let schema = match (metadata.get("schemas").and_then(|v| v.as_array()), current) {
        (Some(schemas), Some(id)) => schemas
            .iter()
            .find(|s| s.get("schema-id").and_then(|v| v.as_i64()) == Some(id))
            .or_else(|| schemas.first()),
        (Some(schemas), None) => schemas.first(),
        (None, _) => metadata.get("schema"),
    };

    let fields = schema
        .and_then(|s| s.get("fields"))
        .and_then(|v| v.as_array());
    let mut names = Vec::new();
    let mut types = Vec::new();
    if let Some(fields) = fields {
        for field in fields {
            let name = field
                .get("name")
                .and_then(|v| v.as_str())
                .unwrap_or_default()
                .to_owned();
            let ty = iceberg_type_to_display(field.get("type").unwrap_or(&serde_json::Value::Null));
            names.push(serde_json::Value::String(name));
            types.push(serde_json::Value::String(ty));
        }
    }
    Ok((names, types))
}

/// Renders an Iceberg field type (from `loadTable` metadata) as a display
/// string, mapping primitives to the DuckDB-style names the plain listing shows
/// and summarising nested types.
fn iceberg_type_to_display(ty: &serde_json::Value) -> String {
    match ty {
        serde_json::Value::String(name) => iceberg_primitive_to_display(name),
        serde_json::Value::Object(obj) => match obj.get("type").and_then(|v| v.as_str()) {
            Some("struct") => "STRUCT".to_string(),
            Some("list") => {
                let element = obj
                    .get("element")
                    .map(iceberg_type_to_display)
                    .unwrap_or_default();
                format!("LIST({})", element)
            }
            Some("map") => {
                let key = obj.get("key").map(iceberg_type_to_display).unwrap_or_default();
                let value = obj
                    .get("value")
                    .map(iceberg_type_to_display)
                    .unwrap_or_default();
                format!("MAP({}, {})", key, value)
            }
            Some(other) => other.to_uppercase(),
            None => "UNKNOWN".to_string(),
        },
        _ => "UNKNOWN".to_string(),
    }
}

/// Maps an Iceberg primitive type name to its DuckDB-style display name so the
/// `--full` output matches the types the plain listing used to show.
fn iceberg_primitive_to_display(name: &str) -> String {
    match name {
        "boolean" => "BOOLEAN".to_string(),
        "int" => "INTEGER".to_string(),
        "long" => "BIGINT".to_string(),
        "float" => "FLOAT".to_string(),
        "double" => "DOUBLE".to_string(),
        "date" => "DATE".to_string(),
        "time" => "TIME".to_string(),
        "timestamp" => "TIMESTAMP".to_string(),
        "timestamp_ns" => "TIMESTAMP_NS".to_string(),
        "timestamptz" | "timestamptz_ns" => "TIMESTAMP WITH TIME ZONE".to_string(),
        "string" => "VARCHAR".to_string(),
        "uuid" => "UUID".to_string(),
        "binary" => "BLOB".to_string(),
        // decimal(P, S) is already descriptive; fixed[L] has no tidy SQL name.
        other if other.starts_with("decimal") => other.to_uppercase(),
        other if other.starts_with("fixed") => "BLOB".to_string(),
        other => other.to_uppercase(),
    }
}

fn duckdb_value_to_json(value: duckdb::types::Value) -> serde_json::Value {
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
            serde_json::Value::Array(items.into_iter().map(duckdb_value_to_json).collect())
        }
        Value::Struct(fields) => serde_json::Value::Object(
            fields
                .iter()
                .map(|(name, value)| (name.clone(), duckdb_value_to_json(value.clone())))
                .collect(),
        ),
        Value::Map(entries) => serde_json::Value::Object(
            entries
                .iter()
                .map(|(key, value)| {
                    (
                        json_value_to_cell(&duckdb_value_to_json(key.clone())),
                        duckdb_value_to_json(value.clone()),
                    )
                })
                .collect(),
        ),
        Value::Union(inner) => duckdb_value_to_json(*inner),
        other => json!(format!("{:?}", other)),
    }
}

fn output_query_result(out: &output::Out, result: &QueryResult) {
    let json_rows: Vec<serde_json::Map<String, serde_json::Value>> = result
        .rows
        .iter()
        .map(|row| {
            result
                .columns
                .iter()
                .cloned()
                .zip(row.iter().cloned())
                .collect()
        })
        .collect();

    let data = result
        .rows
        .iter()
        .map(|row| row.iter().map(json_value_to_cell).collect())
        .collect();

    out.table(result.columns.clone(), data, Some(&json_rows));
    out.note(&format!("\n{} row(s)\n", result.rows.len()));
}

fn json_value_to_cell(value: &serde_json::Value) -> String {
    match value {
        serde_json::Value::Null => String::new(),
        serde_json::Value::String(s) => s.clone(),
        other => other.to_string(),
    }
}

/// Flattens a DuckDB list column (surfaced as a JSON array) into display strings.
/// Anything that isn't an array — a null or missing cell — becomes an empty list.
fn json_array_to_strings(value: Option<&serde_json::Value>) -> Vec<String> {
    match value {
        Some(serde_json::Value::Array(items)) => items.iter().map(json_value_to_cell).collect(),
        _ => Vec::new(),
    }
}

fn is_storage_catalog_type(catalog_type: Option<&str>) -> bool {
    catalog_type == Some(STORAGE_CATALOG_TYPE)
}

fn parse_mode(mode: &str) -> vend_catalog_credentials_body::Mode {
    match mode {
        "read-write" => vend_catalog_credentials_body::Mode::ReadWrite,
        _ => vend_catalog_credentials_body::Mode::Read,
    }
}

fn shell_quote(value: &str) -> String {
    format!("'{}'", value.replace('\'', "'\"'\"'"))
}

fn quote(value: &str) -> String {
    serde_json::to_string(value).expect("serializing a string should not fail")
}

/// A value embedded in generated SQL as a single-quoted string literal.
/// Escaping lives in the `Display` impl, so a value can only appear in the
/// generated text in its escaped form.
struct SqlLiteral<'a>(&'a str);

impl std::fmt::Display for SqlLiteral<'_> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "'{}'", self.0.replace('\'', "''"))
    }
}

/// A value embedded in generated SQL as a double-quoted identifier.
struct SqlIdent<'a>(&'a str);

impl std::fmt::Display for SqlIdent<'_> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "\"{}\"", self.0.replace('"', "\"\""))
    }
}

fn token_export_command(name: &str, environment: &str, mode: &str, tower_url: &str) -> String {
    format!(
        "export TOWER_CATALOG_TOKEN=\"$(tower --tower-url {tower_url} --json catalogs credentials {name} --environment {environment} --mode {mode} | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"credentials\"][\"oauth_token\"])')\"\n",
        tower_url = shell_quote(tower_url),
        name = shell_quote(name),
        environment = shell_quote(environment),
        mode = shell_quote(mode),
    )
}

fn detail_line(label: &str, value: &str) -> String {
    format!("{} {}\n", format!("{}:", label).bold().green(), value)
}

fn header_line(text: &str) -> String {
    format!("{}\n", text.bold().green())
}

fn catalog_details_text(response: &DescribeCatalogResponse) -> String {
    let catalog = &response.catalog;
    let mut out = String::new();

    out.push_str(&detail_line("Catalog", &catalog.name));
    out.push_str(&detail_line("Type", &catalog.r#type));
    out.push_str(&detail_line("Environment", &catalog.environment));

    if !catalog.properties.is_empty() {
        out.push('\n');
        out.push_str(&header_line("Properties"));

        let headers = vec!["Name", "Runtime Var", "Preview"]
            .into_iter()
            .map(str::to_string)
            .collect();
        let data = catalog
            .properties
            .iter()
            .map(|prop| {
                vec![
                    prop.name.clone(),
                    prop.environment_variable.clone().unwrap_or_default(),
                    prop.preview.dimmed().to_string(),
                ]
            })
            .collect();
        out.push_str(&output::table_text(headers, data));
    }

    out
}

fn credentials_text(
    name: &str,
    environment: &str,
    mode: &str,
    tower_url: &str,
    credentials: &CatalogCredentials,
    format: &str,
    show_token: bool,
) -> String {
    let mut out = String::new();

    out.push_str(&detail_line("Catalog", name));
    out.push_str(&detail_line("Mode", &credentials.mode));
    out.push_str(&detail_line("Expires", &credentials.expires_at));
    if show_token {
        out.push_str(&detail_line("Token", &credentials.oauth_token));
    } else {
        out.push_str(&detail_line(
            "Token",
            "not printed; snippets read $TOWER_CATALOG_TOKEN",
        ));
    }
    out.push_str(&output::paragraph(
        "These credentials are short-lived and intended for ad-hoc development use.",
    ));
    out.push('\n');

    if !show_token {
        out.push('\n');
        out.push_str(&header_line("Shell setup"));
        out.push_str(token_export_command(name, environment, mode, tower_url).as_str());
    }

    for snippet in snippets(name, credentials, format, show_token) {
        out.push('\n');
        out.push_str(&header_line(snippet.title));
        out.push_str(snippet.body.as_str());
        if !snippet.body.ends_with('\n') {
            out.push('\n');
        }
        out.push('\n');
    }

    out
}

const PYICEBERG_TMPL: &str = include_str!("templates/pyiceberg.py.tmpl");
const SPARK_TMPL: &str = include_str!("templates/spark.py.tmpl");
const DUCKDB_TMPL: &str = include_str!("templates/duckdb.sql.tmpl");
const DBT_TMPL: &str = include_str!("templates/dbt.yml.tmpl");

/// Substitute `__TOWER_*__` markers in a connection-snippet template. Values must
/// already be escaped for the target format — the templates under `src/templates/`
/// are inert text and the per-format escaping stays in `snippets`.
fn render(template: &str, vars: &[(&str, String)]) -> String {
    let mut out = template.to_string();
    for (marker, value) in vars {
        out = out.replace(marker, value);
    }
    out
}

struct Snippet {
    title: &'static str,
    body: String,
}

fn snippets(
    name: &str,
    credentials: &CatalogCredentials,
    format: &str,
    show_token: bool,
) -> Vec<Snippet> {
    let all = format == "all";
    let mut snippets = Vec::new();

    let py_token = if show_token {
        quote(&credentials.oauth_token)
    } else {
        "os.environ[\"TOWER_CATALOG_TOKEN\"]".to_string()
    };
    let sql_token = if show_token {
        SqlLiteral(&credentials.oauth_token).to_string()
    } else {
        "'${TOWER_CATALOG_TOKEN}'".to_string()
    };
    let dbt_token = if show_token {
        quote(&credentials.oauth_token)
    } else {
        "\"{{ env_var('TOWER_CATALOG_TOKEN') }}\"".to_string()
    };
    if all || format == "pyiceberg" {
        snippets.push(Snippet {
            title: "PyIceberg",
            body: render(
                PYICEBERG_TMPL,
                &[
                    ("__TOWER_NAME__", quote(name)),
                    ("__TOWER_URI__", quote(&credentials.catalog_uri)),
                    ("__TOWER_WAREHOUSE__", quote(&credentials.warehouse)),
                    ("__TOWER_TOKEN__", py_token.clone()),
                ],
            ),
        });
    }

    if all || format == "spark" {
        snippets.push(Snippet {
            title: "Spark",
            body: render(
                SPARK_TMPL,
                &[
                    ("__TOWER_NAME__", name.to_string()),
                    ("__TOWER_URI__", quote(&credentials.catalog_uri)),
                    ("__TOWER_WAREHOUSE__", quote(&credentials.warehouse)),
                    ("__TOWER_TOKEN__", py_token.clone()),
                ],
            ),
        });
    }

    if all || format == "duckdb" {
        snippets.push(Snippet {
            title: "DuckDB",
            body: render(
                DUCKDB_TMPL,
                &[
                    ("__TOWER_NAME__", SqlIdent(name).to_string()),
                    (
                        "__TOWER_URI__",
                        SqlLiteral(&credentials.catalog_uri).to_string(),
                    ),
                    (
                        "__TOWER_WAREHOUSE__",
                        SqlLiteral(&credentials.warehouse).to_string(),
                    ),
                    ("__TOWER_TOKEN__", sql_token.clone()),
                ],
            ),
        });
    }

    if all || format == "dbt" {
        snippets.push(Snippet {
            title: "dbt",
            body: render(
                DBT_TMPL,
                &[
                    ("__TOWER_URI__", quote(&credentials.catalog_uri)),
                    ("__TOWER_WAREHOUSE__", quote(&credentials.warehouse)),
                    ("__TOWER_TOKEN__", dbt_token.clone()),
                ],
            ),
        });
    }

    snippets
}

#[cfg(test)]
mod tests {
    use super::sandbox::{
        agent_hardening_statements, contains_multiple_statements, first_sql_keyword,
        is_write_statement,
    };
    use super::{
        attach_statements, catalogs_cmd, duckdb_value_to_json, is_storage_catalog_type, parse_mode,
        run_duckdb_query, snippets, token_export_command,
    };
    use tower_api::models::{vend_catalog_credentials_body, CatalogCredentials};

    #[test]
    fn list_defaults_to_default_environment() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "list"])
            .expect("list should parse with no args");

        let (_, list_args) = matches.subcommand().expect("expected list subcommand");

        assert_eq!(
            list_args.get_one::<String>("environment").unwrap(),
            "default"
        );
        assert_eq!(list_args.get_one::<bool>("all").copied(), Some(false));
    }

    #[test]
    fn list_accepts_environment_flag() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "list", "-e", "production"])
            .expect("list -e should parse");

        let (_, list_args) = matches.subcommand().expect("expected list subcommand");

        assert_eq!(
            list_args.get_one::<String>("environment").unwrap(),
            "production"
        );
    }

    #[test]
    fn list_accepts_all_flag() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "list", "--all"])
            .expect("list --all should parse");

        let (_, list_args) = matches.subcommand().expect("expected list subcommand");

        assert_eq!(list_args.get_one::<bool>("all").copied(), Some(true));
    }

    #[test]
    fn list_accepts_type_filter() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "list", "--type", "tower-catalog"])
            .expect("list --type should parse");

        let (_, list_args) = matches.subcommand().expect("expected list subcommand");

        assert_eq!(
            list_args.get_one::<String>("type").unwrap(),
            "tower-catalog"
        );
    }

    #[test]
    fn list_accepts_storage_alias() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "list", "--storage"])
            .expect("list --storage should parse");

        let (_, list_args) = matches.subcommand().expect("expected list subcommand");

        assert_eq!(list_args.get_one::<bool>("storage").copied(), Some(true));
    }

    #[test]
    fn list_rejects_type_and_storage_together() {
        let result =
            catalogs_cmd().try_get_matches_from(["catalogs", "list", "--storage", "--type", "s3"]);
        assert!(result.is_err());
    }

    #[test]
    fn storage_catalog_type_detection_is_scoped() {
        assert!(is_storage_catalog_type(Some("tower-catalog")));
        assert!(!is_storage_catalog_type(Some("snowflake-open-catalog")));
        assert!(!is_storage_catalog_type(None));
    }

    #[test]
    fn catalog_help_marks_storage_beta_in_short_and_long_help() {
        let short_help = catalogs_cmd().render_help().to_string();
        let long_help = catalogs_cmd().render_long_help().to_string();

        for help in [short_help, long_help] {
            assert!(help.contains("includes Storage [beta]"));
            assert!(help.contains("Tower Storage is in beta."));
        }
    }

    #[test]
    fn storage_specific_command_and_flag_are_marked_beta() {
        let mut command = catalogs_cmd();
        let credentials_help = command
            .find_subcommand_mut("credentials")
            .expect("credentials command should exist")
            .render_help()
            .to_string();
        assert!(credentials_help
            .contains("Vend short-lived catalog credentials for external tools [beta]"));

        let mut command = catalogs_cmd();
        let list_help = command
            .find_subcommand_mut("list")
            .expect("list command should exist")
            .render_help()
            .to_string();
        assert!(list_help.contains("List Tower-managed storage catalogs [beta]"));
    }

    #[test]
    fn show_requires_catalog_name() {
        let result = catalogs_cmd().try_get_matches_from(["catalogs", "show"]);
        assert!(result.is_err());
    }

    #[test]
    fn show_accepts_catalog_name() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "show", "my-catalog"])
            .expect("show with name should parse");

        let (_, show_args) = matches.subcommand().expect("expected show subcommand");

        assert_eq!(
            show_args.get_one::<String>("catalog_name").unwrap(),
            "my-catalog"
        );
        assert_eq!(
            show_args.get_one::<String>("environment").unwrap(),
            "default"
        );
    }

    #[test]
    fn show_accepts_environment_override() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "show", "my-catalog", "-e", "production"])
            .expect("show with -e should parse");

        let (_, show_args) = matches.subcommand().expect("expected show subcommand");

        assert_eq!(
            show_args.get_one::<String>("catalog_name").unwrap(),
            "my-catalog"
        );
        assert_eq!(
            show_args.get_one::<String>("environment").unwrap(),
            "production"
        );
    }

    #[test]
    fn credentials_accepts_catalog_name() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "credentials", "default"])
            .expect("credentials with name should parse");

        let (_, credentials_args) = matches
            .subcommand()
            .expect("expected credentials subcommand");

        assert_eq!(
            credentials_args.get_one::<String>("catalog_name").unwrap(),
            "default"
        );
        assert_eq!(credentials_args.get_one::<String>("mode").unwrap(), "read");
        assert_eq!(credentials_args.get_one::<String>("format").unwrap(), "all");
    }

    #[test]
    fn credentials_accepts_read_write_mode() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "credentials", "default", "--mode", "read-write"])
            .expect("credentials --mode read-write should parse");

        let (_, credentials_args) = matches
            .subcommand()
            .expect("expected credentials subcommand");

        assert_eq!(
            credentials_args.get_one::<String>("mode").unwrap(),
            "read-write"
        );
        assert_eq!(
            parse_mode(credentials_args.get_one::<String>("mode").unwrap()),
            vend_catalog_credentials_body::Mode::ReadWrite
        );
    }

    #[test]
    fn redact_token_scrubs_secret_from_error_text() {
        let msg = "Parser Error near 'CREATE SECRET tower_cat (TYPE iceberg, TOKEN 'sekret-123')'";
        assert_eq!(
            super::redact_token(msg, "sekret-123"),
            "Parser Error near 'CREATE SECRET tower_cat (TYPE iceberg, TOKEN '[REDACTED]')'"
        );
        assert_eq!(super::redact_token(msg, ""), msg);
        assert_eq!(
            super::redact_token("no secret here", "sekret-123"),
            "no secret here"
        );
    }

    #[test]
    fn show_all_tables_query_lists_tables() {
        let setup = vec![
            "CREATE SCHEMA s; CREATE TABLE s.t1 (i INTEGER); CREATE TABLE s.t2 (i INTEGER);"
                .to_string(),
        ];
        let result = run_duckdb_query(
            &setup,
            "SELECT \"schema\", name FROM (SHOW ALL TABLES) WHERE database = ? ORDER BY \"schema\", name",
            duckdb::params!["memory"],
            None,
        )
        .expect("query should succeed");

        assert_eq!(result.columns, vec!["schema", "name"]);
        assert_eq!(
            result.rows,
            vec![
                vec![serde_json::json!("s"), serde_json::json!("t1")],
                vec![serde_json::json!("s"), serde_json::json!("t2")],
            ]
        );
    }

    #[test]
    fn query_requires_catalog_name() {
        let result = catalogs_cmd().try_get_matches_from(["catalogs", "query"]);
        assert!(result.is_err());
    }

    #[test]
    fn query_accepts_sql_flag_and_environment() {
        let matches = catalogs_cmd()
            .try_get_matches_from([
                "catalogs",
                "query",
                "my-catalog",
                "--sql",
                "SELECT 1",
                "-e",
                "production",
            ])
            .expect("query with --sql should parse");

        let (_, query_args) = matches.subcommand().expect("expected query subcommand");

        assert_eq!(
            query_args.get_one::<String>("catalog_name").unwrap(),
            "my-catalog"
        );
        assert_eq!(query_args.get_one::<String>("sql").unwrap(), "SELECT 1");
        assert_eq!(
            query_args.get_one::<String>("environment").unwrap(),
            "production"
        );
    }

    #[test]
    fn query_sql_flag_is_optional() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "query", "my-catalog"])
            .expect("query without --sql should parse");

        let (_, query_args) = matches.subcommand().expect("expected query subcommand");

        assert!(query_args.get_one::<String>("sql").is_none());
        assert_eq!(
            query_args.get_one::<String>("environment").unwrap(),
            "default"
        );
    }

    #[test]
    fn attach_statements_escapes_values_and_uses_catalog() {
        let credentials = CatalogCredentials::new(
            "https://catalog.example.com".to_string(),
            "2026-06-26T12:00:00Z".to_string(),
            "read".to_string(),
            "secret'token".to_string(),
            "warehouse-id".to_string(),
        );

        let sql = attach_statements(
            "my\"catalog",
            &credentials,
            vend_catalog_credentials_body::Mode::Read,
        )
        .join("\n");

        assert!(sql.contains("TOKEN 'secret''token'"));
        assert!(
            sql.contains("ATTACH 'warehouse-id' AS \"my\"\"catalog\" (TYPE iceberg, READ_ONLY,")
        );
        assert!(sql.contains("ENDPOINT 'https://catalog.example.com'"));
        assert!(!sql.contains("USE "));

        let write_sql = attach_statements(
            "my\"catalog",
            &credentials,
            vend_catalog_credentials_body::Mode::ReadWrite,
        )
        .join("\n");
        assert!(!write_sql.contains("READ_ONLY"));
        assert!(write_sql.contains(
            "ATTACH 'warehouse-id' AS \"my\"\"catalog\" (TYPE iceberg, SECRET tower_cat,"
        ));
    }

    #[test]
    fn query_write_flag_defaults_to_false() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "query", "my-catalog", "--sql", "SELECT 1"])
            .expect("query should parse");
        let (_, query_args) = matches.subcommand().expect("expected query subcommand");
        assert_eq!(query_args.get_one::<bool>("write").copied(), Some(false));

        let matches = catalogs_cmd()
            .try_get_matches_from([
                "catalogs",
                "query",
                "my-catalog",
                "--sql",
                "DELETE FROM t",
                "--write",
            ])
            .expect("query --write should parse");
        let (_, query_args) = matches.subcommand().expect("expected query subcommand");
        assert_eq!(query_args.get_one::<bool>("write").copied(), Some(true));
    }

    #[test]
    fn duckdb_values_convert_to_json() {
        use duckdb::types::{TimeUnit, Value};

        assert_eq!(duckdb_value_to_json(Value::Null), serde_json::Value::Null);
        assert_eq!(
            duckdb_value_to_json(Value::BigInt(42)),
            serde_json::json!(42)
        );
        assert_eq!(
            duckdb_value_to_json(Value::Text("hi".to_string())),
            serde_json::json!("hi")
        );
        assert_eq!(
            duckdb_value_to_json(Value::Timestamp(TimeUnit::Microsecond, 0)),
            serde_json::json!("1970-01-01 00:00:00")
        );
        assert_eq!(
            duckdb_value_to_json(Value::Date32(1)),
            serde_json::json!("1970-01-02")
        );
    }

    #[test]
    fn run_duckdb_query_returns_columns_and_rows() {
        let setup = vec![
            "CREATE TABLE t (id INTEGER, name VARCHAR); INSERT INTO t VALUES (1, 'a'), (2, NULL);"
                .to_string(),
        ];
        let result = run_duckdb_query(&setup, "SELECT id, name FROM t ORDER BY id", [], None)
            .expect("query should succeed");

        assert_eq!(result.columns, vec!["id", "name"]);
        assert_eq!(result.rows.len(), 2);
        assert_eq!(
            result.rows[0],
            vec![serde_json::json!(1), serde_json::json!("a")]
        );
        assert_eq!(
            result.rows[1],
            vec![serde_json::json!(2), serde_json::Value::Null]
        );
    }

    #[test]
    fn nested_duckdb_values_convert_to_json_structures() {
        let result = run_duckdb_query(
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
    fn run_duckdb_query_reports_columns_for_empty_results() {
        let result = run_duckdb_query(&[], "SELECT 1 AS x WHERE 1 = 0", [], None)
            .expect("query should succeed");

        assert_eq!(result.columns, vec!["x"]);
        assert!(result.rows.is_empty());
    }

    #[test]
    fn run_duckdb_query_caps_rows_and_flags_truncation() {
        let capped = run_duckdb_query(&[], "SELECT * FROM range(5) AS t(i)", [], Some(3))
            .expect("query should succeed");
        assert_eq!(capped.rows.len(), 3);
        assert!(capped.truncated);

        let exact = run_duckdb_query(&[], "SELECT * FROM range(3) AS t(i)", [], Some(3))
            .expect("query should succeed");
        assert_eq!(exact.rows.len(), 3);
        assert!(!exact.truncated);
    }

    // --- Sandbox primitive gates -----------------------------------------

    #[test]
    fn contains_multiple_statements_ignores_separators_in_strings_and_comments() {
        assert!(!contains_multiple_statements("SELECT 1"));
        assert!(!contains_multiple_statements("SELECT 1;"));
        assert!(!contains_multiple_statements("  SELECT 1 ;  "));
        assert!(!contains_multiple_statements("SELECT 'a;b'"));
        assert!(!contains_multiple_statements("SELECT 1 -- ; not a statement"));
        assert!(!contains_multiple_statements("SELECT 1; -- trailing comment"));
        assert!(!contains_multiple_statements("SELECT /* ; */ 1"));

        assert!(contains_multiple_statements("SELECT 1; SELECT 2"));
        assert!(contains_multiple_statements("SELECT 1; DROP TABLE t"));
        assert!(contains_multiple_statements("SELECT 'a;b'; SELECT 2"));
    }

    #[test]
    fn write_statements_are_detected_through_case_and_comments() {
        assert_eq!(first_sql_keyword("  SELECT 1"), "select");
        assert_eq!(first_sql_keyword("/* c */ INSERT INTO t VALUES (1)"), "insert");
        assert_eq!(first_sql_keyword("-- lead\nDELETE FROM t"), "delete");

        assert!(!is_write_statement("SELECT * FROM t"));
        assert!(!is_write_statement("WITH x AS (SELECT 1) SELECT * FROM x"));
        assert!(is_write_statement("insert into t values (1)"));
        assert!(is_write_statement("  DROP TABLE t"));
        assert!(is_write_statement("COPY t TO 'out.csv'"));
        assert!(is_write_statement("ATTACH 'x' AS y"));
    }

    #[test]
    fn agent_hardening_allows_selects_but_blocks_local_files_and_config_changes() {
        let setup = agent_hardening_statements();

        let ok = run_duckdb_query(&setup, "SELECT 1 AS x", [], None)
            .expect("a plain select should still run under the hardened session");
        assert_eq!(ok.columns, vec!["x"]);
        assert_eq!(ok.rows, vec![vec![serde_json::json!(1)]]);

        let fs_err = run_duckdb_query(&setup, "SELECT * FROM read_csv('Cargo.toml')", [], None)
            .expect_err("local filesystem access should be blocked");
        assert!(
            fs_err.to_string().to_lowercase().contains("disabled"),
            "unexpected error: {fs_err}"
        );

        let cfg_err = run_duckdb_query(&setup, "SET memory_limit = '1GB'", [], None)
            .expect_err("configuration should be locked");
        let cfg_msg = cfg_err.to_string().to_lowercase();
        assert!(
            cfg_msg.contains("lock") || cfg_msg.contains("configuration"),
            "unexpected error: {cfg_err}"
        );
    }

    /// Regression check against real Iceberg data. The other `run_duckdb_query`
    /// tests use plain in-memory tables; this one writes a small Iceberg table
    /// with DuckDB's `COPY … (FORMAT iceberg)` (real metadata + manifests +
    /// parquet) and reads it back, so the iceberg reader and our column/row
    /// extraction are exercised end to end, NULLs and the row cap included.
    /// Needs the `iceberg` extension, fetched on first run and then cached.
    #[test]
    fn iceberg_scan_reads_written_table_through_run_duckdb_query() {
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

        let result = run_duckdb_query(
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

        let capped = run_duckdb_query(
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

    /// A statement run under the full agent hardening. Extensions are not
    /// loaded, so the attacks below must be blocked by the session lockdown
    /// alone.
    fn run_hardened(sql: &str) -> Result<super::QueryResult, duckdb::Error> {
        run_duckdb_query(&agent_hardening_statements(), sql, [], None)
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
            assert!(contains_multiple_statements(sql), "smuggled statement not caught: {sql}");
        }
        assert!(!contains_multiple_statements(
            "SELECT * FROM runs -- a trailing ; comment"
        ));
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

    /// The coverage the local-only tests can't give: it proves the hardening
    /// does NOT break a real object-store Iceberg read (the reader uses
    /// S3FileSystem, which the hardening leaves enabled) while local-filesystem
    /// access and configuration changes stay blocked in the same session. Starts
    /// a MinIO container via testcontainers and self-skips when no Docker daemon
    /// is available, so a plain `cargo test` still passes without Docker.
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
        setup.extend(agent_hardening_statements());

        let read = run_duckdb_query(
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

        let local = run_duckdb_query(&setup, "SELECT * FROM read_csv('/etc/hostname')", [], None)
            .expect_err("local filesystem reads must stay blocked");
        assert!(
            local.to_string().to_lowercase().contains("disabled"),
            "unexpected error: {local}"
        );

        let cfg = run_duckdb_query(&setup, "SET memory_limit = '1GB'", [], None)
            .expect_err("configuration must stay locked");
        let cfg = cfg.to_string().to_lowercase();
        assert!(
            cfg.contains("lock") || cfg.contains("configuration"),
            "unexpected error: {cfg}"
        );
    }

    #[test]
    fn token_export_command_fetches_token_without_printing_it() {
        let credentials = CatalogCredentials::new(
            "https://catalog.example.com".to_string(),
            "2026-06-26T12:00:00Z".to_string(),
            "read".to_string(),
            "secret-token".to_string(),
            "warehouse-id".to_string(),
        );

        let command =
            token_export_command("default", "production", "read", "http://localhost:8000/");

        assert!(command.contains("export TOWER_CATALOG_TOKEN="));
        assert!(command.contains("tower --tower-url 'http://localhost:8000/' --json"));
        assert!(command.contains("catalogs credentials 'default'"));
        assert!(command.contains("--environment 'production'"));
        assert!(!command.contains(&credentials.oauth_token));
    }

    #[test]
    fn pyiceberg_snippet_reads_token_from_environment_by_default() {
        let credentials = CatalogCredentials::new(
            "https://catalog.example.com".to_string(),
            "2026-06-26T12:00:00Z".to_string(),
            "read".to_string(),
            "secret-token".to_string(),
            "warehouse-id".to_string(),
        );

        let snippets = snippets("default", &credentials, "pyiceberg", false);

        assert_eq!(snippets.len(), 1);
        assert!(snippets[0].body.contains("load_catalog"));
        assert!(snippets[0]
            .body
            .contains("os.environ[\"TOWER_CATALOG_TOKEN\"]"));
        assert!(!snippets[0].body.contains("secret-token"));
    }

    #[test]
    fn duckdb_snippet_attaches_catalog_with_secret() {
        let credentials = CatalogCredentials::new(
            "https://catalog.example.com".to_string(),
            "2026-06-26T12:00:00Z".to_string(),
            "read".to_string(),
            "secret-token".to_string(),
            "warehouse-id".to_string(),
        );

        let snippets = snippets("default", &credentials, "duckdb", false);

        assert_eq!(snippets.len(), 1);
        assert!(snippets[0]
            .body
            .contains("CREATE OR REPLACE SECRET tower_cat (TYPE iceberg"));
        assert!(snippets[0]
            .body
            .contains("ATTACH 'warehouse-id' AS \"default\""));
        assert!(snippets[0]
            .body
            .contains("ENDPOINT 'https://catalog.example.com'"));
        assert!(snippets[0].body.contains("TOKEN '${TOWER_CATALOG_TOKEN}'"));
        assert!(!snippets[0].body.contains("secret-token"));
    }

    #[test]
    fn all_snippet_templates_fully_render() {
        let credentials = CatalogCredentials::new(
            "https://catalog.example.com".to_string(),
            "2026-06-26T12:00:00Z".to_string(),
            "read".to_string(),
            "secret-token".to_string(),
            "warehouse-id".to_string(),
        );

        for show_token in [false, true] {
            let rendered = snippets("default", &credentials, "all", show_token);
            assert_eq!(rendered.len(), 4);
            for snippet in &rendered {
                assert!(
                    !snippet.body.contains("__TOWER_"),
                    "unsubstituted marker in {} snippet (show_token={})",
                    snippet.title,
                    show_token
                );
            }
        }
    }
}
