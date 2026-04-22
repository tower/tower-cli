use snafu::prelude::*;

#[derive(Debug, Snafu)]
pub enum Error {
    #[snafu(display("Config directory not found"))]
    ConfigDirNotFound,

    #[snafu(display("No home directory found"))]
    NoHomeDir,

    #[snafu(display("IO error: {}", source))]
    Io { source: std::io::Error },

    #[snafu(display("No session file found"))]
    NoSession,

    #[snafu(display("Team with name {} not found!", team_name))]
    TeamNotFound { team_name: String },

    #[snafu(display("Unknown describe session value: {}", value))]
    UnknownDescribeSessionValue { value: serde_json::Value },

    DescribeSessionError {
        err: tower_api::apis::Error<tower_api::apis::default_api::DescribeSessionError>,
    },
}

impl From<std::io::Error> for Error {
    fn from(source: std::io::Error) -> Self {
        Error::Io { source }
    }
}

impl From<serde_json::Error> for Error {
    fn from(_: serde_json::Error) -> Self {
        Error::NoSession
    }
}
