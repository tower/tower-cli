use snafu::prelude::*;
use tower_telemetry::debug;

#[derive(Debug, Snafu)]
pub enum Error {
    #[snafu(display("No manifest found"))]
    NoManifest,

    #[snafu(display("Invalid manifest"))]
    InvalidManifest,

    #[snafu(display("Invalid path"))]
    InvalidPath,

    #[snafu(display("Invalid glob pattern: {message}"))]
    InvalidGlob { message: String },

    #[snafu(display("Invalid Towerfile: {message}"))]
    InvalidTowerfile { message: String },

    #[snafu(display("No Towerfile was found in this directory"))]
    MissingTowerfile,

    #[snafu(display("Missing required app field `{field}` in Towerfile"))]
    MissingRequiredAppField { field: String },

    #[snafu(display("IO error: {source}"))]
    Io { source: std::io::Error },
}

impl From<std::io::Error> for Error {
    fn from(err: std::io::Error) -> Self {
        debug!("IO error: {}", err);
        Error::NoManifest
    }
}

impl From<serde_json::Error> for Error {
    fn from(err: serde_json::Error) -> Self {
        debug!("JSON error: {}", err);
        Error::InvalidManifest
    }
}

impl From<crate::core::Error> for Error {
    fn from(err: crate::core::Error) -> Self {
        use crate::core::Error as Core;
        match err {
            Core::InvalidPath => Error::InvalidPath,
            Core::Serialization { source } => {
                debug!("core serialization error: {}", source);
                Error::InvalidManifest
            }
            Core::Io { source } => {
                debug!("core IO error: {}", source);
                Error::NoManifest
            }
            Core::InvalidTowerfile { message } => Error::InvalidTowerfile { message },
            Core::MissingTowerfile => Error::MissingTowerfile,
            Core::MissingRequiredAppField { field } => Error::MissingRequiredAppField { field },
        }
    }
}
