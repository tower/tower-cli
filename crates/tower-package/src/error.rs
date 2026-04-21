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
        }
    }
}
