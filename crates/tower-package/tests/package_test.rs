use std::collections::HashMap;
use std::path::PathBuf;

use tmpdir::TmpDir;
use tokio::{
    fs,
    fs::File,
    io::{BufReader, AsyncReadExt, AsyncWriteExt},
};
use tokio_stream::*;

use tokio_tar::Archive;
use tower_package::{Package, PackageSpec};

#[tokio::test]
async fn it_creates_package() {
    // We enable env_logger here as a way of debugging this test. There might be a way of doing
    // this globally...but I don't know what it is.
    let _ = env_logger::try_init();

    let tmp_dir = TmpDir::new("example").await.expect("Failed to create temp dir");
    create_test_file(tmp_dir.to_path_buf(), "main.py", "print('Hello, world!')").await;
    create_test_file(tmp_dir.to_path_buf(), "requirements.txt", "requests==2.25.1").await;

    let spec = PackageSpec {
        invoke: "main.py".to_string(),
        base_dir: tmp_dir.to_path_buf(),
        file_globs: vec!["*.py".to_string()],
        parameters: vec![],
    };

    let package = Package::build(spec).await.expect("Failed to build package");

    assert_eq!(package.manifest.version, Some(1));
    assert_eq!(package.manifest.invoke, "main.py");

    let package_file_path = package.package_file_path.clone().unwrap();
    assert!(!package_file_path.as_os_str().is_empty());

    let files = read_package_files(package).await;

    assert!(files.contains_key("main.py"), "files {:?} was missing key main.py", files);
    assert!(files.contains_key("MANIFEST"), "files {:?} was missing MANIFEST", files);
}

#[tokio::test]
async fn it_respects_complex_file_globs() {
    // We enable env_logger here as a way of debugging this test. There might be a way of doing
    // this globally...but I don't know what it is.
    let _ = env_logger::try_init();

    let tmp_dir = TmpDir::new("example").await.expect("Failed to create temp dir");
    create_test_file(tmp_dir.to_path_buf(), "main.py", "print('Hello, world!')").await;
    create_test_file(tmp_dir.to_path_buf(), "pack/__init__.py", "").await;
    create_test_file(tmp_dir.to_path_buf(), "pack/pack.py", "").await;

    let spec = PackageSpec {
        invoke: "main.py".to_string(),
        base_dir: tmp_dir.to_path_buf(),
        file_globs: vec![
            "*.py".to_string(),
            "**/*.py".to_string(),
        ],
        parameters: vec![],
    };

    let package = Package::build(spec).await.expect("Failed to build package");

    assert_eq!(package.manifest.version, Some(1));
    assert_eq!(package.manifest.invoke, "main.py");

    let package_file_path = package.package_file_path.clone().unwrap();
    assert!(!package_file_path.as_os_str().is_empty());

    let files = read_package_files(package).await;

    assert!(files.contains_key("main.py"), "files {:?} was missing key main.py", files);
    assert!(files.contains_key("MANIFEST"), "files {:?} was missing MANIFEST", files);
    assert!(files.contains_key("pack/__init__.py"), "files {:?} was missing pack/__init__.py", files);
}

// read_package_files reads the contents of a given package  and returns a map of the file paths to
// their contents as a collection of strings. Not useful for anything except for testing purposes.
async fn read_package_files(package: Package) -> HashMap<String, String> {
    // Now we should crack open the file to make sure that we can find the relevant contents within
    // it.
    let package_file_path = package.package_file_path.expect("Failed to get package file path");
    let file = File::open(package_file_path).await.expect("Failed to open package file");
    let buf = BufReader::new(file);
    // TODO: Re-enable this when we reintroduce gzip compression
    //let gzip = GzipDecoder::new(buf);
    //let mut archive = Archive::new(gzip);
    let mut archive = Archive::new(buf);
    let mut entries = archive.entries().expect("Failed to get entries from archive");

    let mut files = HashMap::new();

    while let Some(file) = entries.next().await {
        let mut file = file.expect("Failed to get file from archive");
        let contents = read_async_to_string(&mut file).await;
        let path = file.path().expect("Failed to get path from file");

        let path = path.to_str().expect("Failed to convert path to string").to_string();
        files.insert(path, contents);
    }
    
    files
}

async fn create_test_file(tempdir: PathBuf, path: &str, contents: &str) {
    let path = tempdir.join(path);

    if let Some(parent) = path.parent() {
        if !parent.exists() {
            fs::create_dir_all(&parent).await.expect("Failed to create file directory");
        }
    }

    log::debug!("creating test file at: {:?} with content {:?}", path, contents);
    let mut file = File::create(&path).await.expect("Failed to create file");
    file.write_all(contents.as_bytes()).await.expect("Failed to write content to file")
}

async fn read_async_to_string<R>(reader: &mut R) -> String
where
    R: AsyncReadExt + Unpin,
{
    let mut content = String::new();
    reader.read_to_string(&mut content).await.expect("Failed to read string from stream");
    content
}

