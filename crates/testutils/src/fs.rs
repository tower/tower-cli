use std::fs::{remove_file, File};
use std::io;
use std::path::{Path, PathBuf};

pub struct TestFile {
    path: PathBuf,
    file: File,
}

impl TestFile {
    // Creates a new temporary file, which will be deleted on drop.
    pub fn new<P: AsRef<Path>>(path: P) -> io::Result<Self> {
        let path = path.as_ref().to_path_buf();
        let file = File::create(&path)?;
        Ok(TestFile { path, file })
    }

    // Provides a mutable reference to the inner file, e.g., to write to it.
    pub fn file(&mut self) -> &mut File {
        &mut self.file
    }
}

impl Drop for TestFile {
    fn drop(&mut self) {
        // Delete the file when `TestFile` goes out of scope.
        let _ = remove_file(&self.path);
    }
}
