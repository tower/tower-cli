use clap::{value_parser, Arg, ArgAction, ArgMatches, Command};
use colored::Colorize;
use config::Config;
use tower_api::models::{
    vend_catalog_credentials_body, CatalogCredentials, DescribeCatalogResponse,
};

use crate::{api, output, util::cmd};

const STORAGE_CATALOG_TYPE: &str = "tower-catalog";

pub fn catalogs_cmd() -> Command {
    Command::new("catalogs")
        .about("Interact with the catalogs in your Tower account")
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
                        .help("List Tower-managed storage catalogs")
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
                .about("Show the details of a catalog, including its property names"),
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
                .about("Vend short-lived catalog credentials for external tools"),
        )
}

pub async fn do_list(config: Config, args: &ArgMatches) {
    let all = cmd::get_bool_flag(args, "all");
    let env = cmd::get_string_flag(args, "environment");
    let catalog_type = if cmd::get_bool_flag(args, "storage") {
        Some(STORAGE_CATALOG_TYPE)
    } else {
        args.get_one::<String>("type").map(String::as_str)
    };

    let catalogs = output::with_spinner(
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
    output::table(headers, data, Some(&catalogs));
}

pub async fn do_credentials(config: Config, args: &ArgMatches) {
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

    let response = output::with_spinner(
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
    output::text(&human, &response);
}

pub async fn do_show(config: Config, args: &ArgMatches) {
    let name = args
        .get_one::<String>("catalog_name")
        .expect("catalog_name is required");
    let env = cmd::get_string_flag(args, "environment");

    match api::describe_catalog(&config, name, &env).await {
        Ok(response) => {
            let human = catalog_details_text(&response);
            output::text(&human, &response);
        }
        Err(err) => output::tower_error_and_die(err, "Fetching catalog details failed"),
    }
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
    use super::{catalogs_cmd, parse_mode, snippets, token_export_command};
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
