use clap::{value_parser, Arg, Command};
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

    async fn check_latest_version() -> Option<String> {
        let res = tower_version::check_latest_version().await;
        res.unwrap_or(None)
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
                    Some(("show", args)) => {
                        apps::do_show_app(sessionized_config, args.subcommand()).await
                    }
                    Some(("logs", args)) => {
                        apps::do_logs_app(sessionized_config, args.subcommand()).await
                    }
                    Some(("create", args)) => apps::do_create_app(sessionized_config, args).await,
                    Some(("delete", args)) => {
                        apps::do_delete_app(sessionized_config, args.subcommand()).await
                    }
                    _ => {
                        apps::apps_cmd().print_help().unwrap();
                        std::process::exit(2);
                    }
                }
            }
            Some(("secrets", sub_matches)) => {
                let secrets_command = sub_matches.subcommand();

                match secrets_command {
                    Some(("list", args)) => {
                        secrets::do_list_secrets(sessionized_config, args).await
                    }
                    Some(("create", args)) => {
                        secrets::do_create_secret(sessionized_config, args).await
                    }
                    Some(("delete", args)) => {
                        secrets::do_delete_secret(sessionized_config, args.subcommand()).await
                    }
                    _ => {
                        secrets::secrets_cmd().print_help().unwrap();
                        std::process::exit(2);
                    }
                }
            }
            Some(("deploy", args)) => deploy::do_deploy(sessionized_config, args).await,
            Some(("run", args)) => run::do_run(sessionized_config, args, args.subcommand()).await,
            Some(("teams", sub_matches)) => {
                let teams_command = sub_matches.subcommand();

                match teams_command {
                    Some(("list", _)) => teams::do_list_teams(sessionized_config).await,
                    Some(("switch", args)) => teams::do_switch_team(sessionized_config, args).await,
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
