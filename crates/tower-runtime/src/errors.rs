use snafu::prelude::*;

#[derive(Debug, Snafu)]
pub enum Error {
    #[snafu(display("failed to RPC server"))]
    RuntimeStartFailed,

    #[snafu(display("spawning process"))]
    SpawnFailed,

    #[snafu(display("no app running"))]
    NoRunningApp,

    #[snafu(display("missing app manifest"))]
    MissingManifest,

    #[snafu(display("not implemented"))]
    NotImplemented,

    #[snafu(display("bundle download failed"))]
    BundleDownloadFailed,

    #[snafu(display("bundle create failed"))]
    BundleCreateFailed,

    #[snafu(display("bundle unpack failed"))]
    BundleUnpackFailed,

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
}

impl From<std::io::Error> for Error {
    fn from(_: std::io::Error) -> Self {
        Error::SpawnFailed
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
            tower_uv::Error::IoError(_) => Error::SpawnFailed,
            tower_uv::Error::NotFound(_) => Error::SpawnFailed,
            tower_uv::Error::PermissionDenied(_) => Error::SpawnFailed,
            tower_uv::Error::Other(_) => Error::SpawnFailed,
            tower_uv::Error::MissingPyprojectToml => Error::SpawnFailed,
            tower_uv::Error::InvalidUv => Error::SpawnFailed,
            tower_uv::Error::UnsupportedPlatform => Error::UnsupportedPlatform,
        }
    }
}
