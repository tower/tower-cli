use std::collections::HashMap;
use std::path::PathBuf;

use tower_runtime::execution::{
    CacheBackend, CacheConfig, CacheIsolation, ExecutionBackend, ExecutionHandle, ExecutionSpec,
    ResourceLimits, RuntimeConfig,
};
use tower_runtime::subprocess::SubprocessBackend;
use tower_runtime::Status;

use config::Towerfile;
use tower_package::{Package, PackageSpec};

fn get_example_app_dir(name: &str) -> PathBuf {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.push("tests");
    path.push("example-apps");
    path.push(name);
    assert!(
        path.exists(),
        "Example app directory does not exist: {}",
        path.display()
    );
    path
}

async fn build_package_from_dir(dir: &PathBuf) -> Package {
    let towerfile = Towerfile::from_path(dir.join("Towerfile")).expect("Failed to load Towerfile");
    let spec = PackageSpec::from_towerfile(&towerfile);
    let mut package = Package::build(spec)
        .await
        .expect("Failed to build package from directory");
    package.unpack().await.expect("Failed to unpack package");
    package
}

async fn create_execution_spec(id: String, package: Package) -> ExecutionSpec {
    let tar_gz_path = package
        .package_file_path
        .expect("Package should have tar.gz file");

    let file = tokio::fs::File::open(&tar_gz_path)
        .await
        .expect("Failed to open package file");

    ExecutionSpec {
        id,
        telemetry_ctx: tower_telemetry::Context::new(),
        package_stream: Box::new(file),
        environment: "test".to_string(),
        secrets: HashMap::new(),
        parameters: HashMap::new(),
        env_vars: HashMap::new(),
        runtime: RuntimeConfig {
            image: "python:3.11".to_string(),
            version: None,
            cache: CacheConfig {
                enable_bundle_cache: false,
                enable_runtime_cache: false,
                enable_dependency_cache: false,
                backend: CacheBackend::None,
                isolation: CacheIsolation::None,
            },
            entrypoint: None,
            command: None,
        },
        resources: ResourceLimits {
            cpu_millicores: None,
            memory_mb: None,
            storage_mb: None,
            max_pids: None,
            gpu_count: 0,
            timeout_seconds: 300,
        },
        networking: None,
    }
}

/// Check if specific execution's temp directory exists
fn uv_temp_dir_exists(execution_id: &str) -> bool {
    let tmp_dir = std::env::temp_dir();
    let uv_cache_dir = tmp_dir.join(format!("tower-uv-{}", execution_id));
    uv_cache_dir.exists()
}

#[tokio::test]
async fn test_no_temp_file_accumulation_happy_path() {
    let execution_id = "test-happy-cleanup";

    // Execute app with dependencies
    let app_dir = get_example_app_dir("02-use-faker");
    let package = build_package_from_dir(&app_dir).await;
    let backend = SubprocessBackend::new(None);
    let spec = create_execution_spec(execution_id.to_string(), package).await;

    let mut handle = backend
        .create(spec)
        .await
        .expect("Failed to create execution");
    let status = handle
        .wait_for_completion()
        .await
        .expect("Failed to wait for completion");

    assert_eq!(status, Status::Exited, "App should exit successfully");

    // Cleanup
    handle.cleanup().await.expect("Failed to cleanup");

    // Verify this execution's temp directory was cleaned up
    assert!(
        !uv_temp_dir_exists(execution_id),
        "UV temp directory should be cleaned up after execution"
    );
}

#[tokio::test]
async fn test_no_temp_file_accumulation_on_termination() {
    let execution_id = "test-terminate-cleanup";

    // Execute app with dependencies
    let app_dir = get_example_app_dir("02-use-faker");
    let package = build_package_from_dir(&app_dir).await;
    let backend = SubprocessBackend::new(None);
    let spec = create_execution_spec(execution_id.to_string(), package).await;

    let mut handle = backend
        .create(spec)
        .await
        .expect("Failed to create execution");

    // Let it start, then terminate
    tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
    handle.terminate().await.expect("Failed to terminate");

    // Cleanup
    handle.cleanup().await.expect("Failed to cleanup");

    // Verify this execution's temp directory was cleaned up
    assert!(
        !uv_temp_dir_exists(execution_id),
        "UV temp directory should be cleaned up after termination"
    );
}

#[tokio::test]
async fn test_multiple_executions_no_accumulation() {
    // Run multiple executions
    for i in 0..3 {
        let execution_id = format!("test-multi-cleanup-{}", i);
        let app_dir = get_example_app_dir("01-hello-world");
        let package = build_package_from_dir(&app_dir).await;
        let backend = SubprocessBackend::new(None);
        let spec = create_execution_spec(execution_id.clone(), package).await;

        let mut handle = backend
            .create(spec)
            .await
            .expect("Failed to create execution");
        handle
            .wait_for_completion()
            .await
            .expect("Failed to wait for completion");
        handle.cleanup().await.expect("Failed to cleanup");

        // Verify each execution's temp directory is cleaned up
        assert!(
            !uv_temp_dir_exists(&execution_id),
            "UV temp directory {} should be cleaned up",
            execution_id
        );
    }
}
