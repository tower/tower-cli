use config::Towerfile;
use glob::glob;
use std::collections::{HashMap, VecDeque};
use std::path::{Path, PathBuf};
use std::pin::Pin;
use tmpdir::TmpDir;
use tokio::{
    fs::File,
    io::{AsyncRead, AsyncReadExt, AsyncWriteExt, BufReader},
};
use tokio_tar::Archive;

use async_compression::tokio::bufread::GzipDecoder;

use tower_telemetry::debug;

use crate::core::{
    build_package, compute_sha256_bytes, normalize_path, Entry, Manifest, PackageInputs,
    Parameter, CURRENT_PACKAGE_VERSION,
};
use crate::error::Error;

// PackageSpec describes how to build a package.
#[derive(Debug)]
pub struct PackageSpec {
    // towerfile_path is the path to the Towerfile that was used to build this package.
    pub towerfile_path: PathBuf,

    // invoke is the file to invoke when the package is run.
    pub invoke: String,

    // base_dir is the directory where the package is located.
    pub base_dir: PathBuf,

    // file_globs is a list of globs that match the files in the package.
    pub file_globs: Vec<String>,

    // parameters are the parameters to use for this app.
    pub parameters: Vec<Parameter>,

    pub import_paths: Vec<String>,
}

impl PackageSpec {
    pub fn from_towerfile(towerfile: &Towerfile) -> Self {
        debug!("creating package spec from towerfile: {:?}", towerfile);
        let towerfile_path = towerfile.file_path.clone();
        let base_dir = towerfile_path
            .parent()
            .unwrap_or_else(|| Path::new("."))
            .to_path_buf();

        // We need to turn these (validated) paths into something taht we can use at runtime.
        let import_paths = towerfile
            .app
            .import_paths
            .iter()
            .map(|p| p.to_string_lossy().to_string())
            .collect();

        let parameters = towerfile
            .parameters
            .iter()
            .map(|p| Parameter {
                name: p.name.clone(),
                description: Some(p.description.clone()),
                default: p.default.clone(),
                hidden: p.hidden,
            })
            .collect();

        Self {
            towerfile_path,
            base_dir,
            import_paths,
            invoke: towerfile.app.script.clone(),
            file_globs: towerfile.app.source.clone(),
            parameters,
        }
    }
}

pub struct Package {
    pub manifest: Manifest,

    // tmp_dir is used to keep the package directory around occasionally so the directory doesn't
    // get deleted out from under the application.
    pub tmp_dir: Option<TmpDir>,

    // package_file_path is path to the packed file on disk.
    pub package_file_path: Option<PathBuf>,

    // unpacked_path is the path to the unpackaged package on disk.
    pub unpacked_path: Option<PathBuf>,
}

impl Package {
    pub fn default() -> Self {
        Self {
            tmp_dir: None,
            package_file_path: None,
            unpacked_path: None,
            manifest: Manifest {
                version: Some(CURRENT_PACKAGE_VERSION),
                invoke: "".to_string(),
                parameters: vec![],
                schedule: None,
                import_paths: vec![],
                app_dir_name: "app".to_string(),
                modules_dir_name: "modules".to_string(),
                checksum: "".to_string(),
            },
        }
    }

    pub async fn from_unpacked_path(path: PathBuf) -> Result<Self, Error> {
        let manifest_path = path.join("MANIFEST");
        let mut file = File::open(&manifest_path).await?;
        let mut contents = String::new();
        file.read_to_string(&mut contents).await?;
        let manifest = Manifest::from_json(&contents)?;

        Ok(Self {
            tmp_dir: None,
            package_file_path: None,
            unpacked_path: Some(path),
            manifest,
        })
    }

    // build creates a new package from a PackageSpec. PackageSpec is typically composed of fields
    // copied from the Towerfile. The most important thing to know is that the collection of file
    // globs to include in the package.
    //
    // The underlying package is just a TAR file with a special `MANIFEST` file that has also been
    // GZip'd.
    pub async fn build(spec: PackageSpec) -> Result<Self, Error> {
        debug!("building package from spec: {:?}", spec);

        // we canonicalize this because we want to treat all paths in the same keyspace more or
        // less.
        let base_dir = spec.base_dir.canonicalize()?;

        // Canonicalize import paths upfront so the resolver can whitelist files within them.
        let canonical_import_paths: Vec<PathBuf> = spec
            .import_paths
            .iter()
            .map(|p| base_dir.join(p).canonicalize())
            .collect::<Result<Vec<_>, _>>()?;

        let resolver = FileResolver::new(base_dir.clone(), canonical_import_paths.clone());

        // If the user didn't specify anything here we'll package everything under this directory.
        let mut file_globs = spec.file_globs.clone();
        if file_globs.is_empty() {
            debug!("no source files specified. using default paths.");
            file_globs.push("./**/*".to_string());
        }

        // Resolve app file paths: physical -> logical (relative to base_dir or import parent).
        let mut app_file_paths: HashMap<PathBuf, PathBuf> = HashMap::new();
        for file_glob in file_globs {
            let path = base_dir.join(file_glob);
            resolver.resolve_glob(path, &mut app_file_paths).await?;
        }

        let app_dir = PathBuf::from("app");
        let mut app_files: Vec<Entry> = Vec::with_capacity(app_file_paths.len());
        for (physical_path, logical_path) in app_file_paths {
            let archive_path = app_dir.join(logical_path);
            let archive_name = normalize_path(&archive_path)?;
            let bytes = tokio::fs::read(&physical_path).await?;
            app_files.push(Entry { archive_name, bytes });
        }

        // Resolve modules and compute their manifest import_paths entries.
        let module_dir = PathBuf::from("modules");
        let mut module_files: Vec<Entry> = Vec::new();
        let mut import_paths: Vec<String> = Vec::new();

        for import_path in &canonical_import_paths {
            let mut module_file_paths: HashMap<PathBuf, PathBuf> = HashMap::new();
            resolver.resolve_path(import_path, &mut module_file_paths).await;

            // Logical paths are relative to the import path's parent so the archive layout
            // matches the manifest entry (modules/<dir>/... not modules/<parent>/<dir>/...).
            let import_parent = import_path.parent().unwrap_or(import_path.as_path());

            let import_name = import_path.file_name().unwrap();
            let manifest_import = module_dir.join(import_name);
            import_paths.push(normalize_path(&manifest_import)?);

            for (physical_path, _) in module_file_paths {
                let logical_path = match physical_path.strip_prefix(import_parent) {
                    Ok(p) => module_dir.join(p),
                    Err(_) => continue,
                };
                let archive_name = normalize_path(&logical_path)?;
                let bytes = tokio::fs::read(&physical_path).await?;
                module_files.push(Entry { archive_name, bytes });
            }
        }

        let towerfile_bytes = tokio::fs::read(&spec.towerfile_path).await?;

        let inputs = PackageInputs {
            app_files,
            module_files,
            towerfile_bytes,
            invoke: spec.invoke,
            parameters: spec.parameters,
            import_paths,
        };

        let built = build_package(inputs)?;

        let tmp_dir = TmpDir::new("tower-package").await?;
        let package_path = tmp_dir.to_path_buf().join("package.tar");
        debug!("writing package to: {:?}", package_path);

        let mut file = File::create(&package_path).await?;
        file.write_all(&built.bytes).await?;
        file.shutdown().await?;

        Ok(Self {
            manifest: built.manifest,
            unpacked_path: None,
            tmp_dir: Some(tmp_dir),
            package_file_path: Some(package_path),
        })
    }

    /// unpack is the primary interface in to unpacking a package. It will allocate a temporary
    /// directory if one isn't already allocated and unpack the package contents into that location.
    pub async fn unpack(&mut self) -> Result<(), Error> {
        // If there's already a tmp_dir allocated to this package, then we'll use that. Otherwise,
        // we allocate one and store it on this package for later use.
        let path = if let Some(tmp_dir) = self.tmp_dir.as_ref() {
            tmp_dir.to_path_buf()
        } else {
            let tmp_dir = TmpDir::new("tower-package").await?;
            let path = tmp_dir.to_path_buf();
            self.tmp_dir = Some(tmp_dir);
            path
        };

        // self.package_file_path should be set otherwise this is a bug.
        let package_path = self.package_file_path.clone().unwrap();
        unpack_archive(&package_path, &path).await?;
        self.unpacked_path = Some(path);
        Ok(())
    }
}

fn extract_glob_path(path: PathBuf) -> String {
    let str = path.to_str().unwrap();

    #[cfg(windows)]
    {
        // This is a nasty hack to get around a limitation in the `glob` crate on Windows. There's
        // a (documented) bug that prevents it from globbing on canonicalized paths.
        //
        // See https://github.com/rust-lang/glob/issues/132
        str.strip_prefix(r"\\?\").ok_or(str).unwrap().to_string()
    }

    #[cfg(not(windows))]
    {
        str.to_string()
    }
}

/// Check if a file is a valid gzip file by attempting to decompress it
async fn is_valid_gzip<P: AsRef<Path>>(path: P) -> bool {
    let file = match File::open(&path).await {
        Ok(file) => file,
        Err(_) => return false,
    };

    let reader = BufReader::new(file);
    let mut decoder = GzipDecoder::new(reader);

    // Try to read a small amount of data. If we can, then we assume that it's a valid gzip file.
    // Othwewise, it's not gzipped I suppose?
    let mut buffer = [0u8; 1024];
    decoder.read(&mut buffer).await.is_ok()
}

async fn unpack_archive<P: AsRef<Path>>(
    package_path: P,
    output_path: P,
) -> Result<(), std::io::Error> {
    let reader: Pin<Box<dyn AsyncRead + Send + Unpin>> = if is_valid_gzip(&package_path).await {
        // gor gzipped files
        let file = File::open(&package_path).await?;
        let buf_reader = BufReader::new(file);
        let decoder = GzipDecoder::new(buf_reader);
        Box::pin(decoder)
    } else {
        // For regular files
        let file = File::open(&package_path).await?;
        Box::pin(file)
    };

    // Create and unpack the archive
    let mut archive = Archive::new(reader);
    archive.unpack(output_path).await?;

    Ok(())
}

fn is_in_dir(p: &PathBuf, dir: &str) -> bool {
    let mut comps = p.components();
    comps.any(|comp| {
        if let std::path::Component::Normal(name) = comp {
            name == dir
        } else {
            false
        }
    })
}

fn is_file(p: &PathBuf, name: &str) -> bool {
    if let Some(file_name) = p.file_name() {
        file_name == name
    } else {
        false
    }
}

struct FileResolver {
    // base_dir is the directory from which logical paths are computed.
    base_dir: PathBuf,

    // import_paths are canonicalized paths to imported directories. Files within these directories
    // are also allowed, with logical paths computed relative to each import path's parent.
    import_paths: Vec<PathBuf>,
}

impl FileResolver {
    fn new(base_dir: PathBuf, import_paths: Vec<PathBuf>) -> Self {
        Self {
            base_dir,
            import_paths,
        }
    }

    fn should_ignore(&self, p: &PathBuf) -> bool {
        // Ignore anything that is compiled python
        if p.extension().map(|ext| ext == "pyc").unwrap_or(false) {
            return true;
        }

        // Only exclude the root Towerfile (base_dir/Towerfile). Since base_dir is already
        // canonicalized, we can derive this path directly. Towerfiles in sub-directories are
        // legitimate app content and must be preserved.
        if p == &self.base_dir.join("Towerfile") {
            return true;
        }

        // Ignore a .gitignore file
        if is_file(p, ".gitignore") {
            return true;
        }

        // Remove anything thats __pycache__
        if is_in_dir(p, "__pycache__") {
            return true;
        }

        // Ignore anything that lives within a .git directory
        if is_in_dir(p, ".git") {
            return true;
        }

        // Ignore anything that's in a virtualenv, too
        if is_in_dir(p, ".venv") {
            return true;
        }

        false
    }

    fn logical_path<'a>(&self, physical_path: &'a Path) -> Option<&'a Path> {
        if let Ok(p) = physical_path.strip_prefix(&self.base_dir) {
            return Some(p);
        }

        // Try each import path's parent as a prefix. This allows files within import paths
        // (which may live outside base_dir) to be resolved with logical paths that preserve
        // the import directory name (e.g. "shared_lib/foo.py").
        for import_path in &self.import_paths {
            if let Some(parent) = import_path.parent() {
                if let Ok(p) = physical_path.strip_prefix(parent) {
                    return Some(p);
                }
            }
        }

        None
    }

    async fn resolve_glob(
        &self,
        path: PathBuf,
        file_paths: &mut HashMap<PathBuf, PathBuf>,
    ) -> Result<(), Error> {
        let path_str = extract_glob_path(path);
        debug!("resolving glob pattern: {}", path_str);

        let entries = glob(&path_str).map_err(|e| Error::InvalidGlob {
            message: format!("{}: {}", path_str, e),
        })?;

        for entry in entries {
            match entry {
                Ok(path) => self.resolve_path(&path, file_paths).await,
                Err(e) => {
                    debug!("skipping glob entry: {}", e);
                }
            }
        }

        Ok(())
    }

    async fn resolve_path(&self, path: &PathBuf, file_paths: &mut HashMap<PathBuf, PathBuf>) {
        let mut queue = VecDeque::new();
        queue.push_back(path.to_path_buf());

        while let Some(current_path) = queue.pop_front() {
            let physical_path = match current_path.canonicalize() {
                Ok(p) => p,
                Err(e) => {
                    debug!(" - skipping path {}: {}", current_path.display(), e);
                    continue;
                }
            };

            if physical_path.is_dir() {
                let mut entries = tokio::fs::read_dir(&physical_path).await.unwrap();

                while let Some(entry) = entries.next_entry().await.unwrap() {
                    queue.push_back(entry.path());
                }
            } else {
                if !self.should_ignore(&physical_path) {
                    let cp = physical_path.clone();
                    match self.logical_path(&cp) {
                        None => {
                            debug!(
                                " - skipping file {}: not in base directory {}: ...",
                                physical_path.display(),
                                self.base_dir.display(),
                            );
                            continue;
                        }
                        Some(logical_path) => {
                            debug!(
                                " - resolved path {} to logical path {}",
                                physical_path.display(),
                                logical_path.display()
                            );
                            file_paths.insert(physical_path, logical_path.to_path_buf());
                        }
                    }
                }
            }
        }
    }
}

pub async fn compute_sha256_file(file_path: &PathBuf) -> Result<String, Error> {
    let bytes = tokio::fs::read(file_path).await?;
    Ok(compute_sha256_bytes(&bytes))
}

#[cfg(test)]
mod test {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn test_should_ignore_pyc_files() {
        let resolver = FileResolver::new(PathBuf::from("/project"), vec![]);

        // A .pyc file should be ignored
        assert!(resolver.should_ignore(&PathBuf::from("/project/module.pyc")));

        // A .pyc file in a subdirectory should be ignored
        assert!(resolver.should_ignore(&PathBuf::from("/project/sub/module.pyc")));

        // A .py file should not be ignored
        assert!(!resolver.should_ignore(&PathBuf::from("/project/module.py")));
    }
}
