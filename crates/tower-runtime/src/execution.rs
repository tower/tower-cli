//! Execution backend abstraction for Tower
//!
//! This module provides traits and types for abstracting execution backends,
//! allowing Tower to support multiple compute substrates (local processes,
//! Kubernetes pods, etc.) through a uniform interface.

use async_trait::async_trait;
use chrono::{DateTime, Utc};
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::mpsc::UnboundedReceiver;

use crate::errors::Error;

// ============================================================================
// Core Execution Types
// ============================================================================

/// ExecutionSpec describes what to execute and how
#[derive(Debug, Clone)]
pub struct ExecutionSpec {
    /// Unique identifier for this execution (e.g., run_id)
    pub id: String,

    /// Bundle reference (how to get the application code)
    pub bundle: BundleRef,

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

/// BundleRef describes where to get the application bundle
#[derive(Debug, Clone)]
pub enum BundleRef {
    /// Local filesystem path (for local execution)
    Local { path: PathBuf },

    /// Remote bundle to be downloaded
    Remote {
        bundle_id: String,
        checksum: String,
        download_url: String,
    },

    /// Container image reference
    ContainerImage {
        registry: String,
        repository: String,
        tag: String,
        digest: Option<String>,
    },
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

    /// Kubernetes PersistentVolume
    K8sPersistentVolume { pv_claim_name: String },

    /// S3-based cache
    S3 { bucket: String, prefix: String },

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
    /// Get unique identifier for this execution
    fn id(&self) -> &str;

    /// Get current execution status
    async fn status(&self) -> Result<ExecutionStatus, Error>;

    /// Subscribe to log stream
    async fn logs(&self) -> Result<LogReceiver, Error>;

    /// Terminate execution gracefully
    async fn terminate(&mut self) -> Result<(), Error>;

    /// Force kill execution
    async fn kill(&mut self) -> Result<(), Error>;

    /// Wait for execution to complete
    async fn wait_for_completion(&self) -> Result<ExecutionStatus, Error>;

    /// Get service endpoint
    async fn service_endpoint(&self) -> Result<Option<ServiceEndpoint>, Error>;

    /// Cleanup resources
    async fn cleanup(&mut self) -> Result<(), Error>;
}

/// ExecutionStatus represents the current state of an execution
#[derive(Debug, Clone, PartialEq)]
pub enum ExecutionStatus {
    /// Execution is being prepared (downloading bundle, setting up environment)
    Preparing,

    /// Execution is currently running
    Running,

    /// Execution completed successfully (exit code 0)
    Succeeded,

    /// Execution failed with non-zero exit code
    Failed { exit_code: i32 },

    /// Execution crashed (segfault, OOM kill, etc.)
    Crashed { reason: String },

    /// Execution was terminated by user/system
    Terminated,

    /// Unknown status (shouldn't happen in normal operation)
    Unknown,
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

// ============================================================================
// Log Streaming Types
// ============================================================================

/// LogReceiver is a stream of log lines from the execution
pub type LogReceiver = UnboundedReceiver<LogLine>;

/// LogLine represents a single line of output
#[derive(Debug, Clone)]
pub struct LogLine {
    /// When this line was emitted
    pub timestamp: DateTime<Utc>,

    /// Which stream (stdout/stderr)
    pub stream: LogStream,

    /// Which phase (setup vs program)
    pub channel: LogChannel,

    /// The actual log content
    pub content: String,
}

/// LogStream identifies stdout vs stderr
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LogStream {
    Stdout,
    Stderr,
}

/// LogChannel identifies setup vs program output
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LogChannel {
    /// Setup phase (dependency installation, environment prep)
    Setup,

    /// Program phase (actual application output)
    Program,
}

// ============================================================================
// App Trait Integration
// ============================================================================

/// App trait provides high-level lifecycle management
#[async_trait]
pub trait App: Send + Sync {
    /// The backend type this App uses
    type Backend: ExecutionBackend;

    /// Start a new execution
    async fn start(backend: Arc<Self::Backend>, opts: StartOptions) -> Result<Self, Error>
    where
        Self: Sized;

    /// Get current execution status
    async fn status(&self) -> Result<ExecutionStatus, Error>;

    /// Terminate execution
    async fn terminate(&mut self) -> Result<(), Error>;

    /// Get service endpoint
    async fn service_endpoint(&self) -> Result<Option<ServiceEndpoint>, Error> {
        Ok(None)
    }
}

/// StartOptions contains all parameters needed to start an execution
pub struct StartOptions {
    pub ctx: tower_telemetry::Context,
    pub package: tower_package::Package,
    pub cwd: Option<PathBuf>,
    pub environment: String,
    pub secrets: HashMap<String, String>,
    pub parameters: HashMap<String, String>,
    pub env_vars: HashMap<String, String>,
    pub output_sender: tokio::sync::mpsc::UnboundedSender<crate::Output>,
    pub cache_dir: Option<PathBuf>,
}

/// AppLauncher orchestrates App lifecycle
pub struct AppLauncher<A: App> {
    backend: Arc<A::Backend>,
    app: Option<A>,
}

impl<A: App> AppLauncher<A> {
    /// Create a new launcher with the specified backend
    pub fn new(backend: Arc<A::Backend>) -> Self {
        Self { backend, app: None }
    }

    /// Launch an app with the given options
    pub async fn launch(&mut self, opts: StartOptions) -> Result<(), Error> {
        // Drop any existing app
        self.app = None;

        // Start new app using backend
        let app = A::start(self.backend.clone(), opts).await?;
        self.app = Some(app);

        Ok(())
    }

    /// Get current app status
    pub async fn status(&self) -> Result<ExecutionStatus, Error> {
        self.app
            .as_ref()
            .ok_or(Error::AppNotStarted)?
            .status()
            .await
    }

    /// Terminate the running app
    pub async fn terminate(&mut self) -> Result<(), Error> {
        if let Some(app) = &mut self.app {
            app.terminate().await?;
            self.app = None;
        }
        Ok(())
    }

    /// Get service endpoint (if app exposes one)
    pub async fn service_endpoint(&self) -> Result<Option<ServiceEndpoint>, Error> {
        match &self.app {
            Some(app) => app.service_endpoint().await,
            None => Ok(None),
        }
    }
}

/// ManagedApp implements App using ExecutionBackend
pub struct ManagedApp<B: ExecutionBackend> {
    backend: Arc<B>,
    handle: Option<B::Handle>,
    output_forwarder: Option<tokio::task::JoinHandle<()>>,
}

#[async_trait]
impl<B: ExecutionBackend> App for ManagedApp<B> {
    type Backend = B;

    async fn start(backend: Arc<B>, opts: StartOptions) -> Result<Self, Error> {
        // Extract output_sender before consuming opts
        let output_sender = opts.output_sender.clone();

        // Convert StartOptions to ExecutionSpec (consumes opts)
        let spec = convert_start_options_to_spec(opts)?;

        // Create execution using backend
        let handle = backend.create(spec).await?;

        // Start log forwarding
        let mut log_receiver = handle.logs().await?;
        let output_forwarder = tokio::spawn(async move {
            while let Some(log_line) = log_receiver.recv().await {
                // Convert LogLine to Output for existing code
                let _ = output_sender.send(crate::Output {
                    channel: match log_line.channel {
                        LogChannel::Setup => crate::Channel::Setup,
                        LogChannel::Program => crate::Channel::Program,
                    },
                    time: log_line.timestamp,
                    fd: match log_line.stream {
                        LogStream::Stdout => crate::FD::Stdout,
                        LogStream::Stderr => crate::FD::Stderr,
                    },
                    line: log_line.content,
                });
            }
        });

        Ok(Self {
            backend,
            handle: Some(handle),
            output_forwarder: Some(output_forwarder),
        })
    }

    async fn status(&self) -> Result<ExecutionStatus, Error> {
        self.handle.as_ref().ok_or(Error::NoHandle)?.status().await
    }

    async fn terminate(&mut self) -> Result<(), Error> {
        if let Some(mut handle) = self.handle.take() {
            handle.terminate().await?;
            handle.cleanup().await?;
        }

        // Stop log forwarding
        if let Some(forwarder) = self.output_forwarder.take() {
            forwarder.abort();
        }

        Ok(())
    }

    async fn service_endpoint(&self) -> Result<Option<ServiceEndpoint>, Error> {
        match &self.handle {
            Some(handle) => handle.service_endpoint().await,
            None => Ok(None),
        }
    }
}

/// Helper function to convert StartOptions to ExecutionSpec
fn convert_start_options_to_spec(opts: StartOptions) -> Result<ExecutionSpec, Error> {
    let package = opts.package;

    // Determine bundle reference from package
    let bundle = if let Some(path) = package.unpacked_path {
        BundleRef::Local { path }
    } else {
        // TODO: Handle remote bundles
        return Err(Error::InvalidPackage);
    };

    // Build runtime config from cache_dir
    let runtime = RuntimeConfig {
        image: "towerhq/tower-runtime:latest".to_string(), // TODO: Make configurable
        version: None,
        cache: CacheConfig {
            enable_bundle_cache: true,
            enable_runtime_cache: true,
            enable_dependency_cache: true,
            backend: match opts.cache_dir {
                Some(dir) => CacheBackend::Local { cache_dir: dir },
                None => CacheBackend::None,
            },
            isolation: CacheIsolation::None, // TODO: Get from context
        },
        entrypoint: None,
        command: None,
    };

    Ok(ExecutionSpec {
        id: uuid::Uuid::new_v4().to_string(), // TODO: Use actual run_id
        bundle,
        runtime,
        environment: opts.environment,
        secrets: opts.secrets,
        parameters: opts.parameters,
        env_vars: opts.env_vars,
        resources: ResourceLimits {
            cpu_millicores: None,
            memory_mb: None,
            storage_mb: None,
            max_pids: None,
            gpu_count: 0,
            timeout_seconds: 0, // No timeout by default
        },
        networking: None,
        telemetry_ctx: opts.ctx,
    })
}

// ============================================================================
// Cache Manager Trait
// ============================================================================

/// CacheManager abstracts caching across execution backends
#[async_trait]
pub trait CacheManager: Send + Sync {
    /// Get cached bundle
    async fn get_bundle(
        &self,
        bundle_id: &str,
        checksum: &str,
    ) -> Result<Option<CacheHandle>, Error>;

    /// Store bundle in cache
    async fn put_bundle(
        &self,
        bundle_id: &str,
        checksum: &str,
        source: CacheSource,
    ) -> Result<CacheHandle, Error>;

    /// Get cached runtime layer
    async fn get_runtime_layer(
        &self,
        image: &str,
        layer_digest: &str,
    ) -> Result<Option<CacheHandle>, Error>;

    /// Store runtime layer in cache
    async fn put_runtime_layer(
        &self,
        image: &str,
        layer_digest: &str,
        source: CacheSource,
    ) -> Result<CacheHandle, Error>;

    /// Get cache directory for dependencies
    async fn get_dependency_cache(
        &self,
        language: &str,
        isolation: CacheIsolation,
    ) -> Result<CacheHandle, Error>;

    /// Cleanup old cache entries
    async fn cleanup(&self, max_age_seconds: u64) -> Result<CleanupStats, Error>;
}

/// CacheHandle represents a cached item that can be used by a backend
#[derive(Debug, Clone)]
pub struct CacheHandle {
    /// The actual storage location
    pub location: CacheLocation,

    /// Access permissions for this cache
    pub permissions: CachePermissions,

    /// Isolation context (which account/app can access this)
    pub isolation: CacheIsolation,
}

/// CacheLocation describes where the cached data lives
#[derive(Debug, Clone)]
pub enum CacheLocation {
    /// Local filesystem path
    Local(PathBuf),

    /// Kubernetes PersistentVolume mount specification
    K8sVolume {
        pv_claim_name: String,
        subpath: String,
    },

    /// S3 location
    S3 {
        bucket: String,
        key: String,
        etag: Option<String>,
    },

    /// Container image layer (already in container runtime)
    ContainerLayer { layer_id: String },
}

/// CachePermissions defines what operations are allowed on cached data
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CachePermissions {
    /// Read-only access
    ReadOnly,

    /// Read-write access
    ReadWrite,
}

/// CacheSource describes where to get data for caching
#[derive(Debug)]
pub enum CacheSource {
    /// Copy from local filesystem
    LocalPath(PathBuf),

    /// Download from URL
    Url(String),

    /// Raw bytes
    Bytes(Vec<u8>),
}

/// CleanupStats reports cache cleanup results
#[derive(Debug, Clone)]
pub struct CleanupStats {
    pub entries_removed: u32,
    pub bytes_freed: u64,
}

// ============================================================================
// Concrete Backend Implementations
// ============================================================================

// LocalBackend implemented in local.rs
