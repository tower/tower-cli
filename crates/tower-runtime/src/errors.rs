use snafu::prelude::*;

#[derive(Clone, Debug, PartialEq, Eq, Snafu)]
pub enum Error {
    #[snafu(display("failed to RPC server"))]
    RuntimeStartFailed,

    #[snafu(display("spawning process: {detail}"))]
    SpawnFailed { detail: String },

    #[snafu(display("no app running"))]
    NoRunningApp,

    #[snafu(display("missing app manifest"))]
    MissingManifest,

    #[snafu(display("not implemented"))]
    NotImplemented,

    #[snafu(display("package download failed"))]
    PackageDownloadFailed,

    #[snafu(display("package create failed"))]
    PackageCreateFailed,

    #[snafu(display("package unpack failed: {detail}"))]
    PackageUnpackFailed { detail: String },

    #[snafu(display("container already initialized"))]
    AlreadyInitialized,

    #[snafu(display("pipe opening failed"))]
    PipeOpeningFailed,

    #[snafu(display("failed to terminate child process"))]
    TerminateFailed,

    #[snafu(display("timeout"))]
    Timeout,

    #[snafu(display("retry"))]
    Retry,

    #[snafu(display("request failed"))]
    RequestFailed,

    #[snafu(display("pip could not be found"))]
    MissingPip,

    #[snafu(display("python could not be found"))]
    MissingPython,

    #[snafu(display("bash could not be found"))]
    MissingBash,

    #[snafu(display("failed to create a virtual environment"))]
    VirtualEnvCreationFailed,

    #[snafu(display("waiter channel closed unexpectedly when polled"))]
    WaiterClosed,

    #[snafu(display("running Tower apps on this platform is not supported"))]
    UnsupportedPlatform,

    #[snafu(display("cancelled"))]
    Cancelled,

    #[snafu(display("app not started"))]
    AppNotStarted,

    #[snafu(display("no execution handle"))]
    NoHandle,

    #[snafu(display("invalid package"))]
    InvalidPackage,

    #[snafu(display("dependency installation failed"))]
    DependencyInstallationFailed,
}

impl From<std::io::Error> for Error {
    fn from(err: std::io::Error) -> Self {
        Error::SpawnFailed {
            detail: err.to_string(),
        }
    }
}

impl From<std::env::JoinPathsError> for Error {
    fn from(_: std::env::JoinPathsError) -> Self {
        Error::UnsupportedPlatform
    }
}

impl From<tower_uv::Error> for Error {
    fn from(err: tower_uv::Error) -> Self {
        match err {
            tower_uv::Error::UnsupportedPlatform => Error::UnsupportedPlatform,
            other => Error::SpawnFailed {
                detail: other.to_string(),
            },
        }
    }
}

impl From<tower_package::Error> for Error {
    fn from(err: tower_package::Error) -> Self {
        Error::PackageUnpackFailed {
            detail: err.to_string(),
        }
    }
}
