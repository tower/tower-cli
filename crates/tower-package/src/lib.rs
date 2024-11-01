use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use tokio::fs::File;
use tokio::io::AsyncReadExt;
use tokio_tar::{EntryType, Builder, Header};
use async_compression::tokio::write::GzipEncoder;
use glob::glob;
use tempdir::TempDir;

mod error;
pub use error::Error;

const CURRENT_PACKAGE_VERSION: i32 = 1;

#[derive(Clone, Serialize, Deserialize)]
pub struct Manifest {
    pub version: i32,
    pub invoke: String,
}

impl Manifest {
    pub async fn from_file(path: &Path) -> Result<Self, Error> {
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

pub struct Package {
    pub manifest: Manifest, 

    // path is where on disk (if anywhere) the pacakge lives.
    pub path: PathBuf,
}

impl Package {
   pub fn default() -> Self {
       Self {
           path: PathBuf::new(),
           manifest: Manifest {
               version: CURRENT_PACKAGE_VERSION,
               invoke: "".to_string(),
           },
       }
   }

   // build creates a new package from a PackageSpec. PackageSpec is typically composed of fields
   // copied from the Towerfile. The most important thing to know is that the collection of file
   // globs to include in the package.
   //
   // The underlying package is just a TAR file with a special `MANIFEST` file that has also been
   // GZip'd.
   pub async fn build(spec: PackageSpec) -> Result<Self, Error> {
       let tmp_dir = TempDir::new("tower-package")?;
       let package_path = tmp_dir.path().join("package.tar");

       let file = File::create(package_path.clone()).await?;
       let gzip = GzipEncoder::new(file);

       let mut builder = Builder::new(gzip);

       for file_glob in spec.file_globs {
           let path = spec.base_dir.join(file_glob);
           let path_str = path.to_str().unwrap();

           for entry in glob(path_str).unwrap() {
               let path = entry.unwrap();
               println!("{:?}", path.display());
           }
       }

       let manifest = Manifest {
           version: CURRENT_PACKAGE_VERSION,
           invoke: String::from(spec.invoke),
       };

       let mut header = Header::new_gnu();
       header.set_entry_type(EntryType::Regular);
       header.set_path(Path::new("MANIFEST")).unwrap();

       let data = serde_json::to_string(&manifest).unwrap();

       builder.append_data(&mut header, "MANIFEST", data.as_bytes()).await?;

       builder.finish().await?;


       Ok(Self {
           manifest,
           path: package_path,
       })
   }
}
