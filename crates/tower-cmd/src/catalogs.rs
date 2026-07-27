use clap::{value_parser, Arg, ArgAction, ArgMatches, Command};
use colored::Colorize;
use config::Config;
use futures_util::StreamExt;
use std::io::{IsTerminal, Read};
use std::time::{Duration, Instant};
use tower_api::models::{
    catalog_fact, update_catalog_fact_body, vend_catalog_credentials_body, CatalogCredentials,
    CatalogFact, DescribeCatalogResponse, UpdateCatalogFactBody,
};
use tower_duckdb::{guard, params, run_query, Hardening, Limits, QueryResult, Session};
use tower_telemetry::debug;

use crate::{api, beta, output, util::cmd};

const STORAGE_CATALOG_TYPE: &str = "tower-catalog";

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
        .subcommand(knowledge_cmd())
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
                .arg(
                    Arg::new("max_rows")
                        .long("max-rows")
                        .value_parser(value_parser!(usize))
                        .help("Maximum rows to return; 0 for no limit. Also lifts the result size limit, so a large result can exhaust memory")
                        .action(ArgAction::Set),
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
            run_query(
                &setup,
                "SELECT \"schema\", name FROM (SHOW ALL TABLES) WHERE database = ? ORDER BY \"schema\", name",
                params![db_name],
                &Limits::none(),
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
    // Read mode runs untrusted SQL, so gate it through DuckDB's parser before it
    // reaches the query path: it must be exactly one SELECT. A smuggled second
    // statement would otherwise execute as a side effect of `prepare`, and a
    // write should fail with a clear message rather than a raw engine error.
    // Write mode is the trusted power-user path and skips the gate.
    if !write {
        let sql_to_check = sql.clone();
        let verdict =
            tokio::task::spawn_blocking(move || guard::classify_read_only(&sql_to_check)).await;
        match verdict {
            Ok(Ok(guard::ReadOnlyCheck::Allowed)) => {}
            Ok(Ok(guard::ReadOnlyCheck::Empty)) => {
                out.die("No SQL statement provided. Pass one with --sql or pipe it via stdin.")
            }
            Ok(Ok(guard::ReadOnlyCheck::Multiple)) => {
                out.die("Only a single SQL statement can be run at a time. Remove the extra statement(s).")
            }
            Ok(Ok(guard::ReadOnlyCheck::NotReadOnly)) => out.die(
                "This command runs read-only queries. Only a single SELECT statement is allowed; re-run with --write to modify the catalog.",
            ),
            Ok(Ok(guard::ReadOnlyCheck::DeniedFunction(name))) => out.die(&format!(
                "'{name}' is not allowed in a read-only query: it changes engine state, runs SQL built at runtime, or reads outside the catalog. Remove it, or re-run with --write."
            )),
            Ok(Ok(guard::ReadOnlyCheck::DeniedTableReference(reference))) => out.die(&format!(
                "'{reference}' is a file or URL, not a table in this catalog. Read-only queries can only read the catalog's own tables; re-run with --write to read elsewhere."
            )),
            Ok(Err(err)) => out.die(&format!("Could not validate the query: {err}")),
            Err(err) => out.die(&format!("Could not validate the query: {err}")),
        }
    }
    let limits = query_limits(write, args.get_one::<usize>("max_rows").copied());
    let query_result = execute_catalog_query(out, &config, name, &env, sql, write, limits).await;
    output_query_result(out, &query_result);
}

/// The result ceilings for a query.
///
/// Read mode defaults to bounded, so a runaway query cannot flood a terminal or a
/// model's context. `--max-rows` is the escape hatch for a caller that knowingly
/// wants more: it sets the row ceiling and lifts the size ceiling, because a
/// caller who asked for a million rows should not then be cut off by a byte
/// budget they never saw. `--max-rows 0` removes the ceilings entirely. Write
/// mode is the trusted path and is unbounded unless a row count is asked for.
fn query_limits(write: bool, max_rows: Option<usize>) -> Limits {
    match max_rows {
        Some(0) => Limits::none(),
        Some(rows) => Limits {
            max_rows: Some(rows),
            max_total_bytes: None,
            timeout: None,
        },
        None if write => Limits::none(),
        None => Limits {
            max_rows: Some(guard::AGENT_MAX_ROWS),
            max_total_bytes: Some(guard::AGENT_MAX_RESULT_BYTES),
            timeout: None,
        },
    }
}

/// Vends credentials for the catalog, attaches it in an in-memory DuckDB, and
/// runs `sql` against it. In read mode (the default) the session is hardened
/// after attach and the result is bounded by `limits`, so an untrusted query
/// cannot read the host or pull an unbounded table back. `write` vends read-write
/// credentials, lets the attach write, and runs the query trusted. Dies with a
/// user-facing error on failure.
async fn execute_catalog_query(
    out: &output::Out,
    config: &Config,
    name: &str,
    env: &str,
    sql: String,
    write: bool,
    limits: Limits,
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
    // Read mode is the sandboxed path: lock the session down after attach so the
    // query cannot read the host or unwind the config. `limits` bounds the result
    // (see `query_limits`). No wall-clock ceiling on this path, because a
    // legitimate analytical scan over a large catalog can take minutes and a
    // person is driving; the agent path uses `Limits::agent()`, which adds one.
    let harden = !write;
    let result = tokio::task::spawn_blocking(move || -> Result<QueryResult, tower_duckdb::Error> {
        let session = Session::open()?;
        session.run_setup(&setup)?;
        if harden {
            // `Hardening::agent()` adds an engine memory ceiling on top of the
            // lockdown. The result `limits` bound what comes back; only the engine
            // can bound what a query spends producing it.
            session.harden(&Hardening::agent())?;
        }
        session.query(&sql, [], &limits)
    })
    .await;

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
        truncated: None,
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
    match result.truncated {
        Some(tower_duckdb::Truncation::Rows) => out.note(&format!(
            "\nShowing the first {} row(s); result truncated at the row limit. Add a LIMIT or filter to narrow it.\n",
            result.rows.len()
        )),
        Some(tower_duckdb::Truncation::Bytes) => out.note(&format!(
            "\nShowing {} row(s); result truncated at the size limit. Select fewer columns, or filter to narrow it.\n",
            result.rows.len()
        )),
        None => out.note(&format!("\n{} row(s)\n", result.rows.len())),
    }
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

/// The values `--scope` accepts, mirroring `catalog_fact::Scope`.
const KNOWLEDGE_SCOPES: [&str; 5] = ["catalog", "namespace", "table", "column", "metric"];

/// The values `--confidence` accepts, mirroring `catalog_fact::Confidence`.
const KNOWLEDGE_CONFIDENCES: [&str; 3] = ["confirmed", "heuristic", "inferred"];

fn knowledge_cmd() -> Command {
    let catalog_arg = Arg::new("catalog_name")
        .value_parser(value_parser!(String))
        .index(1)
        .required(true)
        .help("Name of the catalog");
    let name_arg = Arg::new("name")
        .value_parser(value_parser!(String))
        .index(2)
        .required(true)
        .help("Name of the knowledge entry");
    let environment_arg = Arg::new("environment")
        .short('e')
        .long("environment")
        .default_value("default")
        .value_parser(value_parser!(String))
        .help("Environment the catalog belongs to")
        .action(ArgAction::Set);

    Command::new("knowledge")
        .about(beta::STORAGE.short_about(
            "Store and retrieve knowledge about the semantics of the data in a catalog",
        ))
        .after_help(
            "Knowledge lets agents (and people) record context about a catalog's data — \
             semantics, ontology, conventions — scoped to the catalog itself or to a \
             namespace, table, column, or metric within it.",
        )
        .arg_required_else_help(true)
        .subcommand(
            Command::new("list")
                .arg(catalog_arg.clone())
                .arg(environment_arg.clone())
                .arg(
                    Arg::new("scope")
                        .long("scope")
                        .value_parser(KNOWLEDGE_SCOPES)
                        .help("Only list knowledge with this scope")
                        .action(ArgAction::Set),
                )
                .arg(
                    Arg::new("object")
                        .long("object")
                        .value_parser(value_parser!(String))
                        .help("Only list knowledge about this object path, e.g. bronze.runs.deleted_at")
                        .action(ArgAction::Set),
                )
                .about("List the knowledge recorded for a catalog"),
        )
        .subcommand(
            Command::new("show")
                .arg(catalog_arg.clone())
                .arg(name_arg.clone())
                .arg(environment_arg.clone())
                .about("Show the full details of a knowledge entry, including its body"),
        )
        .subcommand(
            Command::new("set")
                .arg(catalog_arg.clone())
                .arg(name_arg.clone())
                .arg(environment_arg.clone())
                .arg(
                    Arg::new("statement")
                        .long("statement")
                        .value_parser(value_parser!(String))
                        .required(true)
                        .help("The human-readable meaning of the entry")
                        .action(ArgAction::Set),
                )
                .arg(
                    Arg::new("scope")
                        .long("scope")
                        .default_value("catalog")
                        .value_parser(KNOWLEDGE_SCOPES)
                        .help("What kind of object the entry is about")
                        .action(ArgAction::Set),
                )
                .arg(
                    Arg::new("object")
                        .long("object")
                        .value_parser(value_parser!(String))
                        .help("Path to what the entry is about, e.g. bronze.runs.deleted_at; omit for catalog-scoped knowledge")
                        .action(ArgAction::Set),
                )
                .arg(
                    Arg::new("confidence")
                        .long("confidence")
                        .default_value("confirmed")
                        .value_parser(KNOWLEDGE_CONFIDENCES)
                        .help("How trustworthy the entry is")
                        .action(ArgAction::Set),
                )
                .arg(
                    Arg::new("source")
                        .long("source")
                        .value_parser(value_parser!(String))
                        .help("Where the knowledge came from (agent id, user, ...)")
                        .action(ArgAction::Set),
                )
                .arg(
                    Arg::new("body")
                        .long("body")
                        .value_parser(value_parser!(String))
                        .help("Optional structured payload (SQL, unit, enum values) as a JSON string")
                        .action(ArgAction::Set),
                )
                .about("Create a knowledge entry, or replace it if one with the same name exists"),
        )
        .subcommand(
            Command::new("delete")
                .arg(catalog_arg)
                .arg(name_arg)
                .arg(environment_arg)
                .about("Delete a knowledge entry from a catalog"),
        )
}

pub async fn do_knowledge_list(out: &output::Out, config: Config, args: &ArgMatches) {
    beta::notify_once(out, &beta::STORAGE);

    let catalog = args
        .get_one::<String>("catalog_name")
        .expect("catalog_name is required");
    let env = cmd::get_string_flag(args, "environment");
    let scope = args.get_one::<String>("scope").map(String::as_str);
    let object = args.get_one::<String>("object").map(String::as_str);

    let response = out
        .with_spinner(
            "Listing knowledge",
            api::list_catalog_knowledge(&config, catalog, &env, scope, object),
        )
        .await;

    let headers = vec!["Name", "Scope", "Object", "Confidence", "Statement"]
        .into_iter()
        .map(str::to_string)
        .collect();
    let data = response
        .facts
        .iter()
        .map(|entry| {
            vec![
                entry.name.clone(),
                knowledge_scope_str(entry.scope).to_string(),
                entry.object.clone(),
                knowledge_confidence_str(entry.confidence).to_string(),
                truncate_statement(&entry.statement, 80),
            ]
        })
        .collect();
    out.table(headers, data, Some(&response.facts));
}

pub async fn do_knowledge_show(out: &output::Out, config: Config, args: &ArgMatches) {
    beta::notify_once(out, &beta::STORAGE);

    let catalog = args
        .get_one::<String>("catalog_name")
        .expect("catalog_name is required");
    let name = args
        .get_one::<String>("name")
        .expect("name is required");
    let env = cmd::get_string_flag(args, "environment");

    let response = out
        .with_spinner(
            "Fetching knowledge",
            api::describe_catalog_knowledge(&config, catalog, name, &env),
        )
        .await;

    let human = knowledge_details_text(catalog, &env, &response.fact);
    out.text(&human, &response);
}

pub async fn do_knowledge_set(out: &output::Out, config: Config, args: &ArgMatches) {
    beta::notify_once(out, &beta::STORAGE);

    let catalog = args
        .get_one::<String>("catalog_name")
        .expect("catalog_name is required");
    let name = args
        .get_one::<String>("name")
        .expect("name is required");
    let env = cmd::get_string_flag(args, "environment");
    let statement = cmd::get_string_flag(args, "statement");
    let scope = cmd::get_string_flag(args, "scope");
    let confidence = cmd::get_string_flag(args, "confidence");
    let object = args.get_one::<String>("object").cloned();
    let source = args.get_one::<String>("source").cloned();
    let body = args.get_one::<String>("body").cloned();

    // The API carries the body as a JSON string; catch malformed JSON here so
    // the error names the flag instead of surfacing as a server-side 400.
    if let Some(body) = &body {
        if let Err(err) = serde_json::from_str::<serde_json::Value>(body) {
            out.die(&format!("--body is not valid JSON: {}", err));
        }
    }

    let knowledge_body = UpdateCatalogFactBody {
        schema: None,
        body,
        confidence: parse_knowledge_confidence(&confidence),
        object,
        scope: parse_knowledge_scope(&scope),
        source,
        statement,
    };

    let response = out
        .with_spinner(
            "Saving knowledge",
            api::update_catalog_knowledge(&config, catalog, name, &env, knowledge_body),
        )
        .await;

    out.success_with_data(
        &format!("Knowledge '{}' saved in catalog '{}'", name, catalog),
        Some(&response),
    );
}

pub async fn do_knowledge_delete(out: &output::Out, config: Config, args: &ArgMatches) {
    beta::notify_once(out, &beta::STORAGE);

    let catalog = args
        .get_one::<String>("catalog_name")
        .expect("catalog_name is required");
    let name = args
        .get_one::<String>("name")
        .expect("name is required");
    let env = cmd::get_string_flag(args, "environment");

    out.with_spinner(
        "Deleting knowledge",
        api::delete_catalog_knowledge(&config, catalog, name, &env),
    )
    .await;

    out.success(&format!(
        "Knowledge '{}' deleted from catalog '{}'",
        name, catalog
    ));
}

fn knowledge_scope_str(scope: catalog_fact::Scope) -> &'static str {
    match scope {
        catalog_fact::Scope::Catalog => "catalog",
        catalog_fact::Scope::Namespace => "namespace",
        catalog_fact::Scope::Table => "table",
        catalog_fact::Scope::Column => "column",
        catalog_fact::Scope::Metric => "metric",
    }
}

fn knowledge_confidence_str(confidence: catalog_fact::Confidence) -> &'static str {
    match confidence {
        catalog_fact::Confidence::Confirmed => "confirmed",
        catalog_fact::Confidence::Heuristic => "heuristic",
        catalog_fact::Confidence::Inferred => "inferred",
    }
}

fn parse_knowledge_scope(scope: &str) -> update_catalog_fact_body::Scope {
    match scope {
        "namespace" => update_catalog_fact_body::Scope::Namespace,
        "table" => update_catalog_fact_body::Scope::Table,
        "column" => update_catalog_fact_body::Scope::Column,
        "metric" => update_catalog_fact_body::Scope::Metric,
        _ => update_catalog_fact_body::Scope::Catalog,
    }
}

fn parse_knowledge_confidence(confidence: &str) -> update_catalog_fact_body::Confidence {
    match confidence {
        "heuristic" => update_catalog_fact_body::Confidence::Heuristic,
        "inferred" => update_catalog_fact_body::Confidence::Inferred,
        _ => update_catalog_fact_body::Confidence::Confirmed,
    }
}

/// Trims a statement to fit a table cell, on a char boundary, marking the cut
/// with an ellipsis. The full statement is always in the JSON output.
fn truncate_statement(statement: &str, max_chars: usize) -> String {
    if statement.chars().count() <= max_chars {
        statement.to_string()
    } else {
        let truncated: String = statement
            .chars()
            .take(max_chars.saturating_sub(1))
            .collect();
        format!("{}…", truncated)
    }
}

fn knowledge_details_text(catalog: &str, env: &str, entry: &CatalogFact) -> String {
    let mut out = String::new();

    out.push_str(&detail_line("Name", &entry.name));
    out.push_str(&detail_line("Catalog", catalog));
    out.push_str(&detail_line("Environment", env));
    out.push_str(&detail_line("Scope", knowledge_scope_str(entry.scope)));
    if !entry.object.is_empty() {
        out.push_str(&detail_line("Object", &entry.object));
    }
    out.push_str(&detail_line(
        "Confidence",
        knowledge_confidence_str(entry.confidence),
    ));
    if let Some(source) = entry.source.as_deref().filter(|s| !s.is_empty()) {
        out.push_str(&detail_line("Source", source));
    }
    out.push_str(&detail_line("Created", &entry.created_at));
    out.push_str(&detail_line("Updated", &entry.updated_at));

    out.push('\n');
    out.push_str(&header_line("Statement"));
    out.push_str(&entry.statement);
    out.push('\n');

    if let Some(body) = entry.body.as_ref().and_then(|b| b.as_ref()) {
        out.push('\n');
        out.push_str(&header_line("Body"));
        out.push_str(&serde_json::to_string_pretty(body).unwrap_or_else(|_| body.to_string()));
        out.push('\n');
    }

    out
}

#[cfg(test)]
mod tests {
    use super::{
        attach_statements, catalogs_cmd, is_storage_catalog_type, parse_mode, query_limits,
        snippets, token_export_command,
    };
    use tower_api::models::{vend_catalog_credentials_body, CatalogCredentials};
    use tower_duckdb::{params, run_query, Limits};

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
        let result = run_query(
            &setup,
            "SELECT \"schema\", name FROM (SHOW ALL TABLES) WHERE database = ? ORDER BY \"schema\", name",
            params!["memory"],
            &Limits::none(),
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
    fn query_accepts_a_max_rows_override() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "query", "my-catalog", "--sql", "SELECT 1"])
            .expect("query should parse");
        let (_, query_args) = matches.subcommand().expect("expected query subcommand");
        assert_eq!(query_args.get_one::<usize>("max_rows").copied(), None);

        let matches = catalogs_cmd()
            .try_get_matches_from([
                "catalogs",
                "query",
                "my-catalog",
                "--sql",
                "SELECT 1",
                "--max-rows",
                "50000",
            ])
            .expect("query --max-rows should parse");
        let (_, query_args) = matches.subcommand().expect("expected query subcommand");
        assert_eq!(query_args.get_one::<usize>("max_rows").copied(), Some(50_000));

        assert!(
            catalogs_cmd()
                .try_get_matches_from([
                    "catalogs",
                    "query",
                    "my-catalog",
                    "--sql",
                    "SELECT 1",
                    "--max-rows",
                    "not-a-number",
                ])
                .is_err(),
            "a non-numeric --max-rows should be rejected"
        );
    }

    #[test]
    fn read_queries_are_bounded_unless_the_caller_asks_otherwise() {
        // The default: bounded by rows and by size, so a runaway read cannot
        // flood a terminal or a model's context.
        let default = query_limits(false, None);
        assert_eq!(default.max_rows, Some(tower_duckdb::guard::AGENT_MAX_ROWS));
        assert_eq!(
            default.max_total_bytes,
            Some(tower_duckdb::guard::AGENT_MAX_RESULT_BYTES)
        );
    }

    #[test]
    fn max_rows_override_raises_the_row_ceiling_and_lifts_the_size_ceiling() {
        // A caller who asks for a million rows should not then be cut short by a
        // byte budget they never set, so the size ceiling comes off with it.
        let raised = query_limits(false, Some(1_000_000));
        assert_eq!(raised.max_rows, Some(1_000_000));
        assert_eq!(
            raised.max_total_bytes, None,
            "an explicit row count should not be second-guessed by the size cap"
        );

        // Lowering it is just as valid as raising it.
        assert_eq!(query_limits(false, Some(10)).max_rows, Some(10));
    }

    #[test]
    fn max_rows_zero_removes_every_result_ceiling() {
        let unbounded = query_limits(false, Some(0));
        assert_eq!(unbounded.max_rows, None);
        assert_eq!(unbounded.max_total_bytes, None);
    }

    #[test]
    fn write_mode_is_unbounded_but_still_honours_an_explicit_row_count() {
        let write_default = query_limits(true, None);
        assert_eq!(write_default.max_rows, None);
        assert_eq!(write_default.max_total_bytes, None);

        assert_eq!(query_limits(true, Some(25)).max_rows, Some(25));
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

    #[test]
    fn knowledge_command_is_marked_beta() {
        let mut command = catalogs_cmd();
        let knowledge_help = command
            .find_subcommand_mut("knowledge")
            .expect("knowledge command should exist")
            .render_help()
            .to_string();
        assert!(knowledge_help.contains("[beta]"));
    }

    #[test]
    fn knowledge_delete_accepts_catalog_and_name() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "knowledge", "delete", "my-catalog", "my-entry"])
            .expect("knowledge delete should parse");

        let (_, knowledge_args) = matches.subcommand().expect("expected knowledge subcommand");
        let (_, delete_args) = knowledge_args.subcommand().expect("expected delete subcommand");
        assert_eq!(
            delete_args.get_one::<String>("catalog_name").unwrap(),
            "my-catalog"
        );
        assert_eq!(
            delete_args.get_one::<String>("name").unwrap(),
            "my-entry"
        );
    }

    #[test]
    fn knowledge_details_text_includes_body_and_optional_fields() {
        use tower_api::models::{catalog_fact, CatalogFact};

        let mut entry = CatalogFact::new(
            catalog_fact::Confidence::Inferred,
            "2026-07-22T00:00:00Z".to_string(),
            "soft-deletes".to_string(),
            "bronze.runs.deleted_at".to_string(),
            catalog_fact::Scope::Column,
            "deleted_at marks soft-deleted rows".to_string(),
            "2026-07-22T01:00:00Z".to_string(),
        );
        entry.source = Some("agent-42".to_string());
        entry.body = Some(Some(serde_json::json!({"sql": "deleted_at IS NULL"})));

        let text = super::knowledge_details_text("my-catalog", "production", &entry);

        assert!(text.contains("soft-deletes"));
        assert!(text.contains("my-catalog"));
        assert!(text.contains("production"));
        assert!(text.contains("column"));
        assert!(text.contains("bronze.runs.deleted_at"));
        assert!(text.contains("inferred"));
        assert!(text.contains("agent-42"));
        assert!(text.contains("deleted_at marks soft-deleted rows"));
        assert!(text.contains("deleted_at IS NULL"));

        // Optional fields drop out when absent.
        entry.source = None;
        entry.body = None;
        entry.object = String::new();
        let text = super::knowledge_details_text("my-catalog", "production", &entry);
        assert!(!text.contains("Source"));
        assert!(!text.contains("Body"));
        assert!(!text.contains("Object"));
    }

    #[test]
    fn knowledge_list_accepts_filters() {
        let matches = catalogs_cmd()
            .try_get_matches_from([
                "catalogs",
                "knowledge",
                "list",
                "my-catalog",
                "--scope",
                "table",
                "--object",
                "bronze.runs",
                "-e",
                "production",
            ])
            .expect("knowledge list should parse");

        let (_, knowledge_args) = matches.subcommand().expect("expected knowledge subcommand");
        let (_, list_args) = knowledge_args.subcommand().expect("expected list subcommand");

        assert_eq!(
            list_args.get_one::<String>("catalog_name").unwrap(),
            "my-catalog"
        );
        assert_eq!(list_args.get_one::<String>("scope").unwrap(), "table");
        assert_eq!(
            list_args.get_one::<String>("object").unwrap(),
            "bronze.runs"
        );
        assert_eq!(
            list_args.get_one::<String>("environment").unwrap(),
            "production"
        );
    }

    #[test]
    fn knowledge_list_rejects_invalid_scope() {
        let result = catalogs_cmd().try_get_matches_from([
            "catalogs",
            "knowledge",
            "list",
            "my-catalog",
            "--scope",
            "bogus",
        ]);
        assert!(result.is_err());
    }

    #[test]
    fn knowledge_scope_and_confidence_round_trip() {
        use tower_api::models::{catalog_fact, update_catalog_fact_body};

        for scope in super::KNOWLEDGE_SCOPES {
            let parsed = super::parse_knowledge_scope(scope);
            let rendered = match parsed {
                update_catalog_fact_body::Scope::Catalog => catalog_fact::Scope::Catalog,
                update_catalog_fact_body::Scope::Namespace => catalog_fact::Scope::Namespace,
                update_catalog_fact_body::Scope::Table => catalog_fact::Scope::Table,
                update_catalog_fact_body::Scope::Column => catalog_fact::Scope::Column,
                update_catalog_fact_body::Scope::Metric => catalog_fact::Scope::Metric,
            };
            assert_eq!(super::knowledge_scope_str(rendered), scope);
        }

        for confidence in super::KNOWLEDGE_CONFIDENCES {
            let parsed = super::parse_knowledge_confidence(confidence);
            let rendered = match parsed {
                update_catalog_fact_body::Confidence::Confirmed => {
                    catalog_fact::Confidence::Confirmed
                }
                update_catalog_fact_body::Confidence::Heuristic => {
                    catalog_fact::Confidence::Heuristic
                }
                update_catalog_fact_body::Confidence::Inferred => {
                    catalog_fact::Confidence::Inferred
                }
            };
            assert_eq!(super::knowledge_confidence_str(rendered), confidence);
        }
    }

    #[test]
    fn knowledge_set_accepts_all_fields() {
        let matches = catalogs_cmd()
            .try_get_matches_from([
                "catalogs",
                "knowledge",
                "set",
                "my-catalog",
                "my-entry",
                "--statement",
                "deleted_at marks soft-deleted rows",
                "--scope",
                "column",
                "--object",
                "bronze.runs.deleted_at",
                "--confidence",
                "inferred",
                "--source",
                "agent-42",
                "--body",
                "{\"sql\": \"deleted_at IS NULL\"}",
            ])
            .expect("knowledge set with all flags should parse");

        let (_, knowledge_args) = matches.subcommand().expect("expected knowledge subcommand");
        let (_, set_args) = knowledge_args.subcommand().expect("expected set subcommand");

        assert_eq!(set_args.get_one::<String>("scope").unwrap(), "column");
        assert_eq!(
            set_args.get_one::<String>("object").unwrap(),
            "bronze.runs.deleted_at"
        );
        assert_eq!(
            set_args.get_one::<String>("confidence").unwrap(),
            "inferred"
        );
        assert_eq!(set_args.get_one::<String>("source").unwrap(), "agent-42");
        assert_eq!(
            set_args.get_one::<String>("body").unwrap(),
            "{\"sql\": \"deleted_at IS NULL\"}"
        );
    }

    #[test]
    fn knowledge_set_defaults_scope_and_confidence() {
        let matches = catalogs_cmd()
            .try_get_matches_from([
                "catalogs",
                "knowledge",
                "set",
                "my-catalog",
                "my-entry",
                "--statement",
                "deleted_at is a soft-delete marker",
            ])
            .expect("knowledge set should parse");

        let (_, knowledge_args) = matches.subcommand().expect("expected knowledge subcommand");
        let (_, set_args) = knowledge_args.subcommand().expect("expected set subcommand");

        assert_eq!(set_args.get_one::<String>("scope").unwrap(), "catalog");
        assert_eq!(
            set_args.get_one::<String>("confidence").unwrap(),
            "confirmed"
        );
        assert!(set_args.get_one::<String>("object").is_none());
        assert!(set_args.get_one::<String>("source").is_none());
        assert!(set_args.get_one::<String>("body").is_none());
    }

    #[test]
    fn knowledge_set_requires_statement() {
        let result =
            catalogs_cmd().try_get_matches_from(["catalogs", "knowledge", "set", "my-catalog", "f"]);
        assert!(result.is_err());
    }

    #[test]
    fn knowledge_show_requires_catalog_and_name() {
        let result =
            catalogs_cmd().try_get_matches_from(["catalogs", "knowledge", "show", "my-catalog"]);
        assert!(result.is_err());

        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "knowledge", "show", "my-catalog", "my-entry"])
            .expect("knowledge show should parse");
        let (_, knowledge_args) = matches.subcommand().expect("expected knowledge subcommand");
        let (_, show_args) = knowledge_args.subcommand().expect("expected show subcommand");
        assert_eq!(show_args.get_one::<String>("name").unwrap(), "my-entry");
        assert_eq!(
            show_args.get_one::<String>("environment").unwrap(),
            "default"
        );
    }

    #[test]
    fn truncate_statement_preserves_short_and_marks_long() {
        assert_eq!(super::truncate_statement("short", 80), "short");
        let long = "x".repeat(100);
        let truncated = super::truncate_statement(&long, 80);
        assert_eq!(truncated.chars().count(), 80);
        assert!(truncated.ends_with('…'));
    }

}
