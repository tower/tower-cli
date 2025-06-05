use tracing::event;

macro_rules! debug {
    // Handle case with context, format string and arguments
    ($ctx:expr, $fmt:expr, $($arg:tt)*) => {
        if let Some(run_id) = $ctx.run_id {
            event!(tracing::Level::DEBUG, runid = %run_id, "{}", format!($fmt, $($arg)*));
        } else {
            event!(tracing::Level::DEBUG, "{}", format!($fmt, $($arg)*));
        }
    };
    // Handle case with context and just a message (no formatting)
    ($ctx:expr, $msg:expr) => {
        if let Some(run_id) = $ctx.run_id {
            event!(tracing::Level::DEBUG, runid = %run_id, $msg);
        } else {
            event!(tracing::Level::DEBUG, "{}", $msg);
        }
    };
}

macro_rules! info {
    // Handle case with context, format string and arguments
    ($ctx:expr, $fmt:expr, $($arg:tt)*) => {
        if let Some(run_id) = $ctx.run_id {
            event!(tracing::Level::INFO, runid = %run_id, "{}", format!($fmt, $($arg)*));
        } else {
            event!(tracing::Level::INFO, "{}", format!($fmt, $($arg)*));
        }
    };
    // Handle case with context and just a message (no formatting)
    ($ctx:expr, $msg:expr) => {
        if let Some(run_id) = $ctx.run_id {
            event!(tracing::Level::INFO, runid = %run_id, $msg);
        } else {
            event!(tracing::Level::INFO, "{}", $msg);
        }
    };
}

macro_rules! warn {
    // Handle case with context, format string and arguments
    ($ctx:expr, $fmt:expr, $($arg:tt)*) => {
        if let Some(run_id) = $ctx.run_id {
            event!(tracing::Level::WARN, runid = %run_id, "{}", format!($fmt, $($arg)*));
        } else {
            event!(tracing::Level::WARN, "{}", format!($fmt, $($arg)*));
        }
    };
    // Handle case with context and just a message (no formatting)
    ($ctx:expr, $msg:expr) => {
        if let Some(run_id) = $ctx.run_id {
            event!(tracing::Level::WARN, runid = %run_id, $msg);
        } else {
            event!(tracing::Level::WARN, "{}", $msg);
        }
    };
}

macro_rules! error {
    // Handle case with context, format string and arguments
    ($ctx:expr, $fmt:expr, $($arg:tt)*) => {
        if let Some(run_id) = $ctx.run_id {
            event!(tracing::Level::ERROR, runid = %run_id, "{}", format!($fmt, $($arg)*));
        } else {
            event!(tracing::Level::ERROR, "{}", format!($fmt, $($arg)*));
        }
    };
    // Handle case with context and just a message (no formatting)
    ($ctx:expr, $msg:expr) => {
        if let Some(run_id) = $ctx.run_id {
            event!(tracing::Level::ERROR, runid = %run_id, $msg);
        } else {
            event!(tracing::Level::ERROR, "{}", $msg);
        }
    };
}
