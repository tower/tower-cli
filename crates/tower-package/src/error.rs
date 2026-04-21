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

impl From<tower_package_core::Error> for Error {
    fn from(err: tower_package_core::Error) -> Self {
        match err {
            tower_package_core::Error::InvalidPath => Error::InvalidPath,
            tower_package_core::Error::Serialization { source } => {
                debug!("core serialization error: {}", source);
                Error::InvalidManifest
            }
            tower_package_core::Error::Io { source } => {
                debug!("core IO error: {}", source);
                Error::NoManifest
            }
        }
    }
}
