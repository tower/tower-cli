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
