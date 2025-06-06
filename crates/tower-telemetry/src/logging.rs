#[macro_export]
macro_rules! event_with_level {
    // With context
    ($level:expr, ctx: $ctx:expr, $fmt:expr, $($arg:tt)+) => {
        if let Some(runid) = &$ctx.runid {
            $crate::tracing::event!($level, runid = %runid, "{}", format!($fmt, $($arg)+))
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
        $crate::event_with_level!($crate::tracing::Level::INFO, $ctx, $fmt, $($arg)*)
    };

    // With context, just message
    (ctx: $ctx:expr, $msg:expr) => {
        $crate::event_with_level!($crate::tracing::Level::INFO, $ctx, "{}", $msg)
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
        $crate::event_with_level!($crate::tracing::Level::WARN, $ctx, $fmt, $($arg)*)
    };

    // With context, just message
    (ctx: $ctx:expr, $msg:expr) => {
        $crate::event_with_level!($crate::tracing::Level::WARN, $ctx, "{}", $msg)
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
        $crate::event_with_level!($crate::tracing::Level::ERROR, $ctx, $fmt, $($arg)*)
    };

    // With context, just message
    (ctx: $ctx:expr, $msg:expr) => {
        $crate::event_with_level!($crate::tracing::Level::ERROR, $ctx, "{}", $msg)
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


