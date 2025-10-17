use clap::{value_parser, Arg, Command};
use config::{Config, Session};

pub mod api;
mod apps;
mod deploy;
mod environments;
pub mod error;
mod mcp;
pub mod output;
mod package;
mod run;
mod schedules;
mod secrets;
mod session;
mod teams;
mod towerfile_gen;
mod util;
mod version;

pub use error::Error;

pub struct App {
    session: Option<Session>,
    cmd: Command,
}

impl App {
    pub fn new() -> Self {
        let cmd = root_cmd();

        // In certain scenarios, we want to load a session from a JWT token supplied as an
        // environment variable. This is for programmatic use cases where we want to test the CLI
        // in automated environments, for instance.
        let session = if let Ok(token) = std::env::var("TOWER_JWT") {
            Session::from_jwt(&token).ok()
        } else {
            Session::from_config_dir().ok()
        };

        Self { cmd, session }
    }

    async fn check_latest_version() -> Option<String> {
        if tower_version::should_check_latest_version().await {
            let res = tower_version::check_latest_version().await;
            res.unwrap_or(None)
        } else {
            None
        }
    }

    pub async fn run(self) {
        let mut cmd_clone = self.cmd.clone();
        let matches = self.cmd.get_matches();

        let config = Config::from_arg_matches(&matches);

        let sessionized_config = if let Some(session) = self.session {
            config.clone().with_session(session)
        } else {
            config.clone()
        };

        if config.json {
            output::set_output_mode(output::OutputMode::Json);
        }

        if config.debug {
            // Set log level to "DEBUG"
            tower_telemetry::enable_logging(
                tower_telemetry::LogLevel::Debug,
                tower_telemetry::LogFormat::Plain,
                tower_telemetry::LogDestination::Stdout,
            );
        } else {
            tower_telemetry::enable_logging(
                tower_telemetry::LogLevel::Warn,
                tower_telemetry::LogFormat::Plain,
                tower_telemetry::LogDestination::Stdout,
            );
        }

        // Check for newer version only if we successfully get a latest version
        if let Some(latest) = Self::check_latest_version().await {
            let current = tower_version::current_version();

            if current != latest {
                output::write_update_message(&latest, &current);
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
                    Some(("list", _)) => apps::do_list_apps(sessionized_config).await,
                    Some(("create", args)) => apps::do_create(sessionized_config, args).await,
                    Some(("show", args)) => apps::do_show(sessionized_config, args).await,
                    Some(("logs", args)) => apps::do_logs(sessionized_config, args).await,
                    Some(("delete", args)) => apps::do_delete(sessionized_config, args).await,
                    _ => {
                        apps::apps_cmd().print_help().unwrap();
                        std::process::exit(2);
                    }
                }
            }
            Some(("secrets", sub_matches)) => {
                let secrets_command = sub_matches.subcommand();

                match secrets_command {
                    Some(("list", args)) => secrets::do_list(sessionized_config, args).await,
                    Some(("create", args)) => secrets::do_create(sessionized_config, args).await,
                    Some(("delete", args)) => secrets::do_delete(sessionized_config, args).await,
                    _ => {
                        secrets::secrets_cmd().print_help().unwrap();
                        std::process::exit(2);
                    }
                }
            }
            Some(("environments", sub_matches)) => {
                let environments_command = sub_matches.subcommand();

                match environments_command {
                    Some(("list", _)) => environments::do_list(sessionized_config).await,
                    Some(("create", args)) => {
                        environments::do_create(sessionized_config, args).await
                    }
                    _ => {
                        environments::environments_cmd().print_help().unwrap();
                    }
                }
            }
            Some(("schedules", sub_matches)) => {
                let schedules_command = sub_matches.subcommand();

                match schedules_command {
                    Some(("list", args)) => schedules::do_list(sessionized_config, args).await,
                    Some(("create", args)) => schedules::do_create(sessionized_config, args).await,
                    Some(("update", args)) => schedules::do_update(sessionized_config, args).await,
                    Some(("delete", args)) => schedules::do_delete(sessionized_config, args).await,
                    _ => {
                        schedules::schedules_cmd().print_help().unwrap();
                        std::process::exit(2);
                    }
                }
            }
            Some(("deploy", args)) => deploy::do_deploy(sessionized_config, args).await,
            Some(("package", args)) => package::do_package(sessionized_config, args).await,
            Some(("run", args)) => run::do_run(sessionized_config, args, args.subcommand()).await,
            Some(("teams", sub_matches)) => {
                let teams_command = sub_matches.subcommand();

                match teams_command {
                    Some(("list", _)) => teams::do_list(sessionized_config).await,
                    Some(("switch", args)) => teams::do_switch(sessionized_config, args).await,
                    _ => {
                        teams::teams_cmd().print_help().unwrap();
                        std::process::exit(2);
                    }
                }
            }
            Some(("mcp-server", args)) => mcp::do_mcp_server(sessionized_config, args)
                .await
                .unwrap_or_else(|e| {
                    eprintln!("MCP server error: {}", e);
                    std::process::exit(1);
                }),
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
                .long("debug")
                .hide(true)
                .action(clap::ArgAction::SetTrue)
                .global(true),
        )
        .arg(
            Arg::new("json")
                .short('j')
                .long("json")
                .help("Output results in JSON format")
                .action(clap::ArgAction::SetTrue)
                .global(true),
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
        .subcommand(schedules::schedules_cmd())
        .subcommand(secrets::secrets_cmd())
        .subcommand(environments::environments_cmd())
        .subcommand(deploy::deploy_cmd())
        .subcommand(package::package_cmd())
        .subcommand(run::run_cmd())
        .subcommand(version::version_cmd())
        .subcommand(teams::teams_cmd())
        .subcommand(mcp::mcp_cmd())
}
