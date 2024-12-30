use clap::{Arg, Command, value_parser};
use config::{Config, Session};
use tower_api::Client;

mod apps;
mod secrets;
mod session;
mod deploy;
mod run;
mod version;
pub mod output;

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

    pub async fn run(self) {
        let matches = self.cmd.get_matches();
        let config = Config::from_arg_matches(&matches);
        let client = Client::from_config(&config)
            .with_optional_session(self.session);

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

        match matches.subcommand() {
            Some(("login", _)) => session::do_login(config, client).await,
            Some(("version", _)) => version::do_version(config, client).await,
            Some(("apps", sub_matches)) => {
                let apps_command = sub_matches.subcommand();

                match apps_command {
                    Some(("list", _)) => apps::do_list_apps(config, client).await,
                    Some(("show", args)) => apps::do_show_app(config, client, args.subcommand()).await,
                    Some(("logs", args)) => apps::do_logs_app(config, client, args.subcommand()).await,
                    Some(("create", args)) => apps::do_create_app(config, client, args).await,
                    Some(("delete", args)) => apps::do_delete_app(config, client, args.subcommand()).await,
                    _ => unreachable!()
                }
            },
            Some(("secrets", sub_matches)) => {
                let apps_command = sub_matches.subcommand();

                match apps_command {
                    Some(("list", args)) => secrets::do_list_secrets(config, client, args).await,
                    Some(("create", args)) => secrets::do_create_secret(config, client, args).await,
                    Some(("delete", args)) => secrets::do_delete_secret(config, client, args.subcommand()).await,
                    _ => unreachable!()
                }
            },
            Some(("deploy", args)) => {
                deploy::do_deploy(config, client, args).await
            },
            Some(("run", args)) => {
                run::do_run(config, client, args, args.subcommand()).await
            }
            _ => unreachable!()
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
        .subcommand_required(true)
        .arg_required_else_help(true)
        .allow_external_subcommands(true)
        .subcommand(session::login_cmd())
        .subcommand(apps::apps_cmd())
        .subcommand(secrets::secrets_cmd())
        .subcommand(deploy::deploy_cmd())
        .subcommand(run::run_cmd())
        .subcommand(version::version_cmd())
}
