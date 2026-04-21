mod core;

pub use core::{
    build_package, compute_sha256_bytes, compute_sha256_package, normalize_path, BuiltPackage,
    Entry, Manifest, PackageInputs, Parameter, CURRENT_PACKAGE_VERSION, MAX_PACKAGE_SIZE,
};

#[cfg(feature = "native")]
mod error;
#[cfg(feature = "native")]
mod native;

#[cfg(feature = "native")]
pub use error::Error;
#[cfg(feature = "native")]
pub use native::{compute_sha256_file, Package, PackageSpec};

#[cfg(feature = "wasm")]
mod wasm;
