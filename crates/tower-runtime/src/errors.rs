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
}
