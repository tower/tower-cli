// This test clears PATH for the whole process, so it lives in its own test binary.
#![cfg(unix)]

use std::collections::HashMap;
use std::path::PathBuf;

use tokio::sync::mpsc::unbounded_channel;

use config::Towerfile;
use tower_package::{Package, PackageSpec};
use tower_runtime::{errors::Error, local::LocalApp, App, AppFailure, StartOptions, Status};

#[tokio::test]
async fn test_bun_app_fails_without_bun() {
    let dir = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/example-apps/08-bun-hello");
    let towerfile = Towerfile::from_path(dir.join("Towerfile")).expect("Failed to load Towerfile");
    let mut package = Package::build(PackageSpec::from_towerfile(&towerfile))
        .await
        .expect("Failed to build package");
    package.unpack().await.expect("Failed to unpack package");

    std::env::set_var("PATH", "");

    let (sender, mut receiver) = unbounded_channel();
    let opts = StartOptions {
        ctx: tower_telemetry::Context::new("runner-id".to_string()),
        package,
        output_sender: sender,
        cwd: None,
        environment: "local".to_string(),
        secrets: HashMap::new(),
        parameters: HashMap::new(),
        env_vars: HashMap::new(),
        cache_dir: None,
    };

    let app = LocalApp::start(opts).await.expect("Failed to start app");
    while receiver.recv().await.is_some() {}

    let status = app.status().await.expect("Failed to get app status");
    assert_eq!(
        status,
        Status::Failed(AppFailure::Runtime(Error::MissingBun))
    );
}
