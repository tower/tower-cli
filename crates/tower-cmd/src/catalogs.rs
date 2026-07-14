use clap::{value_parser, Arg, ArgAction, ArgMatches, Command};
use colored::Colorize;
use config::Config;
use std::io::{IsTerminal, Read};
use tower_api::models::{
    vend_catalog_credentials_body, CatalogCredentials, DescribeCatalogResponse,
};

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

    let response = match api::describe_catalog(&config, name, &env).await {
        Ok(response) => response,
        Err(err) => out.tower_error_and_die(err, "Fetching catalog details failed"),
    };

    let is_storage = is_storage_catalog_type(Some(&response.catalog.r#type));
    if is_storage {
        beta::notify_once(out, &beta::STORAGE);
    }

    let tables = if is_storage {
        Some(fetch_catalog_tables(out, &config, name, &env).await)
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
        Some(Ok(result)) => {
            let headers = vec!["Schema".to_string(), "Table".to_string()];
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
                        serde_json::json!({
                            "schema": row.first().cloned().unwrap_or(serde_json::Value::Null),
                            "table": row.get(1).cloned().unwrap_or(serde_json::Value::Null),
                        })
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
    let setup_sql = attach_statements(name, &response.credentials, true);
    let sql = format!(
        "SELECT \"schema\", name FROM (SHOW ALL TABLES) WHERE database = {} ORDER BY \"schema\", name",
        sql_string(name),
    );

    let result = tokio::task::spawn_blocking(move || run_duckdb_query(&setup_sql, &sql)).await;
    match result {
        Ok(Ok(query_result)) => {
            spinner.success(out);
            Ok(query_result)
        }
        Ok(Err(err)) => {
            spinner.failure(out);
            Err(redact_token(&err.to_string(), &token))
        }
        Err(err) => {
            spinner.failure(out);
            Err(redact_token(&err.to_string(), &token))
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
    let setup_sql = attach_statements(name, &response.credentials, !write);
    let result = tokio::task::spawn_blocking(move || run_duckdb_query(&setup_sql, &sql)).await;

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

struct QueryResult {
    columns: Vec<String>,
    rows: Vec<Vec<serde_json::Value>>,
}

/// SQL that installs the Iceberg support and attaches the catalog under its
/// Tower name — mirrors `templates/duckdb.sql.tmpl`. No `USE`: DuckDB's `USE`
/// needs a `main` schema, which Iceberg catalogs don't have, so queries must
/// qualify tables as <catalog>.<namespace>.<table>.
fn attach_statements(name: &str, credentials: &CatalogCredentials, read_only: bool) -> String {
    format!(
        "INSTALL httpfs;\n\
         LOAD httpfs;\n\
         INSTALL iceberg;\n\
         LOAD iceberg;\n\
         SET s3_region='eu-central-1';\n\
         CREATE OR REPLACE SECRET tower_cat (TYPE iceberg, TOKEN {token});\n\
         ATTACH {warehouse} AS {name} (TYPE iceberg, {read_only}SECRET tower_cat, ENDPOINT {uri}, DEFAULT_REGION 'eu-central-1');\n",
        read_only = if read_only { "READ_ONLY, " } else { "" },
        token = sql_string(&credentials.oauth_token),
        warehouse = sql_string(&credentials.warehouse),
        name = sql_ident(name),
        uri = sql_string(&credentials.catalog_uri),
    )
}

fn run_duckdb_query(setup_sql: &str, query: &str) -> Result<QueryResult, duckdb::Error> {
    let conn = duckdb::Connection::open_in_memory()?;
    conn.execute_batch(setup_sql)?;

    let mut stmt = conn.prepare(query)?;
    let mut columns: Vec<String> = Vec::new();
    let mut rows = Vec::new();

    {
        let mut result_rows = stmt.query([])?;
        while let Some(row) = result_rows.next()? {
            if columns.is_empty() {
                columns = row.as_ref().column_names();
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

    Ok(QueryResult { columns, rows })
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

fn sql_string(value: &str) -> String {
    format!("'{}'", value.replace('\'', "''"))
}

fn sql_ident(value: &str) -> String {
    format!("\"{}\"", value.replace('"', "\"\""))
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
        sql_string(&credentials.oauth_token)
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
                    ("__TOWER_NAME__", sql_ident(name)),
                    ("__TOWER_URI__", sql_string(&credentials.catalog_uri)),
                    ("__TOWER_WAREHOUSE__", sql_string(&credentials.warehouse)),
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
        let result = run_duckdb_query(
            "CREATE SCHEMA s; CREATE TABLE s.t1 (i INTEGER); CREATE TABLE s.t2 (i INTEGER);",
            "SELECT \"schema\", name FROM (SHOW ALL TABLES) WHERE database = 'memory' ORDER BY \"schema\", name",
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

        let sql = attach_statements("my\"catalog", &credentials, true);

        assert!(sql.contains("TOKEN 'secret''token'"));
        assert!(
            sql.contains("ATTACH 'warehouse-id' AS \"my\"\"catalog\" (TYPE iceberg, READ_ONLY,")
        );
        assert!(sql.contains("ENDPOINT 'https://catalog.example.com'"));
        assert!(!sql.contains("USE "));

        let write_sql = attach_statements("my\"catalog", &credentials, false);
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
        let result = run_duckdb_query(
            "CREATE TABLE t (id INTEGER, name VARCHAR); INSERT INTO t VALUES (1, 'a'), (2, NULL);",
            "SELECT id, name FROM t ORDER BY id",
        )
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
    fn run_duckdb_query_reports_columns_for_empty_results() {
        let result =
            run_duckdb_query("", "SELECT 1 AS x WHERE 1 = 0").expect("query should succeed");

        assert_eq!(result.columns, vec!["x"]);
        assert!(result.rows.is_empty());
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
