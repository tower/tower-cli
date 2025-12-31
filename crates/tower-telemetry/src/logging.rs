use std::io::IsTerminal;
use tracing_subscriber::prelude::*;
use tracing_subscriber::{filter::EnvFilter, fmt, layer::Layer, registry::Registry};

#[macro_export]
macro_rules! event_with_level {
    // With context
    ($level:expr, ctx: $ctx:expr, $fmt:expr, $($arg:tt)+) => {
        if let Some(runid) = &$ctx.runid {
            $crate::tracing::event!($level, "tower.runid" = %runid, "{}", format!($fmt, $($arg)+))
        } else {
            $crate::tracing::event!($level, "{}", format!($fmt, $($arg)+))
        }
    };

    // Without context
    ($level:expr, $fmt:expr, $($arg:tt)*) => {
        $crate::tracing::event!($level, "{}", format!($fmt, $($arg)*))
    };
}

#[macro_export]
macro_rules! trace {
    // With context, format string and arguments
    (ctx: $ctx:expr, $fmt:expr, $($arg:tt)+) => {
        $crate::event_with_level!($crate::tracing::Level::TRACE, ctx: $ctx, $fmt, $($arg)+)
    };

    // With context, just message
    (ctx: $ctx:expr, $msg:expr) => {
        $crate::event_with_level!($crate::tracing::Level::TRACE, ctx: $ctx, "{}", $msg)
    };

    // Without context, format string and arguments
    ($fmt:expr, $($arg:tt)*) => {
        $crate::event_with_level!($crate::tracing::Level::TRACE, $fmt, $($arg)*)
    };

    // Without context, just message
    ($msg:expr) => {
        $crate::event_with_level!($crate::tracing::Level::TRACE, "{}", $msg)
    };
}

#[macro_export]
macro_rules! debug {
    // With context, format string and arguments
    (ctx: $ctx:expr, $fmt:expr, $($arg:tt)+) => {
        $crate::event_with_level!($crate::tracing::Level::DEBUG, ctx: $ctx, $fmt, $($arg)+)
    };

    // With context, just message
    (ctx: $ctx:expr, $msg:expr) => {
        $crate::event_with_level!($crate::tracing::Level::DEBUG, ctx: $ctx, "{}", $msg)
    };

    // Without context, format string and arguments
    ($fmt:expr, $($arg:tt)*) => {
        $crate::event_with_level!($crate::tracing::Level::DEBUG, $fmt, $($arg)*)
    };

    // Without context, just message
    ($msg:expr) => {
        $crate::event_with_level!($crate::tracing::Level::DEBUG, "{}", $msg)
    };
}

#[macro_export]
macro_rules! info {
    // With context, format string and arguments
    (ctx: $ctx:expr, $fmt:expr, $($arg:tt)*) => {
        $crate::event_with_level!($crate::tracing::Level::INFO, ctx: $ctx, $fmt, $($arg)*)
    };

    // With context, just message
    (ctx: $ctx:expr, $msg:expr) => {
        $crate::event_with_level!($crate::tracing::Level::INFO, ctx: $ctx, "{}", $msg)
    };

    // Without context, format string and arguments
    ($fmt:expr, $($arg:tt)*) => {
        $crate::event_with_level!($crate::tracing::Level::INFO, $fmt, $($arg)*)
    };

    // Without context, just message
    ($msg:expr) => {
        $crate::event_with_level!($crate::tracing::Level::INFO, "{}", $msg)
    };
}

#[macro_export]
macro_rules! warn {
    // With context, format string and arguments
    (ctx: $ctx:expr, $fmt:expr, $($arg:tt)*) => {
        $crate::event_with_level!($crate::tracing::Level::WARN, ctx: $ctx, $fmt, $($arg)*)
    };

    // With context, just message
    (ctx: $ctx:expr, $msg:expr) => {
        $crate::event_with_level!($crate::tracing::Level::WARN, ctx: $ctx, "{}", $msg)
    };

    // Without context, format string and arguments
    ($fmt:expr, $($arg:tt)*) => {
        $crate::event_with_level!($crate::tracing::Level::WARN, $fmt, $($arg)*)
    };

    // Without context, just message
    ($msg:expr) => {
        $crate::event_with_level!($crate::tracing::Level::WARN, "{}", $msg)
    };
}

#[macro_export]
macro_rules! error {
    // With context, format string and arguments
    (ctx: $ctx:expr, $fmt:expr, $($arg:tt)*) => {
        $crate::event_with_level!($crate::tracing::Level::ERROR, ctx: $ctx, $fmt, $($arg)*)
    };

    // With context, just message
    (ctx: $ctx:expr, $msg:expr) => {
        $crate::event_with_level!($crate::tracing::Level::ERROR, ctx: $ctx, "{}", $msg)
    };

    // Without context, format string and arguments
    ($fmt:expr, $($arg:tt)*) => {
        $crate::event_with_level!($crate::tracing::Level::ERROR, $fmt, $($arg)*)
    };

    // Without context, just message
    ($msg:expr) => {
        $crate::event_with_level!($crate::tracing::Level::ERROR, "{}", $msg)
    };
}

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

fn should_use_color(destination: &LogDestination) -> bool {
    match destination {
        LogDestination::Stdout => {
            // Check if stdout is a TTY
            std::io::stdout().is_terminal()
        }
        LogDestination::File(_) => {
            // Never use color for file output
            false
        }
    }
}

fn create_fmt_layer(format: LogFormat, destination: LogDestination) -> BoxedFmtLayer {
    let use_color = should_use_color(&destination);

    match destination {
        LogDestination::Stdout => match format {
            LogFormat::Plain => Box::new(
                fmt::layer().event_format(
                    fmt::format()
                        .pretty()
                        .with_target(false)
                        .with_file(false)
                        .with_line_number(false)
                        .with_ansi(use_color),
                ),
            ),
            LogFormat::Json => Box::new(
                fmt::layer().event_format(
                    fmt::format()
                        .json()
                        .with_target(false)
                        .with_file(false)
                        .with_line_number(false)
                        .with_ansi(use_color),
                ),
            ),
        },
        LogDestination::File(path) => {
            let file_appender = tracing_appender::rolling::daily(".", path);
            match format {
                LogFormat::Plain => Box::new(
                    fmt::layer()
                        .event_format(
                            fmt::format()
                                .pretty()
                                .with_target(false)
                                .with_file(false)
                                .with_line_number(false)
                                .with_ansi(use_color),
                        )
                        .with_writer(file_appender),
                ),
                LogFormat::Json => Box::new(
                    fmt::layer()
                        .event_format(
                            fmt::format()
                                .json()
                                .with_target(false)
                                .with_file(false)
                                .with_line_number(false)
                                .with_ansi(use_color),
                        )
                        .with_writer(file_appender),
                ),
            }
        }
    }
}

pub fn enable_logging(level: LogLevel, format: LogFormat, destination: LogDestination) {
    let filter = EnvFilter::new(level)
        .add_directive("h2=off".parse().unwrap())
        .add_directive("tower::buffer=off".parse().unwrap())
        .add_directive("hyper_util=off".parse().unwrap());

    let subscriber = tracing_subscriber::registry()
        .with(create_fmt_layer(format, destination))
        .with(filter);

    let _ = tracing::subscriber::set_global_default(subscriber);
}
