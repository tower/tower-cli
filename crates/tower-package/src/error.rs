use snafu::prelude::*;

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
        log::debug!("IO error: {}", err);
        Error::NoManifest
    }
}

impl From<serde_json::Error> for Error {
    fn from(err: serde_json::Error) -> Self {
        log::debug!("JSON error: {}", err);
        Error::InvalidManifest
    }
}
