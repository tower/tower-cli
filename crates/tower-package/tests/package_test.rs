use tower_package::{Package, PackageSpec};
use tokio::fs::{copy, File};
use tokio::io::AsyncWriteExt;
use async_compression::tokio::write::GzipDecoder;
use tokio_tar::Archive;
use std::path::{Path, PathBuf};
use tmpdir::TmpDir;
use tokio_stream::*;

#[tokio::test]
async fn it_creates_package() {
    let tmp_dir = TmpDir::new("example").await.expect("Failed to create temp dir");
    create_test_file(tmp_dir.to_path_buf(), "main.py", "print('Hello, world!')").await;
    create_test_file(tmp_dir.to_path_buf(), "requirements.txt", "requests==2.25.1").await;

    let spec = PackageSpec {
        invoke: "main.py".to_string(),
        base_dir: tmp_dir.to_path_buf(),
        file_globs: vec!["*.py".to_string()],
    };

    let package = Package::build(spec).await.expect("Failed to build package");
    assert_eq!(package.manifest.version, 1);
    assert_eq!(package.manifest.invoke, "main.py");
    assert!(!package.path.as_os_str().is_empty());

    copy(PathBuf::from(&package.path), PathBuf::from("/tmp/package.tar.gz")).await.expect("Failed to copy package to /tmp/package.tar.gz");

    // Now we should crack open the file to make sure that we can find the relevant contents within
    // it.
    let file = File::open(package.path).await.expect("Failed to open package file");
    let gzip = GzipDecoder::new(file);
    let mut archive = Archive::new(gzip);
    let mut entries = archive.entries().expect("Failed to get entries from archive");

    let mut filenames = vec![];

    while let Some(file) = entries.next().await {
        let file = file.expect("Failed to get file from archive");
        let path = file.path().expect("Failed to get path from file");
        filenames.push(path.to_str().expect("Failed to convert path to string").to_string());
    }
}

async fn create_test_file(tempdir: PathBuf, path: &str, contents: &str) {
    let path = tempdir.join(path);
    let mut file = File::create(&path).await.expect("Failed to create file");
    file.write_all(contents.as_bytes()).await.expect("Failed to write content to file")
}
