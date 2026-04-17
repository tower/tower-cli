use std::collections::HashMap;
use std::path::PathBuf;

use tower_runtime::{local::LocalApp, App, StartOptions, Status};

use config::Towerfile;
use tmpdir::TmpDir;
use tower_package::{Manifest, Package, PackageSpec};
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
async fn test_running_hello_world_json_logs() {
    tower_telemetry::enable_logging(
        tower_telemetry::LogLevel::Debug,
        tower_telemetry::LogFormat::Json,
        tower_telemetry::LogDestination::Stdout,
    );

    debug!("Running 01-hello-world with JSON logs");
    let hello_world_dir = get_example_app_dir("01-hello-world");
    let package = build_package_from_dir(&hello_world_dir).await;
    let (sender, mut receiver) = unbounded_channel();

    // We need to create the package, which will load the app
    let opts = StartOptions {
        ctx: tower_telemetry::Context::new("runner-id".to_string()),
        package,
        output_sender: sender,
        cwd: None,
        environment: "local".to_string(),
        secrets: HashMap::new(),
        parameters: HashMap::new(),
        env_vars: HashMap::new(),
        cache_dir: Some(config::default_cache_dir()),
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
        ctx: tower_telemetry::Context::new("runner-id".to_string()),
        package,
        output_sender: sender,
        cwd: None,
        environment: "local".to_string(),
        secrets: HashMap::new(),
        parameters: HashMap::new(),
        env_vars: HashMap::new(),
        cache_dir: Some(config::default_cache_dir()),
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
        ctx: tower_telemetry::Context::new("runner-id".to_string()),
        package,
        output_sender: sender,
        cwd: None,
        environment: "local".to_string(),
        secrets: HashMap::new(),
        parameters: HashMap::new(),
        env_vars: HashMap::new(),
        cache_dir: Some(config::default_cache_dir()),
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
        ctx: tower_telemetry::Context::new("runner-id".to_string()),
        package,
        output_sender: sender,
        cwd: None,
        environment: "local".to_string(),
        secrets: HashMap::new(),
        parameters: HashMap::new(),
        env_vars: HashMap::new(),
        cache_dir: Some(config::default_cache_dir()),
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
async fn test_running_app_with_secret() {
    debug!("Running 04-app-with-secret");

    // We set a few environment variables that will be used to test the inherritance and override
    // behavior of child apps
    std::env::set_var(
        "PARENT_ENVIRONMENT_VARIABLE",
        "Something that should not get sent to the child",
    );
    std::env::set_var("OVERRIDDEN_ENVIRONMENT_VARIABLE", "The initial value");

    let app_dir = get_example_app_dir("04-app-with-secret");
    let package = build_package_from_dir(&app_dir).await;
    let (sender, mut receiver) = unbounded_channel();

    let mut secrets = HashMap::new();
    secrets.insert("MY_SECRET".to_string(), "It's in the sauce!".to_string());
    secrets.insert(
        "OVERRIDDEN_ENVIRONMENT_VARIABLE".to_string(),
        "I reset it!".to_string(),
    );

    // We need to create the package, which will load the app
    let opts = StartOptions {
        ctx: tower_telemetry::Context::new("runner-id".to_string()),
        package,
        output_sender: sender,
        cwd: None,
        environment: "local".to_string(),
        secrets: secrets,
        parameters: HashMap::new(),
        env_vars: HashMap::new(),

        // NOTE: No cache dir indicates that we want to run in protected mode.
        cache_dir: None,
    };

    // Start the app using the LocalApp runtime
    let app = LocalApp::start(opts).await.expect("Failed to start app");

    // The status should be running
    let status = app.status().await.expect("Failed to get app status");
    assert!(status == Status::Running, "App should be running");

    let mut count_setup = 0;
    let mut count_stdout = 0;

    while let Some(output) = receiver.recv().await {
        match output.channel {
            tower_runtime::Channel::Setup => {
                // We always have some setup lines to count on.
                count_setup += 1;
            }
            tower_runtime::Channel::Program => {
                if output.line.starts_with("The secret is:") {
                    // Indicate that we found the line.
                    count_stdout += 1;
                    assert!(output.line.ends_with("It's in the sauce!"));
                }

                if output
                    .line
                    .starts_with("The parent environment variable is:")
                {
                    // Indicate that we found this line too.
                    count_stdout += 1;
                    assert!(output.line.ends_with("default_value"));
                }

                if output
                    .line
                    .starts_with("The overridden environment variable is:")
                {
                    // Indicate that we found the last line.
                    count_stdout += 1;
                    assert!(output.line.ends_with("I reset it!"));
                }
            }
        }
    }

    assert!(count_setup > 0, "There should be some setup output");
    assert!(
        count_stdout == 3,
        "should be three output lines from the program, there were {}",
        count_stdout
    );

    // check the status once more, should be done.
    let status = app.status().await.expect("Failed to get app status");
    assert!(status == Status::Exited, "App should be running");
}

#[cfg(unix)]
#[tokio::test]
async fn test_setup_failure_reports_status_instead_of_waiter_closed() {
    // Regression: execute_local_app used to bubble up `?` errors (e.g. a failing
    // std::env::join_paths) without ever signalling the oneshot waiter, so
    // LocalApp::status() returned Err(WaiterClosed) and callers exited 1
    // silently. A setup failure must now surface as a terminal Status.
    let tmp = TmpDir::new("test-silent-setup")
        .await
        .expect("Failed to create tmp dir");
    let unpacked_path: PathBuf = tmp.as_ref().to_path_buf();

    // On Unix, std::env::join_paths rejects paths containing ':'. Feeding one
    // into manifest.import_paths causes the PYTHONPATH construction inside
    // execute_local_app to fail via `?` before any subprocess is spawned.
    let package = Package {
        tmp_dir: None,
        package_file_path: None,
        unpacked_path: Some(unpacked_path),
        manifest: Manifest {
            version: Some(1),
            invoke: "main.py".to_string(),
            parameters: vec![],
            schedule: None,
            import_paths: vec!["bad:path".to_string()],
            app_dir_name: "app".to_string(),
            modules_dir_name: "modules".to_string(),
            checksum: "".to_string(),
        },
    };

    let (sender, _receiver) = unbounded_channel();
    let opts = StartOptions {
        ctx: tower_telemetry::Context::new("runner-id".to_string()),
        package,
        output_sender: sender,
        cwd: None,
        environment: "local".to_string(),
        secrets: HashMap::new(),
        parameters: HashMap::new(),
        env_vars: HashMap::new(),
        cache_dir: Some(config::default_cache_dir()),
    };

    let app = LocalApp::start(opts).await.expect("Failed to start app");

    for _ in 0..20 {
        let status = app.status().await.expect("status should not be WaiterClosed");
        if status.is_terminal() {
            match status {
                Status::Crashed { code } => {
                    assert!(code < 0, "expected negative sentinel, got {}", code);
                    return;
                }
                other => panic!("expected Crashed, got {:?}", other),
            }
        }
        tokio::time::sleep(std::time::Duration::from_millis(25)).await;
    }

    panic!("status never reached a terminal state");
}

#[tokio::test]
async fn test_abort_on_dependency_installation_failure() {
    debug!("Running 05-broken-dependencies");
    // This test verifies that when dependency installation fails (uv sync returns non-zero),
    // the app correctly reports a Crashed status rather than continuing execution.
    let broken_deps_dir = get_example_app_dir("05-broken-dependencies");
    let package = build_package_from_dir(&broken_deps_dir).await;
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
        cache_dir: Some(config::default_cache_dir()),
    };

    // Start the app using the LocalApp runtime
    let app = LocalApp::start(opts).await.expect("Failed to start app");

    // Drain all output - we need to consume the channel for the app to complete
    while let Some(output) = receiver.recv().await {
        debug!("Received output: {:?}", output.line);
    }

    // The status should be Crashed since dependency installation failed
    let status = app.status().await.expect("Failed to get app status");
    match status {
        Status::Crashed { code } => {
            assert!(code != 0, "Exit code should be non-zero, got {}", code);
        }
        Status::Exited => {
            panic!("App should have crashed due to dependency installation failure, not exited successfully");
        }
        Status::Running => {
            panic!("App should not still be running");
        }
        Status::None => {
            panic!("App should have a status");
        }
        Status::Failed { .. } => {
            panic!("App should have crashed, not failed with a platform error");
        }
    }
}
