use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use config::Towerfile;
use tokio::fs::File;
use tokio::io::{AsyncRead, AsyncReadExt};
use tokio::io::AsyncWriteExt;
use tokio_tar::Builder;
use async_compression::tokio::write::GzipEncoder;
use std::pin::Pin;
use std::task::{Context, Poll};
use glob::glob;
use tmpdir::TmpDir;

mod error;
pub use error::Error;

const CURRENT_PACKAGE_VERSION: i32 = 1;

#[derive(Clone, Serialize, Deserialize)]
pub struct Manifest {
    pub version: Option<i32>,
    pub invoke: String,
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
pub struct PackageSpec {
    // invoke is the file to invoke when the package is run.
    pub invoke: String,

    // base_dir is the directory where the package is located.
    pub base_dir: PathBuf,

    // file_globs is a list of globs that match the files in the package.
    pub file_globs: Vec<String>,
}

impl PackageSpec {
    pub fn from_towerfile(towerfile: &Towerfile) -> Self {
        let base_dir = std::env::current_dir().unwrap();

        Self {
            base_dir,
            invoke: towerfile.app.script.clone(),
            file_globs: towerfile.app.source.clone(),
        }  
    }
}

pub struct Package {
    // tmp_dir is used to keep the package directory around occasionally so the directory doesn't
    // get deleted out from under the application.
    pub tmp_dir: Option<TmpDir>,

    pub manifest: Manifest, 

    // path is where on disk (if anywhere) the pacakge lives.
    pub path: PathBuf,
}

impl Package {
   pub fn default() -> Self {
       Self {
           tmp_dir: None,
           path: PathBuf::new(),
           manifest: Manifest {
               version: Some(CURRENT_PACKAGE_VERSION),
               invoke: "".to_string(),
           },
       }
   }

   pub async fn from_path(path: PathBuf) -> Self {
       let manifest_path = path.join("MANIFEST");
       let manifest = Manifest::from_path(&manifest_path).await.unwrap();

       Self {
           tmp_dir: None,
           path,
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
       let tmp_dir = TmpDir::new("tower-package").await?;
       let package_path = tmp_dir.to_path_buf().join("package.tar");

       let file = File::create(package_path.clone()).await?;
       let mut builder = Builder::new(file);

       // TODO: When we want to enable gzip compression, we can uncomment the following lines.
       // We'll also need to uncommend the stuff below about finishing compression.
       //let gzip = GzipEncoder::new(file);

       //let mut builder = Builder::new(gzip);

       for file_glob in spec.file_globs {
           let path = spec.base_dir.join(file_glob);
           let path_str = path.to_str().unwrap();

           for entry in glob(path_str).unwrap() {
               let physical_path = entry.unwrap();

               // this copy of physical_path is used to appease the borrow checker.
               let cp = physical_path.clone();
               let logical_path = cp.strip_prefix(&spec.base_dir).unwrap();

               builder.append_path_with_name(physical_path, logical_path).await?;
           }
       }

       let manifest = Manifest {
           version: Some(CURRENT_PACKAGE_VERSION),
           invoke: String::from(spec.invoke),
       };

       // the whole manifest needs to be written to a file as a convenient way to avoid having to
       // manually populate the TAR file headers for this data. maybe in the future, someone will
       // have the humption to do so here, thus avoiding an unnecessary file write (and the
       // associated failure modes).
       let manifest_path = tmp_dir.to_path_buf().join("MANIFEST");
       write_manifest_to_file(&manifest_path, &manifest).await?;
       builder.append_path_with_name(manifest_path, "MANIFEST").await?;

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
           tmp_dir: Some(tmp_dir),
           manifest,
           path: package_path,
       })
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
