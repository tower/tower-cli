use snafu::prelude::*;

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
        log::debug!("error parsing Towerfile TOMl: {}", err);
        println!("error parsing Towerfile TOML: {}", err);
        Error::InvalidTowerfile
    }
}
