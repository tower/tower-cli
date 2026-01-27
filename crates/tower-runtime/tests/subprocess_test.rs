use std::collections::HashMap;
use std::path::PathBuf;

use tower_runtime::execution::{
    CacheBackend, CacheConfig, CacheIsolation, ExecutionBackend, ExecutionHandle, ExecutionSpec,
    NetworkingSpec, ResourceLimits, RuntimeConfig,
};
use tower_runtime::subprocess::SubprocessBackend;
use tower_runtime::Status;

use config::Towerfile;
use tower_package::{Package, PackageSpec};
use tower_telemetry::{self, debug};

fn get_example_app_dir(name: &str) -> PathBuf {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.push("tests");
    path.push("example-apps");
    path.push(name);

    if !path.exists() {
        panic!("Example app directory does not exist: {}", path.display());
    }

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

/// Count uv lock files in /tmp directory
fn count_uv_lock_files() -> usize {
    let tmp_dir = std::env::temp_dir();
    let mut count = 0;

    if let Ok(entries) = std::fs::read_dir(&tmp_dir) {
        for entry in entries.flatten() {
            if let Ok(file_name) = entry.file_name().into_string() {
                if file_name.starts_with("uv-") && file_name.ends_with(".lock") {
                    count += 1;
                }
            }
        }
    }

    count
}

/// Create a package stream from a built package
async fn create_package_stream(package: Package) -> Box<dyn tokio::io::AsyncRead + Send + Unpin> {
    // Get the package tar.gz path
    let tar_gz_path = package
        .package_file_path
        .expect("Package should have tar.gz file");

    let file = tokio::fs::File::open(&tar_gz_path)
        .await
        .expect("Failed to open package file");

    Box::new(file)
}

#[tokio::test]
async fn test_temp_file_accumulation_happy_path() {
    tower_telemetry::enable_logging(
        tower_telemetry::LogLevel::Debug,
        tower_telemetry::LogFormat::Plain,
        tower_telemetry::LogDestination::Stdout,
    );

    debug!("Testing temp file accumulation - happy path");

    // Count uv lock files before execution
    let before_count = count_uv_lock_files();
    debug!("UV lock files before execution: {}", before_count);

    // Build a simple app
    let hello_world_dir = get_example_app_dir("01-hello-world");
    let package = build_package_from_dir(&hello_world_dir).await;

    // Create subprocess backend WITHOUT cache directory (this triggers the problem)
    let backend = SubprocessBackend::new(None);

    // Create execution spec
    let spec = ExecutionSpec {
        id: "test-exec-happy".to_string(),
        telemetry_ctx: tower_telemetry::Context::new(),
        package_stream: create_package_stream(package).await,
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
    };

    // Create and run execution
    let mut handle = backend
        .create(spec)
        .await
        .expect("Failed to create execution");

    // Wait for completion
    let status = handle
        .wait_for_completion()
        .await
        .expect("Failed to wait for completion");
    debug!("Execution completed with status: {:?}", status);

    assert_eq!(status, Status::Exited, "App should exit successfully");

    // Count uv lock files after execution (in system /tmp)
    let after_count = count_uv_lock_files();
    debug!("UV lock files in /tmp after execution: {}", after_count);

    // With the fix: temp files should NOT accumulate in /tmp because they go in isolated directory
    assert_eq!(
        after_count, before_count,
        "UV temp files should NOT accumulate in /tmp with the fix. Before: {}, After: {}",
        before_count, after_count
    );

    // Verify the isolated temp directory was created
    let temp_dir_path = std::env::temp_dir().join("tower-uv-test-exec-happy");
    debug!("Checking for isolated temp directory: {:?}", temp_dir_path);
    assert!(
        temp_dir_path.exists(),
        "Isolated temp directory should exist during execution"
    );

    // Clean up the execution
    handle.cleanup().await.expect("Failed to cleanup");

    // Count again after cleanup
    let after_cleanup_count = count_uv_lock_files();
    debug!(
        "UV lock files in /tmp after cleanup: {}",
        after_cleanup_count
    );

    // With the fix: cleanup should not increase files in /tmp
    assert_eq!(
        after_cleanup_count, before_count,
        "UV temp files in /tmp should remain unchanged after cleanup. Before: {}, After cleanup: {}",
        before_count, after_cleanup_count
    );

    // Verify the isolated temp directory was cleaned up
    assert!(
        !temp_dir_path.exists(),
        "Isolated temp directory should be cleaned up after execution"
    );
}

#[tokio::test]
async fn test_temp_file_accumulation_termination() {
    tower_telemetry::enable_logging(
        tower_telemetry::LogLevel::Debug,
        tower_telemetry::LogFormat::Plain,
        tower_telemetry::LogDestination::Stdout,
    );

    debug!("Testing temp file accumulation - termination scenario");

    // Count uv lock files before execution
    let before_count = count_uv_lock_files();
    debug!("UV lock files before execution: {}", before_count);

    // Build an app with dependencies that takes longer to start
    let use_faker_dir = get_example_app_dir("02-use-faker");
    let package = build_package_from_dir(&use_faker_dir).await;

    // Create subprocess backend WITHOUT cache directory
    let backend = SubprocessBackend::new(None);

    // Create execution spec
    let spec = ExecutionSpec {
        id: "test-exec-terminate".to_string(),
        telemetry_ctx: tower_telemetry::Context::new(),
        package_stream: create_package_stream(package).await,
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
    };

    // Create execution
    let mut handle = backend
        .create(spec)
        .await
        .expect("Failed to create execution");

    // Let it start (uv venv + sync will create temp files)
    tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;

    // Check that temp files were NOT created in /tmp (with the fix)
    let during_count = count_uv_lock_files();
    debug!("UV lock files in /tmp during execution: {}", during_count);

    // With the fix: no files should accumulate in system /tmp
    assert_eq!(
        during_count, before_count,
        "UV temp files should NOT accumulate in /tmp during execution. Before: {}, During: {}",
        before_count, during_count
    );

    // Verify the isolated temp directory exists
    let temp_dir_path = std::env::temp_dir().join("tower-uv-test-exec-terminate");
    debug!("Checking for isolated temp directory: {:?}", temp_dir_path);
    assert!(
        temp_dir_path.exists(),
        "Isolated temp directory should exist during execution"
    );

    // Terminate the execution
    handle.terminate().await.expect("Failed to terminate");
    debug!("Execution terminated");

    // Count uv lock files after termination
    let after_count = count_uv_lock_files();
    debug!("UV lock files in /tmp after termination: {}", after_count);

    // With the fix: no files should have been added to /tmp
    assert_eq!(
        after_count, before_count,
        "UV temp files in /tmp should remain unchanged after termination. Before: {}, After: {}",
        before_count, after_count
    );

    // Clean up
    handle.cleanup().await.expect("Failed to cleanup");

    // Count again after cleanup
    let after_cleanup_count = count_uv_lock_files();
    debug!(
        "UV lock files in /tmp after cleanup: {}",
        after_cleanup_count
    );

    // With the fix: still no files in /tmp
    assert_eq!(
        after_cleanup_count, before_count,
        "UV temp files in /tmp should remain unchanged after cleanup. Before: {}, After cleanup: {}",
        before_count, after_cleanup_count
    );

    // Verify the isolated temp directory was cleaned up
    assert!(
        !temp_dir_path.exists(),
        "Isolated temp directory should be cleaned up after explicit cleanup"
    );
}
