pub mod logging;
pub mod context;

pub use context::Context;

/// reexport tracing to make sure that it gets included everywhere.
pub use tracing;
use tracing_subscriber::prelude::*;
use tracing_subscriber::{registry::Registry, layer::Layer, fmt, EnvFilter};

/// LogLevel describes the various log levels that can be used in the application.
pub enum LogLevel {
    Debug,
    Info,
    Warn,
    Error,
}

impl AsRef<str> for LogLevel {
    fn as_ref(&self) -> &str {
        match self {
            LogLevel::Debug => "debug",
            LogLevel::Info => "info",
            LogLevel::Warn => "warn",
            LogLevel::Error => "error",
        }
    }
}

pub enum LogDestination {
    Stdout,
    File(String),
}

pub enum LogFormat {
    Plain,
    Json,
}

type BoxedFmtLayer = Box<dyn Layer<Registry> + Send + Sync>;

fn create_fmt_layer(format: LogFormat, destination: LogDestination) -> BoxedFmtLayer {
    match destination {
        LogDestination::Stdout => {
            match format {
                LogFormat::Plain => Box::new(fmt::layer().event_format(fmt::format().pretty())),
                LogFormat::Json => Box::new(fmt::layer().event_format(fmt::format().json())),
            }
        }
        LogDestination::File(path) => {
            let file_appender = tracing_appender::rolling::daily(".", path);
            match format {
                LogFormat::Plain => {
                    Box::new(
                        fmt::layer()
                            .event_format(fmt::format().pretty())
                            .with_writer(file_appender)
                    )
                }
                LogFormat::Json => {
                    Box::new(
                        fmt::layer()
                            .event_format(fmt::format().json())
                            .with_writer(file_appender)
                    )
                }
            }
        }
    }
}

pub fn enable_logging(level: LogLevel, format: LogFormat, destination: LogDestination) {
    let fmt_layer = create_fmt_layer(format, destination);
    let filter = EnvFilter::new(level);
    let subscriber = tracing_subscriber::registry().with(fmt_layer).with(filter);

    tracing::subscriber::set_global_default(subscriber)
        .expect("Failed to set global default subscriber");
}
