//! Concrete implementations of ExecutionBackend for different compute substrates

pub mod local;

#[cfg(feature = "k8s")]
pub mod k8s;
