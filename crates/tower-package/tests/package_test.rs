use std::collections::HashMap;
use std::path::PathBuf;

use async_compression::tokio::bufread::GzipDecoder;
use tmpdir::TmpDir;
use tokio::{
    fs,
    fs::File,
    io::{AsyncReadExt, AsyncWriteExt, BufReader},
};
use tokio_stream::*;

use config::Towerfile;
use tokio_tar::Archive;
use tower_package::{Manifest, Package, PackageSpec, Parameter};
use tower_telemetry::debug;



#[tokio::test]
async fn it_creates_package() {
    let tmp_dir = TmpDir::new("example")
        .await
        .expect("Failed to create temp dir");
    create_test_file(tmp_dir.to_path_buf(), "Towerfile", "").await;
    create_test_file(tmp_dir.to_path_buf(), "main.py", "print('Hello, world!')").await;
    create_test_file(
        tmp_dir.to_path_buf(),
        "requirements.txt",
        "requests==2.25.1",
    )
    .await;

    let spec = PackageSpec {
        invoke: "main.py".to_string(),
        base_dir: tmp_dir.to_path_buf(),
        towerfile_path: tmp_dir.to_path_buf().join("Towerfile").to_path_buf(),
        file_globs: vec!["*.py".to_string()],
        parameters: vec![],
        schedule: None,
        import_paths: vec![],
    };

    let package = Package::build(spec).await.expect("Failed to build package");

    assert_eq!(package.manifest.version, Some(3));
    assert_eq!(package.manifest.invoke, "main.py");

    let package_file_path = package.package_file_path.clone().unwrap();
    assert!(!package_file_path.as_os_str().is_empty());

    let files = read_package_files(package).await;

    assert!(
        files.contains_key("app/main.py"),
        "files {:?} was missing key main.py",
        files
    );
    assert!(
        files.contains_key("MANIFEST"),
        "files {:?} was missing MANIFEST",
        files
    );
}

#[tokio::test]
async fn it_respects_complex_file_globs() {
    let tmp_dir = TmpDir::new("example")
        .await
        .expect("Failed to create temp dir");
    create_test_file(tmp_dir.to_path_buf(), "Towerfile", "").await;
    create_test_file(tmp_dir.to_path_buf(), "main.py", "print('Hello, world!')").await;
    create_test_file(tmp_dir.to_path_buf(), "pack/__init__.py", "").await;
    create_test_file(tmp_dir.to_path_buf(), "pack/pack.py", "").await;

    let spec = PackageSpec {
        invoke: "main.py".to_string(),
        base_dir: tmp_dir.to_path_buf(),
        towerfile_path: tmp_dir.to_path_buf().join("Towerfile").to_path_buf(),
        file_globs: vec!["*.py".to_string(), "**/*.py".to_string()],
        parameters: vec![],
        schedule: Some("every 1 minute".to_string()),
        import_paths: vec![],
    };

    let package = Package::build(spec).await.expect("Failed to build package");

    assert_eq!(package.manifest.version, Some(3));
    assert_eq!(package.manifest.invoke, "main.py");
    assert_eq!(
        package.manifest.schedule,
        Some("every 1 minute".to_string())
    );

    let package_file_path = package.package_file_path.clone().unwrap();
    assert!(!package_file_path.as_os_str().is_empty());

    let files = read_package_files(package).await;

    assert!(
        files.contains_key("app/main.py"),
        "files {:?} was missing key main.py",
        files
    );
    assert!(
        files.contains_key("MANIFEST"),
        "files {:?} was missing MANIFEST",
        files
    );
    assert!(
        files.contains_key("app/pack/__init__.py"),
        "files {:?} was missing pack/__init__.py",
        files
    );
}

#[tokio::test]
async fn it_packages_all_files_by_default() {
    let tmp_dir = TmpDir::new("all-files-by-default")
        .await
        .expect("Failed to create temp dir");
    create_test_file(tmp_dir.to_path_buf(), "Towerfile", "").await;
    create_test_file(tmp_dir.to_path_buf(), "main.py", "print('Hello, world!')").await;
    create_test_file(tmp_dir.to_path_buf(), "pack/__init__.py", "").await;
    create_test_file(tmp_dir.to_path_buf(), "pack/pack.py", "").await;

    let spec = PackageSpec {
        invoke: "main.py".to_string(),
        base_dir: tmp_dir.to_path_buf(),
        towerfile_path: tmp_dir.to_path_buf().join("Towerfile").to_path_buf(),
        file_globs: vec![],
        parameters: vec![],
        schedule: Some("every 1 minute".to_string()),
        import_paths: vec![],
    };

    let package = Package::build(spec).await.expect("Failed to build package");

    let package_file_path = package.package_file_path.clone().unwrap();
    assert!(!package_file_path.as_os_str().is_empty());

    let files = read_package_files(package).await;
    assert!(
        files.contains_key("MANIFEST"),
        "files {:?} was missing MANIFEST",
        files
    );
    assert!(
        files.contains_key("app/main.py"),
        "files {:?} was missing key main.py",
        files
    );
    assert!(
        files.contains_key("app/pack/__init__.py"),
        "files {:?} was missing pack/__init__.py",
        files
    );
    assert!(
        files.contains_key("app/pack/pack.py"),
        "files {:?} was missing pack/__init__.py",
        files
    );
}

#[tokio::test]
async fn it_packages_directory_contents() {
    let tmp_dir = TmpDir::new("directory-contents")
        .await
        .expect("Failed to create temp dir");
    create_test_file(tmp_dir.to_path_buf(), "Towerfile", "").await;
    create_test_file(tmp_dir.to_path_buf(), "main.py", "print('Hello, world!')").await;
    create_test_file(tmp_dir.to_path_buf(), "pack/__init__.py", "").await;
    create_test_file(tmp_dir.to_path_buf(), "pack/pack.py", "").await;
    create_test_file(tmp_dir.to_path_buf(), "pack/submodule/pack.py", "").await;

    let spec = PackageSpec {
        invoke: "main.py".to_string(),
        base_dir: tmp_dir.to_path_buf(),
        towerfile_path: tmp_dir.to_path_buf().join("Towerfile").to_path_buf(),
        file_globs: vec!["main.py".to_string(), "pack".to_string()],
        parameters: vec![],
        schedule: Some("every 1 minute".to_string()),
        import_paths: vec![],
    };

    let package = Package::build(spec).await.expect("Failed to build package");

    let package_file_path = package.package_file_path.clone().unwrap();
    assert!(!package_file_path.as_os_str().is_empty());

    let files = read_package_files(package).await;
    assert!(
        files.contains_key("MANIFEST"),
        "files {:?} was missing MANIFEST",
        files
    );
    assert!(
        files.contains_key("app/main.py"),
        "files {:?} was missing key main.py",
        files
    );
    assert!(
        files.contains_key("app/pack/__init__.py"),
        "files {:?} was missing pack/__init__.py",
        files
    );
    assert!(
        files.contains_key("app/pack/pack.py"),
        "files {:?} was missing pack/__init__.py",
        files
    );
    assert!(
        files.contains_key("app/pack/submodule/pack.py"),
        "files {:?} was missing pack/submodule/pack.py",
        files
    );
}

#[tokio::test]
async fn it_packages_import_paths() {
    let tmp_dir = TmpDir::new("example")
        .await
        .expect("Failed to create temp dir");
    create_test_file(tmp_dir.to_path_buf(), "app/Towerfile", "").await;
    create_test_file(
        tmp_dir.to_path_buf(),
        "app/main.py",
        "print('Hello, world!')",
    )
    .await;
    create_test_file(tmp_dir.to_path_buf(), "shared/module/__init__.py", "").await;
    create_test_file(tmp_dir.to_path_buf(), "shared/module/test.py", "").await;

    let spec = PackageSpec {
        invoke: "main.py".to_string(),
        base_dir: tmp_dir.to_path_buf().join("app"),
        towerfile_path: tmp_dir
            .to_path_buf()
            .join("app")
            .join("Towerfile")
            .to_path_buf(),
        file_globs: vec!["**/*.py".to_string()],
        parameters: vec![],
        schedule: None,
        import_paths: vec!["../shared".to_string()],
    };

    let package = Package::build(spec).await.expect("Failed to build package");

    assert_eq!(package.manifest.version, Some(3));
    assert_eq!(package.manifest.invoke, "main.py");
    assert_eq!(package.manifest.schedule, None);

    let files = read_package_files(package).await;

    assert!(
        files.contains_key("MANIFEST"),
        "files {:?} was missing MANIFEST",
        files
    );
    assert!(
        files.contains_key("app/main.py"),
        "files {:?} was missing key app/main.py",
        files
    );
    assert!(
        files.contains_key("modules/shared/module/__init__.py"),
        "files {:?} was missing shared/module/__init__.py",
        files
    );
    assert!(
        files.contains_key("modules/shared/module/test.py"),
        "files {:?} was missing shared/module/test.py",
        files
    );

    // Let's decode the manifest and make sure import paths are set correctly.
    let manifest = Manifest::from_json(files.get("MANIFEST").unwrap())
        .expect("Manifest was not valid JSON");

    // Archive paths are always normalized to forward slashes regardless of OS.
    assert!(
        manifest.import_paths.contains(&"modules/shared".to_string()),
        "Import paths {:?} did not contain expected path",
        manifest.import_paths
    );

    // We should have some integrity check here too.
    assert!(
        !manifest.checksum.is_empty(),
        "Manifest integrity check was not set"
    );
}

#[tokio::test]
async fn it_packages_import_paths_nested_within_base_dir() {
    // When an import path lives inside base_dir (e.g. libs/shared), module files must
    // still be placed under modules/<dir_name>/... (not modules/libs/shared/...) so that
    // the package structure matches the manifest's PYTHONPATH entry.
    let tmp_dir = TmpDir::new("nested-import")
        .await
        .expect("Failed to create temp dir");
    create_test_file(tmp_dir.to_path_buf(), "Towerfile", "").await;
    create_test_file(tmp_dir.to_path_buf(), "main.py", "print('Hello')").await;
    create_test_file(tmp_dir.to_path_buf(), "libs/shared/__init__.py", "").await;
    create_test_file(tmp_dir.to_path_buf(), "libs/shared/util.py", "# util").await;

    let spec = PackageSpec {
        invoke: "main.py".to_string(),
        base_dir: tmp_dir.to_path_buf(),
        towerfile_path: tmp_dir.to_path_buf().join("Towerfile"),
        file_globs: vec!["main.py".to_string()],
        parameters: vec![],
        schedule: None,
        import_paths: vec!["libs/shared".to_string()],
    };

    let package = Package::build(spec).await.expect("Failed to build package");
    let files = read_package_files(package).await;

    // Module files should be under modules/shared/..., NOT modules/libs/shared/...
    // Archive paths are always normalized to forward slashes regardless of OS.
    assert!(
        files.contains_key("modules/shared/__init__.py"),
        "files {:?} was missing modules/shared/__init__.py",
        files
    );
    assert!(
        files.contains_key("modules/shared/util.py"),
        "files {:?} was missing modules/shared/util.py",
        files
    );
    assert!(
        !files.contains_key("modules/libs/shared/__init__.py"),
        "files {:?} should NOT contain modules/libs/shared/__init__.py",
        files
    );

    // Verify the manifest import_paths entry matches the actual package structure.
    let manifest = Manifest::from_json(files.get("MANIFEST").unwrap())
        .expect("Manifest was not valid JSON");

    assert!(
        manifest.import_paths.contains(&"modules/shared".to_string()),
        "Import paths {:?} did not contain expected path modules/shared",
        manifest.import_paths
    );
}

#[tokio::test]
async fn it_excludes_various_content_that_should_not_be_there() {
    let tmp_dir = TmpDir::new("example")
        .await
        .expect("Failed to create temp dir");
    create_test_file(tmp_dir.to_path_buf(), "Towerfile", "").await;
    create_test_file(tmp_dir.to_path_buf(), "main.py", "print('Hello, world!')").await;
    create_test_file(
        tmp_dir.to_path_buf(),
        "main.py.pyc",
        "print('Hello, world!')",
    )
    .await;
    create_test_file(
        tmp_dir.to_path_buf(),
        "some-app/test.py",
        "print('Hello, world!')",
    )
    .await;
    create_test_file(
        tmp_dir.to_path_buf(),
        "some-app/__pycache__/test.pyc",
        "print('Hello, world!')",
    )
    .await;
    create_test_file(tmp_dir.to_path_buf(), ".git/some-file", "").await;

    let spec = PackageSpec {
        invoke: "main.py".to_string(),
        base_dir: tmp_dir.to_path_buf(),
        towerfile_path: tmp_dir.to_path_buf().join("Towerfile").to_path_buf(),
        file_globs: vec![],
        parameters: vec![],
        schedule: None,
        import_paths: vec![],
    };

    let package = Package::build(spec).await.expect("Failed to build package");
    let files = read_package_files(package).await;

    assert!(
        !files.contains_key(".git/some-file"),
        "files {:?} had .git directory",
        files
    );
    assert!(
        !files.contains_key("some-app/__pycache__/test.pyc"),
        "files {:?} contained a .pyc",
        files
    );
    assert!(
        !files.contains_key("main.py.pyc"),
        "files {:?} contained a .pyc",
        files
    );
}

#[tokio::test]
async fn building_package_spec_from_towerfile() {
    let toml = r#"
        [app]
        name = "test"
        script = "./script.py"
        source = ["*.py"]
        schedule = "0 0 * * *"
    "#;

    let mut towerfile = Towerfile::from_toml(toml).unwrap();

    // we have to set the file_path on the Towerfile otherwise we can't build a package spec from
    // it.
    towerfile.file_path = PathBuf::from("./Towerfile");

    let spec = PackageSpec::from_towerfile(&towerfile);

    assert_eq!(spec.invoke, "./script.py");
    assert_eq!(spec.schedule, Some("0 0 * * *".to_string()));
}

#[tokio::test]
async fn it_includes_subapp_towerfiles_but_excludes_root_towerfile() {
    // When a project contains sub-apps with their own Towerfiles, only the root Towerfile (the
    // one used to build the package) should be excluded. Towerfiles belonging to sub-apps must
    // be included so those apps can function correctly.
    let tmp_dir = TmpDir::new("subapp-towerfile")
        .await
        .expect("Failed to create temp dir");

    // Root app files
    create_test_file(tmp_dir.to_path_buf(), "Towerfile", "[app]\nname = \"root\"").await;
    create_test_file(tmp_dir.to_path_buf(), "main.py", "print('Hello, world!')").await;

    // Sub-app with its own Towerfile
    create_test_file(tmp_dir.to_path_buf(), "subapp/Towerfile", "[app]\nname = \"subapp\"").await;
    create_test_file(tmp_dir.to_path_buf(), "subapp/main.py", "print('subapp')").await;

    let spec = PackageSpec {
        invoke: "main.py".to_string(),
        base_dir: tmp_dir.to_path_buf(),
        towerfile_path: tmp_dir.to_path_buf().join("Towerfile"),
        file_globs: vec![],
        parameters: vec![],
        schedule: None,
        import_paths: vec![],
    };

    let package = Package::build(spec).await.expect("Failed to build package");
    let files = read_package_files(package).await;

    // Root Towerfile should NOT be in the app directory (it's added separately as "Towerfile")
    assert!(
        !files.contains_key("app/Towerfile"),
        "files {:?} should not contain the root Towerfile under app/",
        files
    );

    // The root Towerfile is still bundled at the top level for reference
    assert!(
        files.contains_key("Towerfile"),
        "files {:?} should contain the root Towerfile at the top level",
        files
    );

    // Sub-app's Towerfile MUST be included
    assert!(
        files.contains_key("app/subapp/Towerfile"),
        "files {:?} should contain the sub-app Towerfile",
        files
    );

    // Other files should be present
    assert!(
        files.contains_key("app/main.py"),
        "files {:?} was missing main.py",
        files
    );
    assert!(
        files.contains_key("app/subapp/main.py"),
        "files {:?} was missing subapp/main.py",
        files
    );
}

#[tokio::test]
async fn it_includes_hidden_parameters_in_manifest() {
    let tmp_dir = TmpDir::new("hidden-params")
        .await
        .expect("Failed to create temp dir");
    create_test_file(tmp_dir.to_path_buf(), "Towerfile", "").await;
    create_test_file(tmp_dir.to_path_buf(), "main.py", "print('Hello, world!')").await;

    let spec = PackageSpec {
        invoke: "main.py".to_string(),
        base_dir: tmp_dir.to_path_buf(),
        towerfile_path: tmp_dir.to_path_buf().join("Towerfile").to_path_buf(),
        file_globs: vec!["*.py".to_string()],
        parameters: vec![
            Parameter {
                name: "visible_param".to_string(),
                description: Some("A visible parameter".to_string()),
                default: "".to_string(),
                hidden: false,
            },
            Parameter {
                name: "hidden_param".to_string(),
                description: Some("A hidden parameter".to_string()),
                default: "secret".to_string(),
                hidden: true,
            },
        ],
        schedule: None,
        import_paths: vec![],
    };

    let package = Package::build(spec).await.expect("Failed to build package");
    let files = read_package_files(package).await;

    let manifest = Manifest::from_json(files.get("MANIFEST").unwrap())
        .expect("Manifest was not valid JSON");

    assert_eq!(manifest.parameters.len(), 2);

    let visible = manifest.parameters.iter().find(|p| p.name == "visible_param").unwrap();
    assert!(!visible.hidden, "visible_param should not be hidden");

    let hidden = manifest.parameters.iter().find(|p| p.name == "hidden_param").unwrap();
    assert!(hidden.hidden, "hidden_param should be hidden");
    assert_eq!(hidden.default, "secret");
}

// read_package_files reads the contents of a given package  and returns a map of the file paths to
// their contents as a collection of strings. Not useful for anything except for testing purposes.
async fn read_package_files(package: Package) -> HashMap<String, String> {
    // Now we should crack open the file to make sure that we can find the relevant contents within
    // it.
    let package_file_path = package
        .package_file_path
        .expect("Failed to get package file path");
    let file = File::open(package_file_path)
        .await
        .expect("Failed to open package file");
    let buf = BufReader::new(file);

    // TODO: Re-enable this when we reintroduce gzip compression
    let gzip = GzipDecoder::new(buf);
    let mut archive = Archive::new(gzip);
    let mut entries = archive
        .entries()
        .expect("Failed to get entries from archive");

    let mut files = HashMap::new();

    while let Some(file) = entries.next().await {
        let mut file = file.expect("Failed to get file from archive");
        let contents = read_async_to_string(&mut file).await;
        let path = file.path().expect("Failed to get path from file");

        let path = path
            .to_str()
            .expect("Failed to convert path to string")
            .to_string();
        files.insert(path, contents);
    }

    files
}

async fn create_test_file(tempdir: PathBuf, path: &str, contents: &str) {
    let path = tempdir.join(path);

    if let Some(parent) = path.parent() {
        if !parent.exists() {
            fs::create_dir_all(&parent)
                .await
                .expect("Failed to create file directory");
        }
    }

    debug!(
        "creating test file at: {:?} with content {:?}",
        path, contents
    );
    let mut file = File::create(&path).await.expect("Failed to create file");
    file.write_all(contents.as_bytes())
        .await
        .expect("Failed to write content to file")
}

async fn read_async_to_string<R>(reader: &mut R) -> String
where
    R: AsyncReadExt + Unpin,
{
    let mut content = String::new();
    reader
        .read_to_string(&mut content)
        .await
        .expect("Failed to read string from stream");
    content
}
