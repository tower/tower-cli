use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use tokio::{
    fs::File,
    io::{AsyncReadExt, AsyncWriteExt},
};
use config::Towerfile;
use tokio_tar::{Archive, Builder};
use glob::glob;
use tmpdir::TmpDir;

// TODO: Reintroduce once optional gzip compression is allowed for packaging.
// use async_compression::tokio::write::GzipEncoder;

mod error;
pub use error::Error;

const CURRENT_PACKAGE_VERSION: i32 = 1;

#[derive(Clone, Serialize, Deserialize)]
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
    pub parameters: Vec<Parameter>
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

    // parameters are the parameters to use for this app.
    pub parameters: Vec<Parameter>,
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
        let base_dir = towerfile.base_dir.clone();

        Self {
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
       // We expand the base_dir because handling the paths as absolute paths is easier than
       // handling them as relative paths.
       let base_dir = spec.base_dir.canonicalize().unwrap();

       let tmp_dir = TmpDir::new("tower-package").await?;
       let package_path = tmp_dir.to_path_buf().join("package.tar");
       log::debug!("building package at: {:?}", package_path);

       let file = File::create(package_path.clone()).await?;
       let mut builder = Builder::new(file);

       // TODO: When we want to enable gzip compression, we can uncomment the following lines.
       // We'll also need to uncommend the stuff below about finishing compression.
       //let gzip = GzipEncoder::new(file);

       //let mut builder = Builder::new(gzip);

       for file_glob in spec.file_globs {
           let path = base_dir.join(file_glob);
           let path_str = extract_glob_path(path);
           log::debug!("resolving glob pattern: {}", path_str);

           for entry in glob(&path_str).unwrap() {
               let physical_path = entry.unwrap()
                   .canonicalize()
                   .unwrap();

               log::debug!(" - adding file: {:?}", physical_path);

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

       let file = File::open(self.package_file_path.clone().unwrap()).await?;
       let mut archive = Archive::new(file);

       archive.unpack(path.clone()).await?;
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
