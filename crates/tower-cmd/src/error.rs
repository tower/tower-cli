use snafu::prelude::*;
use tower_api::apis::default_api::{
    DeployAppError, DescribeAppError, DescribeRunError, RunAppError,
};
use tower_telemetry::debug;

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

    // Session and authentication errors
    #[snafu(display("No session found. Please log in to Tower first."))]
    NoSession,

    // Run-related errors
    #[snafu(display("Failed to stream run logs"))]
    LogStreamFailed,

    #[snafu(display("Run failed with error status"))]
    RunFailed,

    #[snafu(display("Run crashed"))]
    RunCrashed,

    #[snafu(display("Run was cancelled"))]
    RunCancelled,

    #[snafu(display("App crashed during local execution"))]
    AppCrashed,

    #[snafu(display("API error occurred"))]
    ApiError,

    #[snafu(display("Failed to load Towerfile from {}: {}", path, source))]
    TowerfileLoadFailed { path: String, source: config::Error },

    // Towerfile generation errors
    #[snafu(display("pyproject.toml not found at {}", path))]
    PyprojectNotFound { path: String },

    #[snafu(display("Failed to parse pyproject.toml: {}", source))]
    InvalidPyproject { source: toml::de::Error },

    #[snafu(display("No [project] section found in pyproject.toml"))]
    MissingProjectSection,

    // File I/O errors
    #[snafu(display("File I/O error: {}", source))]
    IoError { source: std::io::Error },

    // Serialization errors
    #[snafu(display("Serialization error: {}", source))]
    SerializationError { source: toml::ser::Error },

    // Address parsing error
    #[snafu(display("Invalid address: {}", source))]
    AddressParseError { source: std::net::AddrParseError },

    // Runtime errors
    #[snafu(display("Runtime error: {}", source))]
    RuntimeError {
        source: tower_runtime::errors::Error,
    },

    // Package errors
    #[snafu(display("Package error: {}", source))]
    PackageError { source: tower_package::Error },

    // API run error
    #[snafu(display("API run error: {}", source))]
    ApiRunError {
        source: tower_api::apis::Error<RunAppError>,
    },

    // API deploy error
    #[snafu(display("API deploy error: {}", source))]
    ApiDeployError {
        source: tower_api::apis::Error<DeployAppError>,
    },

    // API describe app error
    #[snafu(display("API describe app error: {}", source))]
    ApiDescribeAppError {
        source: tower_api::apis::Error<DescribeAppError>,
    },

    // Channel error
    #[snafu(display("Channel receive error"))]
    ChannelReceiveError,
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

impl From<std::io::Error> for Error {
    fn from(source: std::io::Error) -> Self {
        Self::IoError { source }
    }
}

impl From<toml::de::Error> for Error {
    fn from(source: toml::de::Error) -> Self {
        Self::InvalidPyproject { source }
    }
}

impl From<toml::ser::Error> for Error {
    fn from(source: toml::ser::Error) -> Self {
        Self::SerializationError { source }
    }
}

impl From<config::Error> for Error {
    fn from(source: config::Error) -> Self {
        Self::TowerfileLoadFailed {
            path: "unknown".to_string(),
            source,
        }
    }
}

impl From<std::net::AddrParseError> for Error {
    fn from(source: std::net::AddrParseError) -> Self {
        Self::AddressParseError { source }
    }
}

impl From<tower_runtime::errors::Error> for Error {
    fn from(source: tower_runtime::errors::Error) -> Self {
        Self::RuntimeError { source }
    }
}

impl From<tower_package::Error> for Error {
    fn from(source: tower_package::Error) -> Self {
        Self::PackageError { source }
    }
}

impl From<tower_api::apis::Error<RunAppError>> for Error {
    fn from(source: tower_api::apis::Error<RunAppError>) -> Self {
        Self::ApiRunError { source }
    }
}

impl From<tower_api::apis::Error<DeployAppError>> for Error {
    fn from(source: tower_api::apis::Error<DeployAppError>) -> Self {
        Self::ApiDeployError { source }
    }
}

impl From<tower_api::apis::Error<DescribeAppError>> for Error {
    fn from(source: tower_api::apis::Error<DescribeAppError>) -> Self {
        Self::ApiDescribeAppError { source }
    }
}

impl From<tokio::sync::oneshot::error::RecvError> for Error {
    fn from(_: tokio::sync::oneshot::error::RecvError) -> Self {
        Self::ChannelReceiveError
    }
}
