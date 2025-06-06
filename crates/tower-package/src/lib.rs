use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use std::pin::Pin;
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

const CURRENT_PACKAGE_VERSION: i32 = 1;

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Parameter{
    pub name: String,
    pub description: String,
    pub default: String,
}

#[derive(Clone, Serialize, Deserialize)]
pub struct Manifest {
    pub version: Option<i32>,
    pub invoke: String,

    #[serde(default)]
    pub parameters: Vec<Parameter>,

    // schedule is the schedule that we want to execute this app on. this is, just temporarily,
    // where it will live.
    pub schedule: Option<String>,
}

impl Manifest {
    pub async fn from_path(path: &Path) -> Result<Self, Error> {
        let mut file = File::open(path).await?;
        let mut contents = String::new();
        file.read_to_string(&mut contents).await?;

        let manifest: Self = serde_json::from_str(&contents)?;
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
        let base_dir = towerfile.app.workspace.clone();

        let schedule = if towerfile.app.schedule.is_empty() {
            None
        } else {
            Some(towerfile.app.schedule.to_string())
        };

        Self {
            schedule,
            towerfile_path,
            base_dir,
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

       for file_glob in spec.file_globs {
           let path = base_dir.join(file_glob);
           let path_str = extract_glob_path(path);
           debug!("resolving glob pattern: {}", path_str);

           for entry in glob(&path_str).unwrap() {
               let physical_path = entry.unwrap()
                   .canonicalize()
                   .unwrap();

               debug!(" - adding file: {:?}", physical_path);

               // turn this back in to a path that is relative to the TAR file root
               let cp = physical_path.clone();
               let logical_path = cp.strip_prefix(&base_dir).unwrap();

               builder.append_path_with_name(physical_path, logical_path).await?;
           }
       }

       let manifest = Manifest {
           version: Some(CURRENT_PACKAGE_VERSION),
           invoke: String::from(spec.invoke),
           parameters: spec.parameters,
           schedule: spec.schedule,
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

       // consume the builder to close it, then close the underlying gzip stream
       let mut file = builder.into_inner().await?;
       file.shutdown().await?;

       // TODO: When we want to enable gzip compression, we can uncomment the following lines.
       // We'll need to delete the lines above here.
       //let mut gzip = builder.into_inner().await?;
       //gzip.shutdown().await?;

       //// probably not explicitly required; however, makes the test suite pass so...
       //let mut file = gzip.into_inner();
       //file.shutdown().await?;

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
