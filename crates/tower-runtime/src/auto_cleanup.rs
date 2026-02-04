//! Automatic cleanup timer for subprocess executions
//!
//! This module exists to handle the case where the control plane
//! disconnects and never sends a cleanup call to the runner. Under normal circumstances,
//! the control plane should always call cleanup after a run finishes.
//!
//! **TODO**: Possibly remove this module once the control plane reliability issues are resolved.
//! ref: TOW-1342

use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;
use tmpdir::TmpDir;
use tokio::sync::Mutex;

use crate::App;

/// Spawns a background task that monitors an app and performs automatic cleanup
/// after a timeout if explicit cleanup hasn't been called.
///
/// This task:
/// 1. Polls the app status every n seconds
/// 2. When the app reaches a terminal state, waits for cleanup_timeout
/// 3. If cleanup_called flag is still false, performs cleanup and logs a warning
pub fn spawn_cleanup_monitor<T: App + 'static>(
    run_id: String,
    app: Arc<Mutex<T>>,
    package_tmp_dir: Arc<Mutex<Option<TmpDir>>>,
    uv_temp_dir: Arc<Mutex<Option<PathBuf>>>,
    cleanup_called: Arc<AtomicBool>,
    cleanup_timeout: Duration,
) {
    tokio::spawn(async move {
        use tower_telemetry::{info, warn};

        // Wait for terminal state
        loop {
            tokio::time::sleep(Duration::from_secs(5)).await;
            let status = app.lock().await.status().await;
            if matches!(status, Ok(s) if s.is_terminal()) {
                info!(
                    "Run {} finished, starting {}s automatic cleanup timer",
                    run_id,
                    cleanup_timeout.as_secs()
                );
                break;
            }
        }

        // Wait for cleanup timeout
        tokio::time::sleep(cleanup_timeout).await;

        // Check if explicit cleanup was called
        if cleanup_called.load(Ordering::Relaxed) {
            return;
        }

        // Perform automatic cleanup
        warn!(
            "Automatic cleanup triggered for run {} after {}s (control plane cleanup not received)",
            run_id,
            cleanup_timeout.as_secs()
        );

        if let Some(temp_dir) = uv_temp_dir.lock().await.take() {
            let _ = tokio::fs::remove_dir_all(&temp_dir).await;
        }

        if let Some(tmp_dir) = package_tmp_dir.lock().await.take() {
            let _ = tokio::fs::remove_dir_all(tmp_dir.to_path_buf()).await;
        }

        cleanup_called.store(true, Ordering::Relaxed);
    });
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{errors::Error, StartOptions, Status};

    /// Mock LocalApp for testing that allows controlled status transitions
    struct MockLocalApp {
        status: Arc<Mutex<Status>>,
    }

    impl MockLocalApp {
        fn new(initial_status: Status, transition_to_terminal_after: Duration) -> Self {
            let status = Arc::new(Mutex::new(initial_status));
            let app = Self {
                status: status.clone(),
            };

            // Spawn background task to transition to terminal state after delay
            tokio::spawn(async move {
                tokio::time::sleep(transition_to_terminal_after).await;
                *status.lock().await = Status::Exited;
            });

            app
        }
    }

    impl crate::App for MockLocalApp {
        async fn start(_opts: StartOptions) -> Result<Self, Error> {
            unimplemented!("MockLocalApp doesn't support start")
        }

        async fn terminate(&mut self) -> Result<(), Error> {
            Ok(())
        }

        async fn status(&self) -> Result<Status, Error> {
            Ok(*self.status.lock().await)
        }
    }

    /// Helper to create temp directories for testing
    async fn create_test_dirs() -> (TmpDir, PathBuf) {
        let package_tmp = TmpDir::new("test-package")
            .await
            .expect("Failed to create package temp dir");

        // Use timestamp for uniqueness
        let unique_id = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let uv_temp_path = std::env::temp_dir().join(format!("test-uv-{}", unique_id));
        tokio::fs::create_dir_all(&uv_temp_path)
            .await
            .expect("Failed to create uv temp dir");

        (package_tmp, uv_temp_path)
    }

    #[tokio::test]
    async fn test_automatic_cleanup_triggers_after_timeout() {
        // Create a mock app that transitions to Exited after 100ms
        let app = Arc::new(Mutex::new(MockLocalApp::new(
            Status::Running,
            Duration::from_millis(100),
        )));

        // Create temp directories
        let (package_tmp, uv_temp_path) = create_test_dirs().await;
        let package_tmp_dir = Arc::new(Mutex::new(Some(package_tmp)));
        let uv_temp_dir = Arc::new(Mutex::new(Some(uv_temp_path.clone())));
        let cleanup_called = Arc::new(AtomicBool::new(false));

        // Verify directories exist before cleanup
        assert!(tokio::fs::metadata(uv_temp_path.clone()).await.is_ok());

        // Spawn cleanup monitor with short timeout (500ms)
        spawn_cleanup_monitor(
            "test-run-1".to_string(),
            app,
            package_tmp_dir.clone(),
            uv_temp_dir.clone(),
            cleanup_called.clone(),
            Duration::from_millis(500),
        );

        // Wait for:
        // - App to transition (100ms)
        // - Polling to detect terminal state (up to 1000ms)
        // - Cleanup timeout (500ms)
        // - Buffer (500ms)
        tokio::time::sleep(Duration::from_millis(2200)).await;

        // Verify cleanup happened
        assert!(
            cleanup_called.load(Ordering::Relaxed),
            "Cleanup flag should be set"
        );

        // Verify directories were removed
        assert!(
            uv_temp_dir.lock().await.is_none(),
            "UV temp dir should be taken"
        );
        assert!(
            package_tmp_dir.lock().await.is_none(),
            "Package temp dir should be taken"
        );

        // Verify actual filesystem cleanup
        assert!(
            tokio::fs::metadata(uv_temp_path).await.is_err(),
            "UV temp directory should be deleted from filesystem"
        );
    }

    #[tokio::test]
    async fn test_explicit_cleanup_prevents_automatic_cleanup() {
        // Create a mock app that transitions to Exited after 100ms
        let app = Arc::new(Mutex::new(MockLocalApp::new(
            Status::Running,
            Duration::from_millis(100),
        )));

        // Create temp directories
        let (package_tmp, uv_temp_path) = create_test_dirs().await;
        let package_tmp_dir = Arc::new(Mutex::new(Some(package_tmp)));
        let uv_temp_dir = Arc::new(Mutex::new(Some(uv_temp_path.clone())));
        let cleanup_called = Arc::new(AtomicBool::new(false));

        // Spawn cleanup monitor with short timeout (500ms)
        spawn_cleanup_monitor(
            "test-run-2".to_string(),
            app,
            package_tmp_dir.clone(),
            uv_temp_dir.clone(),
            cleanup_called.clone(),
            Duration::from_millis(500),
        );

        // Wait for app to transition + polling to detect it (up to 1100ms)
        tokio::time::sleep(Duration::from_millis(1200)).await;

        // Simulate explicit cleanup call before timeout expires
        cleanup_called.store(true, Ordering::Relaxed);

        // Manually clean up directories (simulating explicit cleanup)
        if let Some(temp_dir) = uv_temp_dir.lock().await.take() {
            let _ = tokio::fs::remove_dir_all(&temp_dir).await;
        }
        if let Some(tmp_dir) = package_tmp_dir.lock().await.take() {
            let _ = tokio::fs::remove_dir_all(tmp_dir.to_path_buf()).await;
        }

        // Wait past the cleanup timeout (already waited 1200ms, need 500ms more + buffer)
        tokio::time::sleep(Duration::from_millis(700)).await;

        // Verify cleanup flag is still true
        assert!(
            cleanup_called.load(Ordering::Relaxed),
            "Cleanup flag should remain set"
        );

        // Verify directories were already cleaned up
        assert!(
            uv_temp_dir.lock().await.is_none(),
            "UV temp dir should already be taken"
        );
        assert!(
            package_tmp_dir.lock().await.is_none(),
            "Package temp dir should already be taken"
        );
    }

    #[tokio::test]
    async fn test_cleanup_waits_for_terminal_state() {
        // Create a mock app that takes longer to transition (1500ms)
        let app = Arc::new(Mutex::new(MockLocalApp::new(
            Status::Running,
            Duration::from_millis(1500),
        )));

        // Create temp directories
        let (package_tmp, uv_temp_path) = create_test_dirs().await;
        let package_tmp_dir = Arc::new(Mutex::new(Some(package_tmp)));
        let uv_temp_dir = Arc::new(Mutex::new(Some(uv_temp_path.clone())));
        let cleanup_called = Arc::new(AtomicBool::new(false));

        // Spawn cleanup monitor with short timeout (200ms)
        spawn_cleanup_monitor(
            "test-run-3".to_string(),
            app.clone(),
            package_tmp_dir.clone(),
            uv_temp_dir.clone(),
            cleanup_called.clone(),
            Duration::from_millis(200),
        );

        // Check status well before transition (500ms)
        tokio::time::sleep(Duration::from_millis(500)).await;

        // Cleanup should NOT have happened yet because app is still Running
        assert!(
            !cleanup_called.load(Ordering::Relaxed),
            "Cleanup should not trigger while app is still running"
        );

        // Verify directories still exist
        assert!(
            uv_temp_dir.lock().await.is_some(),
            "UV temp dir should still exist"
        );

        // Wait for:
        // - Rest of transition (1000ms more)
        // - Polling to detect terminal state (up to 1000ms)
        // - Cleanup timeout (200ms)
        // - Buffer (300ms)
        tokio::time::sleep(Duration::from_millis(2600)).await;

        // Now cleanup should have happened
        assert!(
            cleanup_called.load(Ordering::Relaxed),
            "Cleanup should trigger after app reaches terminal state"
        );

        // Cleanup the temp directory manually if test failed to clean it up
        let _ = tokio::fs::remove_dir_all(uv_temp_path).await;
    }
}
