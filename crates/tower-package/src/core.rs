use flate2::{write::GzEncoder, Compression, GzBuilder};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use snafu::prelude::*;
use std::collections::HashMap;
use std::io::Write;
use std::path::{Component, Path};
use tar::{Builder, Header};

use crate::towerfile::{Parameter, Towerfile};

// Version History:
// 1 - Initial version
// 2 - Add app_dir, modules_dir, and checksum
// 3 - Change checksum algorithm to be cross-platform
pub const CURRENT_PACKAGE_VERSION: i32 = 3;

pub const MAX_PACKAGE_SIZE: u64 = 50 * 1024 * 1024;

#[derive(Debug, Snafu)]
pub enum Error {
    #[snafu(display("Invalid path"))]
    InvalidPath,

    #[snafu(display("Invalid Towerfile: {message}"))]
    InvalidTowerfile { message: String },

    #[snafu(display("No Towerfile was found in this directory"))]
    MissingTowerfile,

    #[snafu(display("Missing required app field `{field}` in Towerfile"))]
    MissingRequiredAppField { field: String },

    #[snafu(display("Serialization error: {source}"))]
    Serialization { source: serde_json::Error },

    #[snafu(display("IO error: {source}"))]
    Io { source: std::io::Error },
}

impl From<serde_json::Error> for Error {
    fn from(source: serde_json::Error) -> Self {
        Error::Serialization { source }
    }
}

impl From<std::io::Error> for Error {
    fn from(source: std::io::Error) -> Self {
        Error::Io { source }
    }
}

impl From<toml::de::Error> for Error {
    fn from(err: toml::de::Error) -> Self {
        Error::InvalidTowerfile {
            message: err.to_string(),
        }
    }
}

impl From<toml::ser::Error> for Error {
    fn from(err: toml::ser::Error) -> Self {
        Error::InvalidTowerfile {
            message: err.to_string(),
        }
    }
}

#[derive(Clone, Serialize, Deserialize)]
pub struct Manifest {
    pub version: Option<i32>,
    pub invoke: String,

    #[serde(default)]
    pub parameters: Vec<Parameter>,

    pub schedule: Option<String>,

    #[serde(default)]
    pub import_paths: Vec<String>,

    #[serde(default)]
    pub app_dir_name: String,

    #[serde(default)]
    pub modules_dir_name: String,

    #[serde(default)]
    pub checksum: String,
}

impl Manifest {
    pub fn from_json(data: &str) -> Result<Self, Error> {
        Ok(serde_json::from_str(data)?)
    }
}

#[derive(Debug, Clone)]
pub struct Entry {
    // archive_name is the POSIX-normalized path inside the tar (e.g. "app/main.py").
    pub archive_name: String,
    pub bytes: Vec<u8>,
}

#[derive(Debug)]
pub struct PackageInputs {
    // app_files have archive_name already rooted under "app/".
    pub app_files: Vec<Entry>,

    // module_files have archive_name already rooted under "modules/".
    pub module_files: Vec<Entry>,

    // towerfile_bytes is the sole source of invoke, parameters, and import_paths.
    pub towerfile_bytes: Vec<u8>,
}

pub struct BuiltPackage {
    pub bytes: Vec<u8>,
    pub manifest: Manifest,
}

// build_package produces a gzipped tar archive containing the given entries plus a generated
// MANIFEST and the original Towerfile. Entries are sorted by archive_name and tar headers are
// normalized (mtime/uid/gid zero, mode 0644) so the output is byte-deterministic for a given
// input.
pub fn build_package(inputs: PackageInputs) -> Result<BuiltPackage, Error> {
    let towerfile_str =
        std::str::from_utf8(&inputs.towerfile_bytes).map_err(|e| Error::InvalidTowerfile {
            message: format!("Towerfile is not valid UTF-8: {}", e),
        })?;
    let towerfile = Towerfile::from_toml(towerfile_str)?;

    let import_paths: Vec<String> = towerfile
        .app
        .import_paths
        .iter()
        .map(|p| format!("modules/{}", import_path_basename(&p.to_string_lossy())))
        .collect();

    let mut entries: Vec<Entry> =
        Vec::with_capacity(inputs.app_files.len() + inputs.module_files.len());
    entries.extend(inputs.app_files);
    entries.extend(inputs.module_files);
    entries.sort_by(|a, b| a.archive_name.cmp(&b.archive_name));

    let mut path_hashes: HashMap<String, String> = HashMap::with_capacity(entries.len());
    for entry in &entries {
        path_hashes.insert(
            entry.archive_name.clone(),
            compute_sha256_bytes(&entry.bytes),
        );
    }

    let manifest = Manifest {
        version: Some(CURRENT_PACKAGE_VERSION),
        invoke: towerfile.app.script,
        parameters: towerfile.parameters,
        schedule: None,
        import_paths,
        app_dir_name: "app".to_string(),
        modules_dir_name: "modules".to_string(),
        checksum: compute_sha256_package(&path_hashes),
    };

    let manifest_bytes = serde_json::to_vec(&manifest)?;

    let gz = GzBuilder::new()
        .mtime(0)
        .write(Vec::new(), Compression::default());
    let mut builder = Builder::new(gz);

    for entry in &entries {
        append_entry(&mut builder, &entry.archive_name, &entry.bytes)?;
    }
    append_entry(&mut builder, "MANIFEST", &manifest_bytes)?;
    append_entry(&mut builder, "Towerfile", &inputs.towerfile_bytes)?;

    let gz: GzEncoder<Vec<u8>> = builder.into_inner()?;
    let bytes = gz.finish()?;

    Ok(BuiltPackage { bytes, manifest })
}

fn append_entry<W: Write>(builder: &mut Builder<W>, name: &str, bytes: &[u8]) -> Result<(), Error> {
    let mut header = Header::new_gnu();
    header.set_size(bytes.len() as u64);
    header.set_mode(0o644);
    header.set_mtime(0);
    header.set_uid(0);
    header.set_gid(0);
    header.set_entry_type(tar::EntryType::Regular);
    header.set_cksum();
    builder.append_data(&mut header, name, bytes)?;
    Ok(())
}

// import_path_basename returns the final non-empty path component of an import path string.
// Accepts both forward- and back-slashes so Towerfiles authored on either OS parse the same.
fn import_path_basename(path: &str) -> &str {
    path.rsplit(|c| c == '/' || c == '\\')
        .find(|s| !s.is_empty() && *s != "." && *s != "..")
        .unwrap_or("")
}

// normalize_path converts a Path to a POSIX-style string with forward slashes, dropping root and
// Windows prefix components and refusing ".." navigation that escapes the path.
pub fn normalize_path(path: &Path) -> Result<String, Error> {
    let mut next = Vec::new();

    for component in path.components() {
        match component {
            Component::Prefix(_) | Component::RootDir => {}
            Component::CurDir => {}
            Component::ParentDir => {
                if !next.is_empty() {
                    return Err(Error::InvalidPath);
                }
            }
            Component::Normal(os_str) => {
                if let Some(s) = os_str.to_str() {
                    next.push(s.to_string());
                }
            }
        }
    }

    Ok(next.join("/"))
}

pub fn compute_sha256_bytes(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

// compute_sha256_package hashes the sorted (archive_name, file_hash) pairs to produce a stable
// fingerprint of the package contents.
pub fn compute_sha256_package(path_hashes: &HashMap<String, String>) -> String {
    let mut keys: Vec<&String> = path_hashes.keys().collect();
    keys.sort();

    let mut hasher = Sha256::new();
    for key in keys {
        hasher.update(format!("{}:{}", key, &path_hashes[key]).as_bytes());
    }
    format!("{:x}", hasher.finalize())
}

#[cfg(test)]
mod test {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn test_normalize_path() {
        let path = PathBuf::from(".")
            .join("some")
            .join("nested")
            .join("path")
            .join("to")
            .join("file.txt");
        assert_eq!(
            normalize_path(&path).unwrap(),
            "some/nested/path/to/file.txt"
        );
    }

    #[test]
    fn test_build_package_is_deterministic() {
        let inputs = || PackageInputs {
            app_files: vec![
                Entry {
                    archive_name: "app/b.py".into(),
                    bytes: b"b".to_vec(),
                },
                Entry {
                    archive_name: "app/a.py".into(),
                    bytes: b"a".to_vec(),
                },
            ],
            module_files: vec![],
            towerfile_bytes: b"[app]\nname = \"x\"\nscript = \"app/a.py\"\n".to_vec(),
        };

        let p1 = build_package(inputs()).unwrap();
        let p2 = build_package(inputs()).unwrap();
        assert_eq!(p1.bytes, p2.bytes);
        assert!(!p1.manifest.checksum.is_empty());
        assert_eq!(p1.manifest.invoke, "app/a.py");
    }

    #[test]
    fn test_derives_import_paths_from_towerfile() {
        let towerfile = br#"
[app]
name = "x"
script = "main.py"
import_paths = ["../shared", "libs/inner", "./weird/"]
"#;
        let out = build_package(PackageInputs {
            app_files: vec![],
            module_files: vec![],
            towerfile_bytes: towerfile.to_vec(),
        })
        .unwrap();
        assert_eq!(
            out.manifest.import_paths,
            vec!["modules/shared", "modules/inner", "modules/weird"]
        );
    }

    #[test]
    fn test_invalid_towerfile_is_rejected() {
        let result = build_package(PackageInputs {
            app_files: vec![],
            module_files: vec![],
            towerfile_bytes: b"not = = toml".to_vec(),
        });
        assert!(matches!(result, Err(Error::InvalidTowerfile { .. })));
    }
}
