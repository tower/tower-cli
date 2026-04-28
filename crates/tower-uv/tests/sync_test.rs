//! Integration tests for `Uv::sync` requirements.txt handling.
//!
//! `sync()` runs a plain `uv pip install -r requirements.txt` (no setuptools
//! pin). Callers that hit a resolution failure can retry via
//! `sync_with_legacy_setuptools_pin()` for the legacy `pkg_resources`
//! compatibility case. The retry orchestration lives in
//! `tower-runtime::local`.
//!
//! These tests shell out to a real `uv` binary and hit pypi, mirroring the
//! existing `install_test.rs`.

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
async fn sync_succeeds_for_simple_requirements() {
    let tmp = TempDir::new().expect("tempdir");
    let cwd = tmp.path().to_path_buf();

    tokio::fs::write(cwd.join("requirements.txt"), "six\n")
        .await
        .expect("write requirements.txt");

    let uv = make_uv_with_venv(&cwd).await;
    let env_vars: HashMap<String, String> = HashMap::new();
    let child = uv.sync(&cwd, &env_vars).await.expect("sync spawn failed");
    let code = wait(child).await;
    assert_eq!(code, 0, "sync should succeed for a simple requirements.txt");
}

#[tokio::test]
async fn sync_succeeds_when_user_requires_modern_setuptools() {
    let tmp = TempDir::new().expect("tempdir");
    let cwd = tmp.path().to_path_buf();

    // Regression case: an app that requires setuptools>=82 used to fail
    // because tower-uv unconditionally injected `setuptools<82`. Now the
    // default sync path applies no pin, so resolution should succeed.
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
async fn sync_with_legacy_setuptools_pin_installs_legacy_setuptools() {
    let tmp = TempDir::new().expect("tempdir");
    let cwd = tmp.path().to_path_buf();

    tokio::fs::write(cwd.join("requirements.txt"), "six\n")
        .await
        .expect("write requirements.txt");

    let uv = make_uv_with_venv(&cwd).await;
    let env_vars: HashMap<String, String> = HashMap::new();
    let child = uv
        .sync_with_legacy_setuptools_pin(&cwd, &env_vars)
        .await
        .expect("retry spawn failed");
    let code = wait(child).await;
    assert_eq!(
        code, 0,
        "sync_with_legacy_setuptools_pin should succeed when the pin is compatible"
    );
}

#[tokio::test]
async fn sync_with_legacy_setuptools_pin_fails_when_user_requires_modern_setuptools() {
    let tmp = TempDir::new().expect("tempdir");
    let cwd = tmp.path().to_path_buf();

    // The fallback method intentionally pins `setuptools<82`. When the user's
    // requirements demand setuptools>=82, the resolver must report a conflict
    // — this confirms the pin is actually being applied.
    tokio::fs::write(cwd.join("requirements.txt"), "setuptools>=82\n")
        .await
        .expect("write requirements.txt");

    let uv = make_uv_with_venv(&cwd).await;
    let env_vars: HashMap<String, String> = HashMap::new();
    let child = uv
        .sync_with_legacy_setuptools_pin(&cwd, &env_vars)
        .await
        .expect("retry spawn failed");
    let code = wait(child).await;
    assert_ne!(
        code, 0,
        "sync_with_legacy_setuptools_pin should fail when the pin conflicts with user's requirements"
    );
}

#[tokio::test]
async fn sync_with_legacy_setuptools_pin_errors_without_project_files() {
    let tmp = TempDir::new().expect("tempdir");
    let cwd = tmp.path().to_path_buf();

    let uv = Uv::new(None, false).await.expect("Uv::new failed");
    let env_vars: HashMap<String, String> = HashMap::new();
    let result = uv.sync_with_legacy_setuptools_pin(&cwd, &env_vars).await;
    assert!(
        matches!(result, Err(tower_uv::Error::MissingPyprojectToml)),
        "fallback should refuse to run without pyproject.toml or requirements.txt"
    );
}

#[tokio::test]
async fn sync_with_legacy_setuptools_pin_fails_for_pyproject_requiring_modern_setuptools() {
    let tmp = TempDir::new().expect("tempdir");
    let cwd = tmp.path().to_path_buf();

    // Mirrors the requirements.txt counterpart: when the project pins
    // setuptools>=82, the pin must conflict — proving it's actually applied.
    tokio::fs::write(
        cwd.join("pyproject.toml"),
        "[project]\nname = \"test-app\"\nversion = \"0.0.1\"\nrequires-python = \">=3.10\"\ndependencies = [\"setuptools>=82\"]\n",
    )
    .await
    .expect("write pyproject.toml");

    let uv = make_uv_with_venv(&cwd).await;
    let env_vars: HashMap<String, String> = HashMap::new();
    let child = uv
        .sync_with_legacy_setuptools_pin(&cwd, &env_vars)
        .await
        .expect("retry spawn failed");
    let code = wait(child).await;
    assert_ne!(
        code, 0,
        "sync_with_legacy_setuptools_pin should fail when the pyproject project requires setuptools>=82"
    );
}

#[tokio::test]
async fn sync_with_legacy_setuptools_pin_installs_for_pyproject() {
    let tmp = TempDir::new().expect("tempdir");
    let cwd = tmp.path().to_path_buf();

    tokio::fs::write(
        cwd.join("pyproject.toml"),
        "[project]\nname = \"test-app\"\nversion = \"0.0.1\"\nrequires-python = \">=3.10\"\ndependencies = [\"six\"]\n",
    )
    .await
    .expect("write pyproject.toml");

    let uv = make_uv_with_venv(&cwd).await;
    let env_vars: HashMap<String, String> = HashMap::new();
    let child = uv
        .sync_with_legacy_setuptools_pin(&cwd, &env_vars)
        .await
        .expect("retry spawn failed");
    let code = wait(child).await;
    assert_eq!(
        code, 0,
        "sync_with_legacy_setuptools_pin should succeed for a pyproject project"
    );
}
