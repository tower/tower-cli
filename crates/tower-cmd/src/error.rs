use snafu::prelude::*;
use tower_telemetry::debug;
use tower_api::apis::default_api::DescribeRunError;

#[derive(Debug, Snafu)]
pub enum Error {
    #[snafu(display("fetching catalogs failed"))]
    FetchingCatalogsFailed,

    #[snafu(display("fetching secrets failed"))]
    FetchingSecretsFailed,

    #[snafu(display("cryptography error"))]
    CryptographyError,

    #[snafu(display("run completed"))]
    RunCompleted,

    #[snafu(display("unknown error"))]
    UnknownError,
}

impl From<crypto::Error> for Error {
    fn from(err: crypto::Error) -> Self {
        debug!("cryptography error: {:?}", err);
        Self::CryptographyError
    }
}

impl From<tower_api::apis::Error<DescribeRunError>> for Error {
    fn from(err: tower_api::apis::Error<DescribeRunError>) -> Self {
        debug!("API error: {:?}", err);
        Self::UnknownError
    }
}
