use std::collections::HashMap;
use std::path::PathBuf;

use tower_runtime::{local::LocalApp, App, StartOptions, Status};

use config::Towerfile;
use tower_package::{Package, PackageSpec};
use tower_telemetry::{self, debug};

use tokio::sync::mpsc::unbounded_channel;

fn get_example_app_dir(name: &str) -> PathBuf {
    // This is where the root of the app lives.
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

#[tokio::test]
async fn test_running_hello_world() {
    tower_telemetry::enable_logging(
        tower_telemetry::LogLevel::Debug,
        tower_telemetry::LogFormat::Plain,
        tower_telemetry::LogDestination::Stdout,
    );

    debug!("Running 01-hello-world");
    let hello_world_dir = get_example_app_dir("01-hello-world");
    let package = build_package_from_dir(&hello_world_dir).await;
    let (sender, mut receiver) = unbounded_channel();

    // We need to create the package, which will load the app
    let opts = StartOptions {
        ctx: tower_telemetry::Context::new(),
        package,
        output_sender: sender,
        cwd: None,
        environment: "local".to_string(),
        secrets: HashMap::new(),
        parameters: HashMap::new(),
        env_vars: HashMap::new(),
    };

    // Start the app using the LocalApp runtime
    let app = LocalApp::start(opts).await.expect("Failed to start app");

    // The status should be running
    let status = app.status().await.expect("Failed to get app status");
    assert!(status == Status::Running, "App should be running");

    let mut outputs = Vec::new();
    while let Some(output) = receiver.recv().await {
        outputs.push(output.line);
    }

    let found_hello = outputs.iter().any(|line| line.contains("Hello, world!"));
    assert!(
        found_hello,
        "Should have received 'Hello, world!' output from the application"
    );

    // check the status once more, should be done.
    let status = app.status().await.expect("Failed to get app status");
    assert!(status == Status::Exited, "App should be running");
}

#[tokio::test]
async fn test_running_use_faker() {
    debug!("Running 02-use-faker");
    // This test is a simple test that outputs some text to the console; however, this time it has
    // a dependency defined in pyproject.toml, which means that it'll have to do a uv sync first.
    let use_faker_dir = get_example_app_dir("02-use-faker");
    let package = build_package_from_dir(&use_faker_dir).await;
    let (sender, mut receiver) = unbounded_channel();

    // We need to create the package, which will load the app
    let opts = StartOptions {
        ctx: tower_telemetry::Context::new(),
        package,
        output_sender: sender,
        cwd: None,
        environment: "local".to_string(),
        secrets: HashMap::new(),
        parameters: HashMap::new(),
        env_vars: HashMap::new(),
    };

    // Start the app using the LocalApp runtime
    let app = LocalApp::start(opts).await.expect("Failed to start app");

    // The status should be running
    let status = app.status().await.expect("Failed to get app status");
    assert!(status == Status::Running, "App should be running");

    let mut count_setup = 0;
    let mut count_stdout = 0;

    while let Some(output) = receiver.recv().await {
        debug!("Received output: {:?}", output.line);
        match output.channel {
            tower_runtime::Channel::Setup => {
                count_setup += 1;
            }
            tower_runtime::Channel::Program => {
                count_stdout += 1;
            }
        }
    }

    assert!(count_setup > 0, "There should be some setup output");
    assert!(count_stdout > 0, "should be more than one output");

    // check the status once more, should be done.
    let status = app.status().await.expect("Failed to get app status");
    assert!(status == Status::Exited, "App should be running");
}

#[tokio::test]
async fn test_running_legacy_app() {
    debug!("Running 03-legacy-app");
    // This test is a simple test that outputs some text to the console; however, this time it has
    // a dependency defined in pyproject.toml, which means that it'll have to do a uv sync first.
    let legacy_app_dir = get_example_app_dir("03-legacy-app");
    let package = build_package_from_dir(&legacy_app_dir).await;
    let (sender, mut receiver) = unbounded_channel();

    // We need to create the package, which will load the app
    let opts = StartOptions {
        ctx: tower_telemetry::Context::new(),
        package,
        output_sender: sender,
        cwd: None,
        environment: "local".to_string(),
        secrets: HashMap::new(),
        parameters: HashMap::new(),
        env_vars: HashMap::new(),
    };

    // Start the app using the LocalApp runtime
    let app = LocalApp::start(opts).await.expect("Failed to start app");

    // The status should be running
    let status = app.status().await.expect("Failed to get app status");
    assert!(status == Status::Running, "App should be running");

    let mut count_setup = 0;
    let mut count_stdout = 0;

    while let Some(output) = receiver.recv().await {
        debug!("Received output: {:?}", output.line);
        match output.channel {
            tower_runtime::Channel::Setup => {
                count_setup += 1;
            }
            tower_runtime::Channel::Program => {
                count_stdout += 1;
            }
        }
    }

    assert!(count_setup > 0, "There should be some setup output");
    assert!(count_stdout > 0, "should be more than one output");

    // check the status once more, should be done.
    let status = app.status().await.expect("Failed to get app status");
    assert!(status == Status::Exited, "App should be running");
}
