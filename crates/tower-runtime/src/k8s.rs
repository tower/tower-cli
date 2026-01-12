//! Kubernetes backend for Tower execution
//!
//! This module provides ExecutionBackend implementation for Kubernetes, supporting:
//! - Pod-based isolation with resource limits
//! - PersistentVolumeClaim-based caching
//! - Service endpoints for long-running apps
//! - Log streaming from pods
//!
//! Only available with the "k8s" feature flag.

use crate::errors::Error;
use crate::execution::{
    BackendCapabilities, BundleRef, CacheBackend, ExecutionBackend, ExecutionHandle, ExecutionSpec,
    ExecutionStatus, LogChannel, LogLine, LogReceiver, LogStream, NetworkingSpec, ServiceEndpoint,
};

use async_trait::async_trait;
use chrono::Utc;
use k8s_openapi::api::core::v1::{
    ConfigMap, Container, Pod, PodSpec, ResourceRequirements, Service, ServicePort, ServiceSpec,
    Volume, VolumeMount,
};
use kube::{
    api::{Api, DeleteParams, LogParams, PostParams},
    runtime::wait::await_condition,
    Client,
};
use std::collections::BTreeMap;
use std::sync::Arc;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::sync::Mutex;
use tokio_util::compat::FuturesAsyncReadCompatExt;

/// K8sBackend executes apps as Kubernetes Pods
pub struct K8sBackend {
    client: Client,
    namespace: String,
    cache_pv_claim: Option<String>,
}

impl K8sBackend {
    /// Create a new K8sBackend
    pub async fn new(namespace: String, cache_pv_claim: Option<String>) -> Result<Self, Error> {
        let client = Client::try_default()
            .await
            .map_err(|_| Error::RuntimeStartFailed)?;

        Ok(Self {
            client,
            namespace,
            cache_pv_claim,
        })
    }

    /// Build pod spec from execution spec
    fn build_pod_spec(
        &self,
        spec: &ExecutionSpec,
        path_mapping: &BTreeMap<String, String>,
    ) -> Result<Pod, Error> {
        let mut labels = BTreeMap::new();
        labels.insert("app".to_string(), "tower-app".to_string());
        labels.insert("execution-id".to_string(), spec.id.clone());

        // Build environment variables
        let mut env_vars = vec![];
        for (key, value) in &spec.secrets {
            env_vars.push(k8s_openapi::api::core::v1::EnvVar {
                name: key.clone(),
                value: Some(value.clone()),
                ..Default::default()
            });
        }
        for (key, value) in &spec.parameters {
            env_vars.push(k8s_openapi::api::core::v1::EnvVar {
                name: key.clone(),
                value: Some(value.clone()),
                ..Default::default()
            });
        }
        for (key, value) in &spec.env_vars {
            env_vars.push(k8s_openapi::api::core::v1::EnvVar {
                name: key.clone(),
                value: Some(value.clone()),
                ..Default::default()
            });
        }

        // Build volume mounts for caching
        let mut volume_mounts = vec![];
        let mut volumes = vec![];

        if let CacheBackend::K8sPersistentVolume { pv_claim_name } = &spec.runtime.cache.backend {
            // Mount cache PVC
            volume_mounts.push(VolumeMount {
                name: "cache".to_string(),
                mount_path: "/cache".to_string(),
                ..Default::default()
            });
            volumes.push(Volume {
                name: "cache".to_string(),
                persistent_volume_claim: Some(
                    k8s_openapi::api::core::v1::PersistentVolumeClaimVolumeSource {
                        claim_name: pv_claim_name.clone(),
                        read_only: Some(false),
                    },
                ),
                ..Default::default()
            });
        }

        // Build resource requirements
        let mut resource_limits = BTreeMap::new();
        let mut resource_requests = BTreeMap::new();

        if let Some(cpu) = spec.resources.cpu_millicores {
            let cpu_str = format!("{}m", cpu);
            resource_limits.insert(
                "cpu".to_string(),
                k8s_openapi::apimachinery::pkg::api::resource::Quantity(cpu_str.clone()),
            );
            resource_requests.insert(
                "cpu".to_string(),
                k8s_openapi::apimachinery::pkg::api::resource::Quantity(cpu_str),
            );
        }

        if let Some(memory) = spec.resources.memory_mb {
            let mem_str = format!("{}Mi", memory);
            resource_limits.insert(
                "memory".to_string(),
                k8s_openapi::apimachinery::pkg::api::resource::Quantity(mem_str.clone()),
            );
            resource_requests.insert(
                "memory".to_string(),
                k8s_openapi::apimachinery::pkg::api::resource::Quantity(mem_str),
            );
        }

        if let Some(storage) = spec.resources.storage_mb {
            let storage_str = format!("{}Mi", storage);
            resource_limits.insert(
                "ephemeral-storage".to_string(),
                k8s_openapi::apimachinery::pkg::api::resource::Quantity(storage_str.clone()),
            );
            resource_requests.insert(
                "ephemeral-storage".to_string(),
                k8s_openapi::apimachinery::pkg::api::resource::Quantity(storage_str),
            );
        }

        let resources = ResourceRequirements {
            limits: Some(resource_limits),
            requests: Some(resource_requests),
            ..Default::default()
        };

        // Add bundle volume mount
        volume_mounts.push(VolumeMount {
            name: "bundle".to_string(),
            mount_path: "/app".to_string(),
            read_only: Some(true),
            ..Default::default()
        });

        // Build items array to map ConfigMap keys to their original paths
        // e.g., "app__task.py" -> "app/task.py"
        let items: Vec<k8s_openapi::api::core::v1::KeyToPath> = path_mapping
            .iter()
            .map(
                |(sanitized_key, original_path)| k8s_openapi::api::core::v1::KeyToPath {
                    key: sanitized_key.clone(),
                    path: original_path.clone(),
                    mode: Some(0o755),
                },
            )
            .collect();

        // Bundle will be provided as a ConfigMap (created separately)
        volumes.push(Volume {
            name: "bundle".to_string(),
            config_map: Some(k8s_openapi::api::core::v1::ConfigMapVolumeSource {
                name: format!("bundle-{}", spec.id),
                default_mode: Some(0o755),
                items: Some(items),
                ..Default::default()
            }),
            ..Default::default()
        });

        // Build container spec
        // Note: In K8s, 'command' = entrypoint, 'args' = command
        let container = Container {
            name: "app".to_string(),
            image: Some(spec.runtime.image.clone()),
            env: Some(env_vars),
            command: spec.runtime.entrypoint.clone(), // K8s command = entrypoint
            args: spec.runtime.command.clone(),       // K8s args = command
            volume_mounts: if volume_mounts.is_empty() {
                None
            } else {
                Some(volume_mounts)
            },
            resources: Some(resources),
            working_dir: Some("/app".to_string()),
            ..Default::default()
        };

        // Build pod spec
        let pod_spec = PodSpec {
            containers: vec![container],
            volumes: if volumes.is_empty() {
                None
            } else {
                Some(volumes)
            },
            restart_policy: Some("Never".to_string()),
            ..Default::default()
        };

        Ok(Pod {
            metadata: k8s_openapi::apimachinery::pkg::apis::meta::v1::ObjectMeta {
                name: Some(format!("tower-run-{}", spec.id)),
                namespace: Some(self.namespace.clone()),
                labels: Some(labels),
                ..Default::default()
            },
            spec: Some(pod_spec),
            ..Default::default()
        })
    }

    /// Create ConfigMap with bundle contents
    /// Returns a mapping of sanitized keys to original paths for volume mounting
    async fn create_bundle_configmap(
        &self,
        spec: &ExecutionSpec,
    ) -> Result<BTreeMap<String, String>, Error> {
        use k8s_openapi::api::core::v1::ConfigMap;
        use std::collections::BTreeMap;

        let configmaps: Api<ConfigMap> = Api::namespaced(self.client.clone(), &self.namespace);

        // Get bundle path
        let bundle_path = match &spec.bundle {
            BundleRef::Local { path } => path,
            _ => return Err(Error::NotImplemented), // Only Local bundles supported for now
        };

        // Recursively read ALL files from the bundle directory
        let mut data = BTreeMap::new();
        let mut binary_data = BTreeMap::new();
        let mut path_mapping = BTreeMap::new(); // sanitized_key -> original_path

        Self::walk_directory(
            &bundle_path,
            &bundle_path,
            &mut data,
            &mut binary_data,
            &mut path_mapping,
        )
        .await?;

        if data.is_empty() && binary_data.is_empty() {
            return Err(Error::RuntimeStartFailed); // No files found
        }

        let configmap = ConfigMap {
            metadata: k8s_openapi::apimachinery::pkg::apis::meta::v1::ObjectMeta {
                name: Some(format!("bundle-{}", spec.id)),
                namespace: Some(self.namespace.clone()),
                ..Default::default()
            },
            data: if !data.is_empty() { Some(data) } else { None },
            binary_data: if !binary_data.is_empty() {
                Some(binary_data)
            } else {
                None
            },
            ..Default::default()
        };

        configmaps
            .create(&PostParams::default(), &configmap)
            .await
            .map_err(|_| Error::RuntimeStartFailed)?;

        Ok(path_mapping)
    }

    /// Sanitize a file path to be a valid ConfigMap key
    /// Replaces '/' with '__' to comply with K8s key restrictions: [-._a-zA-Z0-9]+
    fn sanitize_configmap_key(path: &str) -> String {
        path.replace('/', "__")
    }

    /// Recursively walk directory and collect all files
    async fn walk_directory(
        current_path: &std::path::Path,
        base_path: &std::path::Path,
        text_data: &mut BTreeMap<String, String>,
        binary_data: &mut BTreeMap<String, k8s_openapi::ByteString>,
        path_mapping: &mut BTreeMap<String, String>,
    ) -> Result<(), Error> {
        use tokio::fs;

        let mut entries = fs::read_dir(current_path)
            .await
            .map_err(|_| Error::RuntimeStartFailed)?;

        while let Some(entry) = entries
            .next_entry()
            .await
            .map_err(|_| Error::RuntimeStartFailed)?
        {
            let path = entry.path();

            if path.is_dir() {
                // Recursively process subdirectories
                Box::pin(Self::walk_directory(
                    &path,
                    base_path,
                    text_data,
                    binary_data,
                    path_mapping,
                ))
                .await?;
            } else if path.is_file() {
                // Get relative path from base (e.g., "app/task.py")
                let relative_path = path
                    .strip_prefix(base_path)
                    .map_err(|_| Error::RuntimeStartFailed)?
                    .to_str()
                    .ok_or(Error::RuntimeStartFailed)?
                    .to_string();

                // Sanitize the key for ConfigMap (e.g., "app/task.py" -> "app__task.py")
                let sanitized_key = Self::sanitize_configmap_key(&relative_path);

                // Store mapping for volume mount reconstruction
                path_mapping.insert(sanitized_key.clone(), relative_path.clone());

                // Try reading as text first
                match fs::read_to_string(&path).await {
                    Ok(contents) => {
                        text_data.insert(sanitized_key, contents);
                    }
                    Err(_) => {
                        // If not text, read as binary
                        if let Ok(contents) = fs::read(&path).await {
                            binary_data.insert(sanitized_key, k8s_openapi::ByteString(contents));
                        }
                    }
                }
            }
        }

        Ok(())
    }

    /// Build service spec for networking
    fn build_service_spec(
        &self,
        exec_id: &str,
        networking: &NetworkingSpec,
    ) -> Result<Service, Error> {
        let mut labels = BTreeMap::new();
        labels.insert("app".to_string(), "tower-app".to_string());
        labels.insert("execution-id".to_string(), exec_id.to_string());

        let service_port = ServicePort {
            name: Some("http".to_string()),
            port: networking.port as i32,
            target_port: Some(
                k8s_openapi::apimachinery::pkg::util::intstr::IntOrString::Int(
                    networking.port as i32,
                ),
            ),
            ..Default::default()
        };

        let service_spec = ServiceSpec {
            selector: Some(labels.clone()),
            ports: Some(vec![service_port]),
            type_: Some("ClusterIP".to_string()),
            ..Default::default()
        };

        Ok(Service {
            metadata: k8s_openapi::apimachinery::pkg::apis::meta::v1::ObjectMeta {
                name: Some(
                    networking
                        .service_name
                        .clone()
                        .unwrap_or_else(|| format!("tower-svc-{}", exec_id)),
                ),
                namespace: Some(self.namespace.clone()),
                labels: Some(labels),
                ..Default::default()
            },
            spec: Some(service_spec),
            ..Default::default()
        })
    }
}

#[async_trait]
impl ExecutionBackend for K8sBackend {
    type Handle = K8sHandle;

    async fn create(&self, spec: ExecutionSpec) -> Result<Self::Handle, Error> {
        let pods: Api<Pod> = Api::namespaced(self.client.clone(), &self.namespace);

        // Create ConfigMap with bundle contents and get path mapping
        let path_mapping = self.create_bundle_configmap(&spec).await?;

        // Build and create pod with path mapping for volume items
        let pod = self.build_pod_spec(&spec, &path_mapping)?;
        let pod_name = pod.metadata.name.clone().ok_or(Error::RuntimeStartFailed)?;

        pods.create(&PostParams::default(), &pod)
            .await
            .map_err(|_| Error::RuntimeStartFailed)?;

        // Create service if networking is specified
        let service_endpoint = if let Some(networking) = &spec.networking {
            if networking.expose_service {
                let services: Api<Service> = Api::namespaced(self.client.clone(), &self.namespace);
                let service = self.build_service_spec(&spec.id, networking)?;
                let service_name = service
                    .metadata
                    .name
                    .clone()
                    .ok_or(Error::RuntimeStartFailed)?;

                services
                    .create(&PostParams::default(), &service)
                    .await
                    .map_err(|_| Error::RuntimeStartFailed)?;

                Some(ServiceEndpoint {
                    host: format!("{}.{}.svc.cluster.local", service_name, self.namespace),
                    port: networking.port,
                    protocol: "http".to_string(),
                    url: Some(format!(
                        "http://{}.{}.svc.cluster.local:{}",
                        service_name, self.namespace, networking.port
                    )),
                })
            } else {
                None
            }
        } else {
            None
        };

        Ok(K8sHandle {
            id: spec.id,
            pod_name,
            namespace: self.namespace.clone(),
            client: self.client.clone(),
            service_endpoint: Arc::new(Mutex::new(service_endpoint)),
        })
    }

    fn capabilities(&self) -> BackendCapabilities {
        BackendCapabilities {
            name: "k8s".to_string(),
            supports_persistent_cache: true,
            supports_prewarming: true,
            supports_network_isolation: true,
            supports_service_endpoints: true,
            typical_cold_start_ms: 5000, // ~5s for image pull + pod start
            typical_warm_start_ms: 1000, // ~1s with cached image
            max_concurrent_executions: None, // Limited by cluster capacity
        }
    }

    async fn cleanup(&self) -> Result<(), Error> {
        // No global cleanup needed for K8s backend
        Ok(())
    }
}

/// K8sHandle provides lifecycle management for a Kubernetes Pod execution
pub struct K8sHandle {
    id: String,
    pod_name: String,
    namespace: String,
    client: Client,
    service_endpoint: Arc<Mutex<Option<ServiceEndpoint>>>,
}

#[async_trait]
impl ExecutionHandle for K8sHandle {
    fn id(&self) -> &str {
        &self.id
    }

    async fn status(&self) -> Result<ExecutionStatus, Error> {
        let pods: Api<Pod> = Api::namespaced(self.client.clone(), &self.namespace);

        let pod = pods
            .get(&self.pod_name)
            .await
            .map_err(|_| Error::NoRunningApp)?;

        let phase = pod
            .status
            .and_then(|s| s.phase)
            .unwrap_or_else(|| "Unknown".to_string());

        Ok(match phase.as_str() {
            "Pending" => ExecutionStatus::Preparing,
            "Running" => ExecutionStatus::Running,
            "Succeeded" => ExecutionStatus::Succeeded,
            "Failed" => ExecutionStatus::Failed { exit_code: 1 },
            _ => ExecutionStatus::Unknown,
        })
    }

    async fn logs(&self) -> Result<LogReceiver, Error> {
        let pods: Api<Pod> = Api::namespaced(self.client.clone(), &self.namespace);
        let (tx, rx) = tokio::sync::mpsc::unbounded_channel();

        let pod_name = self.pod_name.clone();
        let pods_clone = pods.clone();

        tokio::spawn(async move {
            // Wait for pod to have containers created (Running, Succeeded, or Failed)
            // This ensures we can stream logs even if the pod crashes
            let condition = await_condition(pods_clone.clone(), &pod_name, |obj: Option<&Pod>| {
                obj.and_then(|pod| pod.status.as_ref())
                    .and_then(|status| status.phase.as_ref())
                    .map(|phase| phase == "Running" || phase == "Succeeded" || phase == "Failed")
                    .unwrap_or(false)
            });

            // Wait with a timeout
            if tokio::time::timeout(std::time::Duration::from_secs(60), condition)
                .await
                .is_ok()
            {
                let log_params = LogParams {
                    follow: true,
                    ..Default::default()
                };

                if let Ok(logs) = pods_clone.log_stream(&pod_name, &log_params).await {
                    // Convert futures AsyncBufRead to tokio AsyncRead
                    let compat_logs = logs.compat();
                    let mut reader = BufReader::new(compat_logs).lines();
                    while let Ok(Some(line)) = reader.next_line().await {
                        let log_line = LogLine {
                            timestamp: Utc::now(),
                            stream: LogStream::Stdout, // K8s combines stdout/stderr
                            channel: LogChannel::Program,
                            content: line,
                        };
                        if tx.send(log_line).is_err() {
                            break;
                        }
                    }
                }
            }
        });

        Ok(rx)
    }

    async fn terminate(&mut self) -> Result<(), Error> {
        let pods: Api<Pod> = Api::namespaced(self.client.clone(), &self.namespace);

        pods.delete(&self.pod_name, &DeleteParams::default())
            .await
            .map_err(|_| Error::TerminateFailed)?;

        Ok(())
    }

    async fn kill(&mut self) -> Result<(), Error> {
        // For K8s, kill is the same as terminate (pod deletion)
        self.terminate().await
    }

    async fn wait_for_completion(&self) -> Result<ExecutionStatus, Error> {
        let pods: Api<Pod> = Api::namespaced(self.client.clone(), &self.namespace);

        // Wait for pod to reach terminal state
        await_condition(pods.clone(), &self.pod_name, |obj: Option<&Pod>| {
            obj.and_then(|pod| pod.status.as_ref())
                .and_then(|status| status.phase.as_ref())
                .map(|phase| phase == "Succeeded" || phase == "Failed")
                .unwrap_or(false)
        })
        .await
        .map_err(|_| Error::Timeout)?;

        self.status().await
    }

    async fn service_endpoint(&self) -> Result<Option<ServiceEndpoint>, Error> {
        let endpoint = self.service_endpoint.lock().await;
        Ok(endpoint.clone())
    }

    async fn cleanup(&mut self) -> Result<(), Error> {
        // Delete pod
        self.terminate().await?;

        // Delete ConfigMap with bundle
        let configmaps: Api<ConfigMap> = Api::namespaced(self.client.clone(), &self.namespace);
        let configmap_name = format!("bundle-{}", self.id);
        let _ = configmaps
            .delete(&configmap_name, &DeleteParams::default())
            .await;

        // Delete service if it exists
        if let Some(endpoint) = self.service_endpoint.lock().await.as_ref() {
            let services: Api<Service> = Api::namespaced(self.client.clone(), &self.namespace);
            // Extract service name from hostname
            let service_name = endpoint.host.split('.').next().unwrap_or("unknown");
            let _ = services
                .delete(service_name, &DeleteParams::default())
                .await;
        }

        Ok(())
    }
}
