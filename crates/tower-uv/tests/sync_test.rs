//! Integration tests for `Uv::sync` requirements.txt handling.
//!
//! These tests focus on the `setuptools<82` injection logic. The default path
//! resolves *without* the pin (most apps work fine with a modern setuptools);
//! the pin is only applied as a fallback when unpinned resolution fails (e.g.
//! `dlt[motherduck,hub]==1.26.0a1`-style transitive constraints).
//!
//! The tests shell out to a real `uv` binary and hit pypi over the network,
//! mirroring the existing `install_test.rs`.

use std::collections::HashMap;
use std::path::PathBuf;

use tempfile::TempDir;
use tokio::process::Child;
use tower_uv::Uv;

async fn wait(mut child: Child) -> i32 {
    let status = child.wait().await.expect("wait failed");
    status.code().unwrap_or(-1)
}

async fn make_uv_with_venv(cwd: &PathBuf) -> Uv {
    let uv = Uv::new(None, false).await.expect("Uv::new failed");
    let env_vars: HashMap<String, String> = HashMap::new();
    let venv_child = uv.venv(cwd, &env_vars).await.expect("venv spawn failed");
    let code = wait(venv_child).await;
    assert_eq!(code, 0, "venv creation failed");
    uv
}

#[tokio::test]
async fn sync_succeeds_without_pin_for_simple_requirements() {
    let tmp = TempDir::new().expect("tempdir");
    let cwd = tmp.path().to_path_buf();

    // Trivial requirements.txt — unpinned resolution succeeds, so we install
    // without the setuptools<82 pin.
    tokio::fs::write(cwd.join("requirements.txt"), "six\n")
        .await
        .expect("write requirements.txt");

    let uv = make_uv_with_venv(&cwd).await;
    let env_vars: HashMap<String, String> = HashMap::new();
    let child = uv.sync(&cwd, &env_vars).await.expect("sync spawn failed");
    let code = wait(child).await;
    assert_eq!(code, 0, "sync should succeed for simple requirements.txt");
}

#[tokio::test]
async fn sync_succeeds_when_user_requires_modern_setuptools() {
    let tmp = TempDir::new().expect("tempdir");
    let cwd = tmp.path().to_path_buf();

    // Regression test for the dlt scenario: an app that explicitly wants
    // setuptools>=82 should resolve cleanly (no pin gets injected).
    tokio::fs::write(cwd.join("requirements.txt"), "setuptools>=82\n")
        .await
        .expect("write requirements.txt");

    let uv = make_uv_with_venv(&cwd).await;
    let env_vars: HashMap<String, String> = HashMap::new();
    let child = uv.sync(&cwd, &env_vars).await.expect("sync spawn failed");
    let code = wait(child).await;
    assert_eq!(
        code, 0,
        "sync should succeed when the user requires setuptools>=82"
    );
}

#[tokio::test]
async fn sync_succeeds_when_user_pins_legacy_setuptools() {
    let tmp = TempDir::new().expect("tempdir");
    let cwd = tmp.path().to_path_buf();

    // Apps that need pkg_resources can pin setuptools<82 themselves; our logic
    // shouldn't get in the way.
    tokio::fs::write(cwd.join("requirements.txt"), "setuptools<82\n")
        .await
        .expect("write requirements.txt");

    let uv = make_uv_with_venv(&cwd).await;
    let env_vars: HashMap<String, String> = HashMap::new();
    let child = uv.sync(&cwd, &env_vars).await.expect("sync spawn failed");
    let code = wait(child).await;
    assert_eq!(code, 0, "sync should succeed when the user pins setuptools<82");
}
