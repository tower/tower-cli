use clap::{value_parser, Arg, ArgMatches, Command};
use colored::Colorize;
use config::Config;

use crate::{api, output, util::cmd};

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
                        .action(clap::ArgAction::Set),
                )
                .arg(
                    Arg::new("all")
                        .short('a')
                        .long("all")
                        .help("List catalogs across all environments")
                        .action(clap::ArgAction::SetTrue),
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
                        .action(clap::ArgAction::Set),
                )
                .about("Show the details of a catalog, including its property names"),
        )
}

pub async fn do_list(config: Config, args: &ArgMatches) {
    let all = cmd::get_bool_flag(args, "all");
    let env = cmd::get_string_flag(args, "environment");

    let list_response =
        output::with_spinner("Listing catalogs", api::list_catalogs(&config, &env, all)).await;

    let headers = vec!["Name", "Type", "Environment"]
        .into_iter()
        .map(str::to_string)
        .collect();
    let data = list_response
        .catalogs
        .iter()
        .map(|catalog| {
            vec![
                catalog.name.clone(),
                catalog.r#type.clone(),
                catalog.environment.clone(),
            ]
        })
        .collect();
    output::table(headers, data, Some(&list_response.catalogs));
}

pub async fn do_show(config: Config, args: &ArgMatches) {
    let name = args
        .get_one::<String>("catalog_name")
        .expect("catalog_name is required");
    let env = cmd::get_string_flag(args, "environment");

    match api::describe_catalog(&config, name, &env).await {
        Ok(response) => {
            if output::get_output_mode().is_json() {
                output::json(&response);
                return;
            }

            let catalog = &response.catalog;

            output::detail("Catalog", &catalog.name);
            output::detail("Type", &catalog.r#type);
            output::detail("Environment", &catalog.environment);

            if !catalog.properties.is_empty() {
                output::newline();
                output::header("Properties");

                let headers = vec!["Name", "Preview"]
                    .into_iter()
                    .map(str::to_string)
                    .collect();
                let data = catalog
                    .properties
                    .iter()
                    .map(|prop| {
                        vec![
                            prop.name.clone(),
                            prop.preview.dimmed().to_string(),
                        ]
                    })
                    .collect();
                output::table(headers, data, Some(&response));
            }
        }
        Err(err) => output::tower_error_and_die(err, "Fetching catalog details failed"),
    }
}

#[cfg(test)]
mod tests {
    use super::catalogs_cmd;

    #[test]
    fn list_defaults_to_default_environment() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "list"])
            .expect("list should parse with no args");

        let (_, list_args) = matches.subcommand().expect("expected list subcommand");

        assert_eq!(list_args.get_one::<String>("environment").unwrap(), "default");
        assert_eq!(list_args.get_one::<bool>("all").copied(), Some(false));
    }

    #[test]
    fn list_accepts_environment_flag() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "list", "-e", "production"])
            .expect("list -e should parse");

        let (_, list_args) = matches.subcommand().expect("expected list subcommand");

        assert_eq!(list_args.get_one::<String>("environment").unwrap(), "production");
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

        assert_eq!(show_args.get_one::<String>("catalog_name").unwrap(), "my-catalog");
        assert_eq!(show_args.get_one::<String>("environment").unwrap(), "default");
    }

    #[test]
    fn show_accepts_environment_override() {
        let matches = catalogs_cmd()
            .try_get_matches_from(["catalogs", "show", "my-catalog", "-e", "production"])
            .expect("show with -e should parse");

        let (_, show_args) = matches.subcommand().expect("expected show subcommand");

        assert_eq!(show_args.get_one::<String>("catalog_name").unwrap(), "my-catalog");
        assert_eq!(show_args.get_one::<String>("environment").unwrap(), "production");
    }
}
