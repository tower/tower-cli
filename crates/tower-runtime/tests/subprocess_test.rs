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

/// Find UV cache directories in /tmp and default cache location
/// UV creates cache directories when TMPDIR is set and no --cache-dir is provided
fn find_uv_cache_dirs() -> Vec<PathBuf> {
    let mut cache_dirs = Vec::new();

    // Check /tmp for temporary cache directories
    let tmp_dir = std::env::temp_dir();
    if let Ok(entries) = std::fs::read_dir(&tmp_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                // Check if it looks like a UV cache by inspecting contents
                if path.join("wheels").exists()
                    || path.join("built-wheels").exists()
                    || path.join("simple-v12").exists()
                    || path.join("archive-v0").exists()
                {
                    cache_dirs.push(path);
                }
            }
        }
    }

    // Also check default UV cache location
    if let Ok(home) = std::env::var("HOME") {
        let default_uv_cache = PathBuf::from(home).join(".cache").join("uv");
        if default_uv_cache.exists() {
            cache_dirs.push(default_uv_cache);
        }
    }

    cache_dirs
}

/// Calculate total size of directories in bytes
fn calculate_dir_size(paths: &[PathBuf]) -> u64 {
    let mut total = 0u64;
    for path in paths {
        if let Ok(metadata) = std::fs::metadata(path) {
            if metadata.is_file() {
                total += metadata.len();
            } else if metadata.is_dir() {
                // Recursively calculate directory size
                if let Ok(entries) = std::fs::read_dir(path) {
                    for entry in entries.flatten() {
                        total += calculate_dir_size(&[entry.path()]);
                    }
                }
            }
        }
    }
    total
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

#[tokio::test]
async fn test_uv_cache_directory_accumulation() {
    tower_telemetry::enable_logging(
        tower_telemetry::LogLevel::Debug,
        tower_telemetry::LogFormat::Plain,
        tower_telemetry::LogDestination::Stdout,
    );

    debug!("Testing UV cache directory accumulation");

    // Find existing UV cache directories and calculate size
    let before_dirs = find_uv_cache_dirs();
    let before_size = calculate_dir_size(&before_dirs);
    debug!(
        "Before execution: {} UV cache dirs, total size: {} bytes ({} MB)",
        before_dirs.len(),
        before_size,
        before_size / 1024 / 1024
    );
    for dir in &before_dirs {
        debug!("  - {:?}", dir);
    }

    // Run multiple executions with dependencies to trigger cache creation
    for i in 0..3 {
        debug!("Execution {} starting", i);

        let use_faker_dir = get_example_app_dir("02-use-faker");
        let package = build_package_from_dir(&use_faker_dir).await;

        let backend = SubprocessBackend::new(None);

        let spec = ExecutionSpec {
            id: format!("test-cache-{}", i),
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

        let mut handle = backend
            .create(spec)
            .await
            .expect("Failed to create execution");

        // Give UV time to start and create cache
        tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;

        // Check isolated cache directory DURING execution
        let isolated_cache_path = std::env::temp_dir().join(format!("tower-uv-test-cache-{}", i));
        if isolated_cache_path.exists() {
            debug!(
                "Execution {} - Isolated cache directory exists during execution",
                i
            );

            // List what's inside
            if let Ok(entries) = std::fs::read_dir(&isolated_cache_path) {
                for entry in entries.flatten().take(10) {
                    debug!("    {:?}", entry.file_name());
                }
            }

            // Check for UV cache structure
            let has_cache_artifacts = isolated_cache_path.join("wheels").exists()
                || isolated_cache_path.join("built-wheels").exists()
                || isolated_cache_path.join("simple-v12").exists()
                || isolated_cache_path.join("archive-v0").exists();

            if has_cache_artifacts {
                debug!("  ✓ Contains UV cache artifacts");
            } else {
                debug!("  ⚠ No typical UV cache structure found");
            }
        } else {
            debug!(
                "  ⚠ Isolated cache directory does not exist during execution {}",
                i
            );
        }

        // Wait for completion
        handle
            .wait_for_completion()
            .await
            .expect("Failed to wait for completion");

        // Verify cache size before cleanup
        if isolated_cache_path.exists() {
            let cache_size = calculate_dir_size(&[isolated_cache_path.clone()]);
            debug!(
                "Execution {} - Cache size before cleanup: {} MB",
                i,
                cache_size / 1024 / 1024
            );
        }

        // Clean up
        handle.cleanup().await.expect("Failed to cleanup");

        // Verify cleanup removed the isolated cache
        if isolated_cache_path.exists() {
            debug!("  ❌ WARNING: Isolated cache still exists after cleanup!");
        } else {
            debug!("  ✓ Isolated cache cleaned up successfully");
        }

        debug!("Execution {} completed and cleaned up", i);
    }

    // Check for cache directories after executions
    let after_dirs = find_uv_cache_dirs();
    let after_size = calculate_dir_size(&after_dirs);
    debug!(
        "After {} executions: {} UV cache dirs, total size: {} bytes ({} MB)",
        3,
        after_dirs.len(),
        after_size,
        after_size / 1024 / 1024
    );
    for dir in &after_dirs {
        debug!("  - {:?}", dir);
    }

    // The real problem: cache directories accumulating
    let size_increase = after_size.saturating_sub(before_size);
    debug!(
        "Size increase: {} bytes ({} MB)",
        size_increase,
        size_increase / 1024 / 1024
    );

    // With UV_CACHE_DIR set to isolated temp directories:
    // 1. Cache should NOT accumulate in ~/.cache/uv
    // 2. Cache should NOT accumulate in /tmp
    // 3. Each execution's cache is cleaned up after completion

    // Check if default UV cache grew (it shouldn't with our fix)
    if let Ok(home) = std::env::var("HOME") {
        let default_uv_cache = PathBuf::from(home).join(".cache").join("uv");
        let before_default = before_dirs.iter().find(|p| **p == default_uv_cache);
        let after_default = after_dirs.iter().find(|p| **p == default_uv_cache);

        match (before_default, after_default) {
            (Some(_), Some(_)) => {
                // Cache existed before and after - verify it didn't grow
                debug!(
                    "Default UV cache (~/.cache/uv) exists - should not have grown significantly"
                );
                assert!(
                    size_increase < 10_000_000, // Less than 10MB growth
                    "Default UV cache should not grow when UV_CACHE_DIR is set. Growth: {} MB",
                    size_increase / 1024 / 1024
                );
            }
            (None, Some(_)) => {
                // Cache was created - this is wrong, UV should use our isolated dir
                panic!("UV created cache in ~/.cache/uv despite UV_CACHE_DIR being set!");
            }
            _ => {
                debug!("Default UV cache doesn't exist - good, UV is using isolated directories");
            }
        }
    }

    // Count cache directories in /tmp (there should be none after cleanup)
    let tmp_cache_dirs: Vec<_> = after_dirs
        .iter()
        .filter(|p| p.starts_with(&std::env::temp_dir()))
        .collect();

    debug!(
        "Cache directories remaining in /tmp: {} (should be 0)",
        tmp_cache_dirs.len()
    );

    // With our fix, all isolated temp dirs should be cleaned up
    assert_eq!(
        tmp_cache_dirs.len(),
        0,
        "No UV cache directories should remain in /tmp after cleanup. Found: {:?}",
        tmp_cache_dirs
    );
}
