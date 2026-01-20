//! Execution backend abstraction for Tower
//!
//! This module provides traits and types for abstracting execution backends,
//! allowing Tower to support multiple compute substrates (local processes,
//! Kubernetes pods, etc.) through a uniform interface.

use async_trait::async_trait;
use std::collections::HashMap;
use std::path::PathBuf;
use tokio::io::AsyncRead;

use crate::errors::Error;
use crate::{OutputReceiver, Status};

// ============================================================================
// Core Execution Types
// ============================================================================

/// ExecutionSpec describes what to execute and how
pub struct ExecutionSpec {
    /// Unique identifier for this execution (e.g., run_id)
    pub id: String,

    /// Package as a stream of tar.gz data
    pub package_stream: Box<dyn AsyncRead + Send + Unpin>,

    /// Runtime configuration (image, version, etc.)
    pub runtime: RuntimeConfig,

    /// Environment name (e.g., "production", "staging", "default")
    pub environment: String,

    /// Secret key-value pairs to inject
    pub secrets: HashMap<String, String>,

    /// Parameter key-value pairs to inject
    pub parameters: HashMap<String, String>,

    /// Additional environment variables
    pub env_vars: HashMap<String, String>,

    /// Resource limits for execution
    pub resources: ResourceLimits,

    /// Networking configuration (for service workloads)
    pub networking: Option<NetworkingSpec>,

    /// Telemetry context for tracing
    pub telemetry_ctx: tower_telemetry::Context,
}

/// RuntimeConfig specifies the execution runtime environment
#[derive(Debug, Clone)]
pub struct RuntimeConfig {
    /// Runtime image to use (e.g., "towerhq/tower-runtime:python-3.11")
    pub image: String,

    /// Specific version/tag if applicable
    pub version: Option<String>,

    /// Cache configuration
    pub cache: CacheConfig,

    /// Entrypoint override (if not using bundle's default)
    pub entrypoint: Option<Vec<String>>,

    /// Command override (if not using bundle's default)
    pub command: Option<Vec<String>>,
}

/// CacheConfig describes what should be cached
#[derive(Debug, Clone)]
pub struct CacheConfig {
    /// Enable bundle caching (content-addressable by checksum)
    pub enable_bundle_cache: bool,

    /// Enable runtime layer caching (container image layers)
    pub enable_runtime_cache: bool,

    /// Enable dependency caching (language-specific, e.g., pip cache, node_modules)
    pub enable_dependency_cache: bool,

    /// Cache backend to use
    pub backend: CacheBackend,

    /// Cache isolation strategy
    pub isolation: CacheIsolation,
}

/// CacheIsolation defines security boundaries for caches
#[derive(Debug, Clone)]
pub enum CacheIsolation {
    /// Global sharing (safe for immutable content-addressable caches)
    Global,

    /// Per-account isolation
    PerAccount { account_id: String },

    /// Per-app isolation
    PerApp { app_id: String },

    /// No isolation
    None,
}

/// CacheBackend describes where caches are stored
#[derive(Debug, Clone)]
pub enum CacheBackend {
    /// Local filesystem cache
    Local { cache_dir: PathBuf },

    /// No caching
    None,
}

/// ResourceLimits defines compute resource constraints
#[derive(Debug, Clone)]
pub struct ResourceLimits {
    /// CPU limit in millicores (e.g., 1000 = 1 CPU)
    pub cpu_millicores: Option<u32>,

    /// Memory limit in megabytes
    pub memory_mb: Option<u32>,

    /// Ephemeral storage limit in megabytes
    pub storage_mb: Option<u32>,

    /// Maximum number of processes
    pub max_pids: Option<u32>,

    /// GPU count
    pub gpu_count: u32,

    /// Execution timeout in seconds
    pub timeout_seconds: u32,
}

/// NetworkingSpec defines networking requirements
#[derive(Debug, Clone)]
pub struct NetworkingSpec {
    /// Port the app listens on
    pub port: u16,

    /// Whether this app needs a stable service endpoint
    pub expose_service: bool,

    /// Service name (for DNS)
    pub service_name: Option<String>,
}

// ============================================================================
// Execution Backend Trait
// ============================================================================

/// ExecutionBackend abstracts the compute substrate
#[async_trait]
pub trait ExecutionBackend: Send + Sync {
    /// The handle type this backend returns
    type Handle: ExecutionHandle;

    /// Create a new execution environment
    async fn create(&self, spec: ExecutionSpec) -> Result<Self::Handle, Error>;

    /// Get backend capabilities
    fn capabilities(&self) -> BackendCapabilities;

    /// Cleanup backend resources
    async fn cleanup(&self) -> Result<(), Error>;
}

/// BackendCapabilities describes what a backend supports
#[derive(Debug, Clone)]
pub struct BackendCapabilities {
    /// Backend name
    pub name: String,

    /// Supports persistent volumes for caching
    pub supports_persistent_cache: bool,

    /// Supports pre-warmed environments
    pub supports_prewarming: bool,

    /// Supports network isolation
    pub supports_network_isolation: bool,

    /// Supports service endpoints
    pub supports_service_endpoints: bool,

    /// Typical startup latency in milliseconds
    pub typical_cold_start_ms: u64,
    pub typical_warm_start_ms: u64,

    /// Maximum concurrent executions
    pub max_concurrent_executions: Option<u32>,
}

// ============================================================================
// Execution Handle Trait
// ============================================================================

/// ExecutionHandle represents a running execution
#[async_trait]
pub trait ExecutionHandle: Send + Sync {
    /// Get a unique identifier for this execution
    fn id(&self) -> &str;

    /// Get current execution status
    async fn status(&self) -> Result<Status, Error>;

    /// Subscribe to log stream
    async fn logs(&self) -> Result<OutputReceiver, Error>;

    /// Terminate execution gracefully
    async fn terminate(&mut self) -> Result<(), Error>;

    /// Force kill execution
    async fn kill(&mut self) -> Result<(), Error>;

    /// Wait for execution to complete
    async fn wait_for_completion(&self) -> Result<Status, Error>;

    /// Get service endpoint
    async fn service_endpoint(&self) -> Result<Option<ServiceEndpoint>, Error>;

    /// Cleanup resources
    async fn cleanup(&mut self) -> Result<(), Error>;
}

/// ServiceEndpoint describes how to reach a running service
#[derive(Debug, Clone)]
pub struct ServiceEndpoint {
    /// Host/IP to connect to
    pub host: String,

    /// Port to connect to
    pub port: u16,

    /// Protocol (http, https, tcp, etc.)
    pub protocol: String,

    /// Full URL if applicable (e.g., "http://app-run-123.default.svc.cluster.local:8080")
    pub url: Option<String>,
}
