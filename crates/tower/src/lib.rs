#[cfg(feature = "pyo3")]
mod bindings {
    use std::path::PathBuf;

    use pyo3::exceptions::PyRuntimeError;
    use pyo3::prelude::*;

    use config::Towerfile;
    use tower_package::{Package, PackageSpec};

    /// Build a Tower package from a directory containing a Towerfile.
    ///
    /// Args:
    ///     dir: Path to the directory containing the Towerfile.
    ///     output: Destination path for the built .tar.gz package.
    #[pyfunction]
    fn build_package(dir: &str, output: &str) -> PyResult<()> {
        let towerfile_path = PathBuf::from(dir).join("Towerfile");

        let towerfile = Towerfile::from_path(towerfile_path)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        let spec = PackageSpec::from_towerfile(&towerfile);

        let rt = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        let package = rt
            .block_on(Package::build(spec))
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        let src = package
            .package_file_path
            .as_ref()
            .ok_or_else(|| PyRuntimeError::new_err("package build produced no output file"))?;

        std::fs::copy(src, output).map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        Ok(())
    }

    #[pymodule]
    pub fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_function(wrap_pyfunction!(build_package, m)?)?;
        Ok(())
    }
}
