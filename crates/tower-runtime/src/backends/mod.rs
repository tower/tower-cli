//! Concrete implementations of ExecutionBackend for different compute substrates

pub mod subprocess;

pub mod k8s;

/// Simple backend for CLI --local runs
pub mod cli;
