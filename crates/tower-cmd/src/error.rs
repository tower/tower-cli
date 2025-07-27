use snafu::prelude::*;
use tower_telemetry::debug;

#[derive(Debug, Snafu)]
pub enum Error {
    #[snafu(display("fetching catalogs failed"))]
    FetchingCatalogsFailed,

    #[snafu(display("fetching secrets failed"))]
    FetchingSecretsFailed,

    #[snafu(display("cryptography error"))]
    CryptographyError,
}

impl From<crypto::Error> for Error {
    fn from(err: crypto::Error) -> Self {
        debug!("cryptography error: {:?}", err);
        Self::CryptographyError
    }
}
