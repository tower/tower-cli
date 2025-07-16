use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use std::pin::Pin;
use std::collections::{VecDeque, HashMap};
use tokio::{
    fs::File,
    io::{AsyncRead, BufReader, AsyncReadExt, AsyncWriteExt},
};
use config::Towerfile;
use tokio_tar::{Archive, Builder};
use glob::glob;
use tmpdir::TmpDir;

use async_compression::tokio::write::GzipEncoder;
use async_compression::tokio::bufread::GzipDecoder;

use tower_telemetry::debug;

mod error;
pub use error::Error;

const CURRENT_PACKAGE_VERSION: i32 = 2;

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Parameter{
    pub name: String,
    pub description: String,
    pub default: String,
}

#[derive(Clone, Serialize, Deserialize)]
pub struct Manifest {
    // version is the version of the packaging format that was used.
    pub version: Option<i32>,

    // invoke is the target in this package to invoke.
    pub invoke: String,

    #[serde(default)]
    pub parameters: Vec<Parameter>,

    // schedule is the schedule that we want to execute this app on. this is, just temporarily,
    // where it will live.
    pub schedule: Option<String>,

    // import_paths are the rewritten collection of modules that this app's code goes into.
    #[serde(default)]
    pub import_paths: Vec<String>,

    // app_dir_name is the name of the application directory within the package.
    #[serde(default)]
    pub app_dir_name: String,

    // modules_dir_name is the name of the modules directory within the package.
    #[serde(default)]
    pub modules_dir_name: String,
}

impl Manifest {
    pub async fn from_path(path: &Path) -> Result<Self, Error> {
        let mut file = File::open(path).await?;
        let mut contents = String::new();
        file.read_to_string(&mut contents).await?;
        Self::from_json(&contents).await
    }

    pub async fn from_json(data: &str) -> Result<Self, Error> {
        let manifest: Self = serde_json::from_str(data)?;
        Ok(manifest) 
    }
}

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

    // schedule defines the frequency that this app should be run on.
    pub schedule: Option<String>,

    pub import_paths: Vec<String>,
}

fn get_parameters(towerfile: &Towerfile) -> Vec<Parameter> {
    let mut parameters = Vec::new();
    for p in &towerfile.parameters {
        parameters.push(Parameter {
            name: p.name.clone(),
            description: p.description.clone(),
            default: p.default.clone(),
        });
    }
    parameters
}

impl PackageSpec {
    pub fn from_towerfile(towerfile: &Towerfile) -> Self {
        debug!("creating package spec from towerfile: {:?}", towerfile);
        let towerfile_path = towerfile.file_path.clone();
        let base_dir = towerfile_path.parent().
            unwrap_or_else(|| Path::new(".")).
            to_path_buf();

        let schedule = if towerfile.app.schedule.is_empty() {
            None
        } else {
            Some(towerfile.app.schedule.to_string())
        };

        // We need to turn these (validated) paths into something taht we can use at runtime.
        let import_paths = towerfile.app.import_paths.iter()
            .map(|p| p.to_string_lossy().to_string())
            .collect();

        Self {
            schedule,
            towerfile_path,
            base_dir,
            import_paths,
            invoke: towerfile.app.script.clone(),
            file_globs: towerfile.app.source.clone(),
            parameters: get_parameters(towerfile),
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
           },
       }
   }

   pub async fn from_unpacked_path(path: PathBuf) -> Self {
       let manifest_path = path.join("MANIFEST");
       let manifest = Manifest::from_path(&manifest_path).await.unwrap();

       Self {
           tmp_dir: None,
           package_file_path: None,
           unpacked_path: Some(path),
           manifest,
       }
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

       let tmp_dir = TmpDir::new("tower-package").await?;
       let package_path = tmp_dir.to_path_buf().join("package.tar");
       debug!("building package at: {:?}", package_path);

       let file = File::create(package_path.clone()).await?;
       let gzip = GzipEncoder::new(file);
       let mut builder = Builder::new(gzip);

       // If the user didn't specify anything here we'll package everything under this directory
       // and ship it to Tower.
       let mut file_globs = spec.file_globs.clone();

       // If there was no source specified, we'll pull in all the source code in the current
       // directory.
       if file_globs.is_empty() {
           debug!("no source files specified. using default paths.");
           file_globs.push("./**/*".to_string()); 
       } 

       // We'll collect all the file paths in a collection here.
       let mut file_paths = HashMap::new();

       for file_glob in file_globs {
           let path = base_dir.join(file_glob);
           resolve_glob_path(path, &base_dir, &mut file_paths).await;
       }

       // App code lives in the app dir
       let app_dir = PathBuf::from("app");

       // Now that we have all the paths, we'll append them to the builder.
       for (physical_path, logical_path) in file_paths {
           // All of the app code goes into the "app" directory.
           let logical_path = app_dir.join(logical_path);
           builder.append_path_with_name(physical_path, logical_path).await?;
       }

       // Module code lives in the modules dir.
       let module_dir = PathBuf::from("modules");
       let mut import_paths = vec![];

       // Now we need to package up all the modules to include in the code base too.
       for import_path in &spec.import_paths {
           // The import_path should always be relative to the base_path.
           let import_path = base_dir.join(import_path).canonicalize()?;
           let parent = import_path.parent().unwrap();

           let mut file_paths = HashMap::new();
           resolve_path(&import_path, parent, &mut file_paths).await;

           // The file_name should constitute the logical path
           let import_path = import_path.file_name().unwrap();
           let import_path = module_dir.join(import_path);
           let import_path_str = import_path.into_os_string().into_string().unwrap();
           import_paths.push(import_path_str);

           // Now we write all of these paths to the modules directory.
           for (physical_path, logical_path) in file_paths {
               let logical_path = module_dir.join(logical_path);
               debug!("adding file {}", logical_path.display());
               builder.append_path_with_name(physical_path, logical_path).await?;
           }
       }

       let manifest = Manifest {
           import_paths,
           version: Some(CURRENT_PACKAGE_VERSION),
           invoke: String::from(spec.invoke),
           parameters: spec.parameters,
           schedule: spec.schedule,
           app_dir_name: app_dir.to_string_lossy().to_string(),
           modules_dir_name: module_dir.to_string_lossy().to_string(),
       };

       // the whole manifest needs to be written to a file as a convenient way to avoid having to
       // manually populate the TAR file headers for this data. maybe in the future, someone will
       // have the humption to do so here, thus avoiding an unnecessary file write (and the
       // associated failure modes).
       let manifest_path = tmp_dir.to_path_buf().join("MANIFEST");
       write_manifest_to_file(&manifest_path, &manifest).await?;
       builder.append_path_with_name(manifest_path, "MANIFEST").await?;

       // Let's also package the Towerfile along with it.
       builder.append_path_with_name(
           spec.towerfile_path,
           "Towerfile",
       ).await?;

       // We'll need to delete the lines above here.
       let mut gzip = builder.into_inner().await?;
       gzip.shutdown().await?;

       //// probably not explicitly required; however, makes the test suite pass so...
       let mut file = gzip.into_inner();
       file.shutdown().await?;

       Ok(Self {
           manifest,
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

async fn write_manifest_to_file(path: &PathBuf, manifest: &Manifest) -> Result<(), Error> {
    let mut file = File::create(path).await?;
    let data = serde_json::to_string(&manifest)?;
    file.write_all(data.as_bytes()).await?;

    // this is required to ensure that everything gets flushed to disk. it's not enough to just let
    // the file reference get dropped.
    file.shutdown().await?;

    Ok(())
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
    match decoder.read(&mut buffer).await {
        Ok(_) => true,
        Err(_) => false,
    }
}

async fn unpack_archive<P: AsRef<Path>>(package_path: P, output_path: P) -> Result<(), std::io::Error> {
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

async fn resolve_glob_path(path: PathBuf, base_dir: &PathBuf, file_paths: &mut HashMap<PathBuf, PathBuf>) {
   let path_str = extract_glob_path(path);
   debug!("resolving glob pattern: {}", path_str);

   for entry in glob(&path_str).unwrap() {
       resolve_path(&entry.unwrap(), base_dir, file_paths).await;
   }
}

async fn resolve_path(path: &PathBuf, base_dir: &Path, file_paths: &mut HashMap<PathBuf, PathBuf>) {
    let mut queue = VecDeque::new();
    queue.push_back(path.to_path_buf());

    while let Some(current_path) = queue.pop_front() {
        let canonical_path = current_path.canonicalize();

        if canonical_path.is_err() {
            debug!(" - skipping path {}: {}", current_path.display(), canonical_path.unwrap_err());
            continue;         
        }

        // We can safely unwrap this because we understand that it's not going to fail at this
        // point.
        let physical_path = canonical_path.unwrap();

        if physical_path.is_dir() {
            let mut entries = tokio::fs::read_dir(&physical_path).await.unwrap();

            while let Some(entry) = entries.next_entry().await.unwrap() {
                queue.push_back(entry.path());
            }
        } else {
            if !should_ignore_file(&physical_path) {
                let cp = physical_path.clone();

                match cp.strip_prefix(base_dir) {
                    Err(err) => {
                        debug!(" - skipping file {}: not in base directory {}: {:?}", physical_path.display(), base_dir.display(), err);
                        continue;
                    }
                    Ok(logical_path) => {
                        debug!(" - resolved path {} to logical path {}", physical_path.display(), logical_path.display());
                        file_paths.insert(physical_path, logical_path.to_path_buf());
                    }
                }
            }
        }
    }
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

fn should_ignore_file(p: &PathBuf) -> bool {
    // Ignore anything that is compiled python
    if p.ends_with(".pyc") {
        return true;
    }

    if is_file(p, "Towerfile") {
        return true;
    }

    // Ignore a .gitignore file
    if is_file(p, ".gitignore") {
        return true;
    }

    // Remove anything thats __pycache__
    if is_in_dir(p, "__pycache__") {
        return true
    }

    // Ignore anything that lives within a .git directory
    if is_in_dir(p, ".git") {
        return true
    }

    // Ignore anything that's in a virtualenv, too
    if is_in_dir(p, ".venv") {
        return true
    }

    return false;
}
