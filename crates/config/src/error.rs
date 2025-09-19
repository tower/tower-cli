use snafu::prelude::*;
use tower_telemetry::debug;

#[derive(Debug, Snafu)]
pub enum Error {
    #[snafu(display("Config directory not found"))]
    ConfigDirNotFound,

    #[snafu(display("No home directory found"))]
    NoHomeDir,

    #[snafu(display("No session file found"))]
    NoSession,

    #[snafu(display("Invalid Towerfile"))]
    InvalidTowerfile,

    #[snafu(display("No Towerfile was found in this directory"))]
    MissingTowerfile,

    #[snafu(display("Missing required app field `{}` in Towerfile", field))]
    MissingRequiredAppField { field: String },

    #[snafu(display("Team with name {} not found!", team_name))]
    TeamNotFound { team_name: String },

    #[snafu(display("Unknown describe session value: {}", value))]
    UnknownDescribeSessionValue { value: serde_json::Value },

    DescribeSessionError {
        err: tower_api::apis::Error<tower_api::apis::default_api::DescribeSessionError>,
    },
}

impl From<std::io::Error> for Error {
    fn from(_: std::io::Error) -> Self {
        Error::ConfigDirNotFound
    }
}

impl From<serde_json::Error> for Error {
    fn from(_: serde_json::Error) -> Self {
        Error::NoSession
    }
}

impl From<toml::de::Error> for Error {
    fn from(err: toml::de::Error) -> Self {
        debug!("error parsing Towerfile TOMl: {}", err);
        Error::InvalidTowerfile
    }
}

impl From<toml::ser::Error> for Error {
    fn from(err: toml::ser::Error) -> Self {
        debug!("error serializing Towerfile TOML: {}", err);
        Error::InvalidTowerfile
    }
}
