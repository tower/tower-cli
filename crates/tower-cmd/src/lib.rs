use anyhow::Result;
use clap::{Arg, Command, value_parser};
use config::{Config, Session};
use colored::*;

mod apps;
mod secrets;
mod session;
mod deploy;
mod run;
mod version;
pub mod output;
mod util;

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

        let config = Config::from_arg_matches(&matches);
        
        // Create the configuration for the new API client
        let mut configuration = tower_api::apis::configuration::Configuration::new();
        
        // Set the base URL from config
        configuration.base_path = config.tower_url.clone().to_string();
        
        // Add session token if available
        if let Some(session) = &self.session {
            configuration.bearer_access_token = Some(session.token.clone().jwt);
        }

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
                eprintln!("{}", format!("\nA newer version of tower-cli is available: {} (you have {})", 
                    latest_version, current_version).yellow());
                eprintln!("{}", "To upgrade, run: pip install --upgrade tower-cli\n".yellow());
            }
        }

        // If no subcommand was provided, show help and exit
        if matches.subcommand().is_none() {
            cmd_clone.print_help().unwrap();
            std::process::exit(2);
        }

        match matches.subcommand() {
            Some(("login", _)) => session::do_login(config, &configuration).await,
            Some(("version", _)) => version::do_version(config, &configuration).await,
            Some(("apps", sub_matches)) => {
                let apps_command = sub_matches.subcommand();

                match apps_command {
                    Some(("list", _)) => apps::do_list_apps(config, &configuration).await,
                    Some(("show", args)) => apps::do_show_app(config, &configuration, args.subcommand()).await,
                    Some(("logs", args)) => apps::do_logs_app(config, &configuration, args.subcommand()).await,
                    Some(("create", args)) => apps::do_create_app(config, &configuration, args).await,
                    Some(("delete", args)) => apps::do_delete_app(config, &configuration, args.subcommand()).await,
                    _ => {
                        apps::apps_cmd().print_help().unwrap();
                        std::process::exit(2);
                    }
                }
            },
            Some(("secrets", sub_matches)) => {
                let secrets_command = sub_matches.subcommand();

                match secrets_command {
                    Some(("list", args)) => secrets::do_list_secrets(config, &configuration, args).await,
                    Some(("create", args)) => secrets::do_create_secret(config, &configuration, args).await,
                    Some(("delete", args)) => secrets::do_delete_secret(config, &configuration, args.subcommand()).await,
                    _ => {
                        secrets::secrets_cmd().print_help().unwrap();
                        std::process::exit(2);
                    }
                }
            },
            Some(("deploy", args)) => {
                deploy::do_deploy(config, configuration, args).await
            },
            Some(("run", args)) => {
                run::do_run(config, &configuration, args, args.subcommand()).await
            },
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
                .action(clap::ArgAction::SetTrue)
        )
        .arg(
            Arg::new("tower_url")
                .short('u')
                .long("tower-url")
                .hide(true)
                .value_parser(value_parser!(String))
                .action(clap::ArgAction::Set)
        )
        .subcommand_required(false)
        .arg_required_else_help(false)
        .subcommand(session::login_cmd())
        .subcommand(apps::apps_cmd())
        .subcommand(secrets::secrets_cmd())
        .subcommand(deploy::deploy_cmd())
        .subcommand(run::run_cmd())
        .subcommand(version::version_cmd())
}
