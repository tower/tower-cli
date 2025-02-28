use anyhow::Result;
use clap::{value_parser, Arg, Command};
use colored::*;
use config::{Config, Session};

mod apps;
mod deploy;
pub mod output;
mod run;
mod secrets;
mod session;
mod teams;
mod util;
mod version;

pub struct App {
    session: Option<Session>,
    cmd: Command,
}

impl App {
    pub fn new() -> Self {
        let cmd = root_cmd();
        let session = Session::from_config_dir().ok();

        Self { cmd, session }
    }

    async fn check_latest_version() -> Result<Option<String>> {
        tower_version::check_latest_version().await
    }

    pub async fn run(self) {
        let mut cmd_clone = self.cmd.clone();
        let matches = self.cmd.get_matches();

        let mut config = Config::from_arg_matches(&matches);

        // Init the configuration for the new API client
        config.init_api_configuration(self.session.as_ref());
        let mut config = Config::from_arg_matches(&matches);

        // Init the configuration for the new API client
        config.init_api_configuration(self.session.as_ref());

        // Setup logging
        simple_logger::SimpleLogger::new()
            .with_module_level("rustyline", log::LevelFilter::Warn)
            .env()
            .init()
            .unwrap();

        if config.debug {
            log::set_max_level(log::LevelFilter::Debug);
        } else {
            log::set_max_level(log::LevelFilter::Info);
        }

        // Check for newer version only if we successfully get a latest version
        if let Ok(Some(latest_version)) = Self::check_latest_version().await {
            let current_version = tower_version::current_version();
            // Compare versions
            if latest_version != current_version {
                eprintln!(
                    "{}",
                    format!(
                        "\nA newer version of tower-cli is available: {} (you have {})",
                        latest_version, current_version
                    )
                    .yellow()
                );
                eprintln!(
                    "{}",
                    "To upgrade, run: pip install --upgrade tower-cli\n".yellow()
                );
                eprintln!(
                    "{}",
                    format!(
                        "\nA newer version of tower-cli is available: {} (you have {})",
                        latest_version, current_version
                    )
                    .yellow()
                );
                eprintln!(
                    "{}",
                    "To upgrade, run: pip install --upgrade tower-cli\n".yellow()
                );
            }
        }

        // If no subcommand was provided, show help and exit
        if matches.subcommand().is_none() {
            cmd_clone.print_help().unwrap();
            std::process::exit(2);
        }

        match matches.subcommand() {
            Some(("login", _)) => session::do_login(config).await,
            Some(("version", _)) => version::do_version().await,
            Some(("apps", sub_matches)) => {
                let apps_command = sub_matches.subcommand();

                match apps_command {
                    Some(("list", _)) => apps::do_list_apps(config).await,
                    Some(("show", args)) => apps::do_show_app(config, args.subcommand()).await,
                    Some(("logs", args)) => apps::do_logs_app(config, args.subcommand()).await,
                    Some(("create", args)) => apps::do_create_app(config, args).await,
                    Some(("delete", args)) => apps::do_delete_app(config, args.subcommand()).await,
                    _ => {
                        apps::apps_cmd().print_help().unwrap();
                        std::process::exit(2);
                    }
                }
            }
            Some(("secrets", sub_matches)) => {
                let secrets_command = sub_matches.subcommand();

                match secrets_command {
                    Some(("list", args)) => secrets::do_list_secrets(config, args).await,
                    Some(("create", args)) => secrets::do_create_secret(config, args).await,
                    Some(("delete", args)) => {
                        secrets::do_delete_secret(config, args.subcommand()).await
                    }
                    _ => {
                        secrets::secrets_cmd().print_help().unwrap();
                        std::process::exit(2);
                    }
                }
            }
            Some(("deploy", args)) => deploy::do_deploy(config, args).await,
            Some(("run", args)) => run::do_run(config, args, args.subcommand()).await,
            Some(("teams", sub_matches)) => {
                let teams_command = sub_matches.subcommand();

                match teams_command {
                    Some(("list", _)) => teams::do_list_teams(config).await,
                    Some(("switch", args)) => teams::do_switch_team(config, args).await,
                    _ => {
                        teams::teams_cmd().print_help().unwrap();
                        std::process::exit(2);
                    }
                }
            }
            _ => {
                cmd_clone.print_help().unwrap();
                std::process::exit(2);
            }
        }
    }
}

fn root_cmd() -> Command {
    Command::new("tower")
        .about("Tower is a compute platform for modern data projects")
        .arg(
            Arg::new("debug")
                .short('d')
                .long("debug")
                .hide(true)
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("tower_url")
                .short('u')
                .long("tower-url")
                .hide(true)
                .value_parser(value_parser!(String))
                .action(clap::ArgAction::Set),
        )
        .subcommand_required(false)
        .arg_required_else_help(false)
        .subcommand(session::login_cmd())
        .subcommand(apps::apps_cmd())
        .subcommand(secrets::secrets_cmd())
        .subcommand(deploy::deploy_cmd())
        .subcommand(run::run_cmd())
        .subcommand(version::version_cmd())
        .subcommand(teams::teams_cmd())
}
