use tower_package::{Package, PackageSpec};
use std::io::Write;
use std::path::Path;
use std::fs::File;
use tempdir::TempDir;

#[tokio::test]
async fn it_creates_package() {
    let tmp_dir = TempDir::new("example").expect("Failed to create temp dir");
    create_test_file(tmp_dir.path(), "main.py", "print('Hello, world!')");
    create_test_file(tmp_dir.path(), "requirements.txt", "requests==2.25.1");

    let spec = PackageSpec {
        invoke: "main.py".to_string(),
        base_dir: tmp_dir.path().to_path_buf(),
        file_globs: vec!["*.py".to_string()],
    };

    let package = Package::build(spec).await.expect("Failed to build package");
    assert_eq!(package.manifest.version, 1);
    assert_eq!(package.manifest.invoke, "main.py");
    assert!(!package.path.as_os_str().is_empty())
}

fn create_test_file(tempdir: &Path, path: &str, contents: &str) {
    let path = tempdir.join(path);
    let mut file = File::create(&path).expect("Failed to create file");
    file.write_all(contents.as_bytes()).expect("Failed to write content to file")
}
