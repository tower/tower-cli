use clap::{Arg, Command, value_parser};
use config::{Config, Session};
use tower_api::Client;

mod apps;
mod session;
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

        // TODO: Should this be configured every time?
        simple_logger::SimpleLogger::new().env().init().unwrap();

        if config.debug {
            log::set_max_level(log::LevelFilter::Debug);
        } else {
            log::set_max_level(log::LevelFilter::Info);
        }

        match matches.subcommand() {
            Some(("login", _)) => session::do_login(config, client).await,
            Some(("apps", sub_matches)) => {
                let apps_command = sub_matches.subcommand();

                match apps_command {
                    Some(("list", _)) => apps::do_list_apps(config, client).await,
                    Some(("create", _)) => apps::do_create_app(config, client).await,
                    Some(("delete", _)) => apps::do_delete_app(config, client).await,
                    _ => unreachable!()
                }
            },
            _ => unreachable!()
        }
    }
}

fn root_cmd() -> Command {
    Command::new("tower")
        .about("Tower is a compute platform for modern data projects")
        .arg(
            Arg::new("debug")
                .long("debug")
                .action(clap::ArgAction::SetTrue)
        )
        .arg(
            Arg::new("tower_url")
                .long("tower-url")
                .value_parser(value_parser!(String))
                .action(clap::ArgAction::Set)
        )
        .subcommand_required(true)
        .arg_required_else_help(true)
        .allow_external_subcommands(true)
        .subcommand(apps::apps_cmd())
        .subcommand(session::login_cmd())
}
