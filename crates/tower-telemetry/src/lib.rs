pub mod logging;
pub mod context;

pub use context::Context;

/// reexport tracing to make sure that it gets included everywhere.
pub use tracing;
use tracing_subscriber;

pub enum LogLevel {
    Debug,
    Info,
    Warn,
    Error,
}

impl Into<tracing_subscriber::filter::LevelFilter> for LogLevel {
    fn into(self) -> tracing_subscriber::filter::LevelFilter {
        match self {
            LogLevel::Debug => tracing_subscriber::filter::LevelFilter::DEBUG,
            LogLevel::Info => tracing_subscriber::filter::LevelFilter::INFO,
            LogLevel::Warn => tracing_subscriber::filter::LevelFilter::WARN,
            LogLevel::Error => tracing_subscriber::filter::LevelFilter::ERROR,
        }
    }
}

pub fn enable_logging(level: LogLevel) {
    tracing_subscriber::fmt()
        .with_max_level(level)
        .init();
}
