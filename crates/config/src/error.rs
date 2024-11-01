use snafu::prelude::*;

#[derive(Debug, Snafu)]
pub enum Error {
    #[snafu(display("Config directory not found"))]
    ConfigDirNotFound,

    #[snafu(display("No home directory found"))]
    NoHomeDir,

    #[snafu(display("No session file found"))]
    NoSession,
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
