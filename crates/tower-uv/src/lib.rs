use std::collections::HashMap;
use std::fs::{self, OpenOptions};
use std::hash::{Hash, Hasher};
use std::path::{Path, PathBuf};
use std::process::Stdio;

use fs2::FileExt;
use regex::Regex;
use seahash::SeaHasher;
use tokio::process::{Child, Command};
use tower_telemetry::debug;

pub mod install;

// UV_VERSION is the version of UV to download and install when setting up a local UV deployment.
pub const UV_VERSION: &str = "0.9.27";

#[derive(Debug)]
pub enum Error {
    IoError(std::io::Error),
    NotFound(String),
    PermissionDenied(String),
    Other(String),
    MissingPyprojectToml,
    InvalidUv,
    UnsupportedPlatform,
}

impl From<std::io::Error> for Error {
    fn from(err: std::io::Error) -> Self {
        // Convert std::fs::Error to your custom Error type
        Error::IoError(err)
    }
}

impl From<install::Error> for Error {
    fn from(err: install::Error) -> Self {
        match err {
            install::Error::NotFound(msg) => Error::NotFound(msg),
            install::Error::UnsupportedPlatform => Error::UnsupportedPlatform,
            install::Error::IoError(e) => Error::IoError(e),
            install::Error::Other(msg) => Error::Other(msg),
        }
    }
}

fn normalize_env_vars(env_vars: &HashMap<String, String>) -> HashMap<String, String> {
    // we copy this locally so we can mutate the results.
    let mut env_vars = env_vars.clone();

    // Copy the PATH across so that the child process can find tools/binaries already installed
    // on the host system.
    let path = std::env::var("PATH").unwrap_or_default();
    env_vars.insert("PATH".to_string(), path);

    // This special hack helps us support Sling. The user needs to specify exactly where the Sling
    // binary is installed using the SLING_BINARY environment variable such that we don't have to
    // download the Sling binary every single time.
    let sling_binary = std::env::var("SLING_BINARY").unwrap_or_default();
    env_vars.insert("SLING_BINARY".to_string(), sling_binary);

    #[cfg(windows)]
    {
        // If we are running on Windows, we need to retain the SYSTEMROOT env var because Python
        // needs it to initialize it's random number generator. Fun fact!
        let systemroot = std::env::var("SYSTEMROOT").unwrap_or_default();
        env_vars.insert("SYSTEMROOT".to_string(), systemroot);

        // We also need to bring along the TEMP environment variable because Python needs it for
        // things like creating temporary files, etc. But only set if not already provided.
        if !env_vars.contains_key("TEMP") {
            let temp = std::env::var("TEMP").unwrap_or_default();
            env_vars.insert("TEMP".to_string(), temp);
        }

        // Apparently, according to some random person on Stack Overflow, sometimes the var can be
        // TEMP and sometimes it can be TMP. So uh...let's just grab both just in case.
        if !env_vars.contains_key("TMP") {
            let tmp = std::env::var("TMP").unwrap_or_default();
            env_vars.insert("TMP".to_string(), tmp);
        }
    }

    #[cfg(not(windows))]
    {
        // Some downstream dependencies require a HOME environment variable to be set.
        let home = std::env::var("HOME").unwrap_or_default();
        env_vars.insert("HOME".to_string(), home);

        // We also need a PATH environment variable often times, we really want the most basic
        // thing we can get here but for now we'll pass in the currently-configured one.
        let path = std::env::var("PATH").unwrap_or_default();
        env_vars.insert("PATH".to_string(), path);

        // On Unix systems, we also want to bring along the TMPDIR environment variable for temp
        // files. But only set it if not already provided (to allow custom temp directories).
        if !env_vars.contains_key("TMPDIR") {
            let tmpdir = std::env::var("TMPDIR").unwrap_or_default();
            env_vars.insert("TMPDIR".to_string(), tmpdir);
        }

        // Also other potentially-set temp vars. These may not be set.
        // Only set if not already provided.
        if !env_vars.contains_key("TEMP") {
            let temp = std::env::var("TEMP").unwrap_or_default();
            env_vars.insert("TEMP".to_string(), temp);
        }

        if !env_vars.contains_key("TMP") {
            let tmp = std::env::var("TMP").unwrap_or_default();
            env_vars.insert("TMP".to_string(), tmp);
        }

        // Let's pass in TZ as well to propagate that to child processes.
        let tz = std::env::var("TZ").unwrap_or_default();
        env_vars.insert("TZ".to_string(), tz);

        // And finally locale info, some peeps might need that.
        let lang = std::env::var("LANG").unwrap_or_default();
        env_vars.insert("LANG".to_string(), lang);
    }

    env_vars
}

/// Cleans up stale UV lock files from the system temp directory.
///
/// UV creates lock files (e.g., `uv-<hash>.lock`) in the temp directory for concurrent operation
/// safety. These files are not automatically cleaned up when UV exits. This function finds all
/// such files and removes any that are not currently locked by another process.
pub fn cleanup_stale_uv_lock_files() {
    let temp_dir = std::env::temp_dir();

    let entries = match fs::read_dir(&temp_dir) {
        Ok(entries) => entries,
        Err(e) => {
            debug!(
                "Failed to read temp directory for lock file cleanup: {:?}",
                e
            );
            return;
        }
    };

    for entry in entries.flatten() {
        let path = entry.path();

        // Only process files matching the uv-*.lock pattern
        if let Some(file_name) = path.file_name() {
            if !is_uv_lock_file_name(&file_name) {
                continue;
            }
        } else {
            continue;
        }

        // Try to open the file and acquire an exclusive lock
        let file = match OpenOptions::new().read(true).write(true).open(&path) {
            Ok(f) => f,
            Err(e) => {
                debug!("Failed to open lock file {:?}: {:?}", path, e);
                continue
            }
        };

        // Try to acquire an exclusive lock without blocking
        if file.try_lock_exclusive().is_ok() {
            // We got the lock, meaning no other process is using this file.
            // Unlock and delete it.
            let _ = FileExt::unlock(&file);
            drop(file); // Close the file handle before deleting

            if let Err(e) = fs::remove_file(&path) {
                debug!("Failed to remove stale lock file {:?}: {:?}", path, e);
            } else {
                debug!("Cleaned up stale UV lock file: {:?}", path);
            }
        }
        // If we couldn't get the lock, another process is using it, so leave it alone
    }
}

fn is_uv_lock_file_name<S: AsRef<std::ffi::OsStr>>(lock_name: S) -> bool {
    // There isn't a really great way of _not_ instantiating this on each call, without using a
    // LazyLock or some other synchronization method. So, we just take the runtime hit instead of
    // the synchonization hit.
    let uv_lock_pattern = Regex::new(r"^uv-[0-9a-f]{16}\.lock$").unwrap();
    let os_str = lock_name.as_ref();

    os_str.to_str()
        .map(|name| uv_lock_pattern.is_match(name))
        .unwrap_or(false)
}

/// Computes the lock file path that uv will create for a given working directory.
///
/// This replicates uv's lock file naming: `uv-{hash}.lock` where the hash is
/// a seahash of the workspace path. When running uv commands with a specific
/// working directory, this function can predict which lock file will be used.
pub fn compute_uv_lock_file_path(cwd: &Path) -> PathBuf {
    let mut hasher = SeaHasher::new();
    cwd.hash(&mut hasher);
    let hash = hasher.finish();
    let hash_hex = hex::encode(hash.to_le_bytes());

    std::env::temp_dir().join(format!("uv-{}.lock", hash_hex))
}

/// Cleans up the lock file for a specific working directory after uv exits.
///
/// This should be called after a uv process completes to clean up the lock file
/// it created. The lock file is only removed if no other process is using it.
///
/// Returns `true` if the lock file was successfully removed, `false` otherwise
/// (either because it didn't exist, couldn't be opened, or is still locked).
pub fn cleanup_lock_file_for_cwd(cwd: &Path) -> bool {
    let lock_path = compute_uv_lock_file_path(cwd);

    let file = match OpenOptions::new().read(true).write(true).open(&lock_path) {
        Ok(f) => f,
        Err(_) => return false, // File doesn't exist or can't be opened
    };

    // Only delete if we can acquire exclusive lock (no other process using it)
    if file.try_lock_exclusive().is_ok() {
        let _ = FileExt::unlock(&file);
        drop(file); // Close the file handle before deleting

        if let Err(e) = fs::remove_file(&lock_path) {
            debug!("Failed to remove lock file {:?}: {:?}", lock_path, e);
            false
        } else {
            debug!("Cleaned up UV lock file for {:?}: {:?}", cwd, lock_path);
            true
        }
    } else {
        // Another process is still using this lock file
        false
    }
}

async fn test_uv_path(path: &PathBuf) -> Result<(), Error> {
    let res = Command::new(&path)
        .arg("--color")
        .arg("never")
        .arg("--no-progress")
        .arg("--help")
        .output()
        .await;

    match res {
        Ok(_) => Ok(()),
        Err(e) => {
            debug!("Testing UV failed: {:?}", e);
            Err(Error::InvalidUv)
        }
    }
}

pub struct Uv {
    pub uv_path: PathBuf,

    // cache_dir is the directory that dependencies should be cached in.
    cache_dir: Option<PathBuf>,

    // protected_mode is a flag that indicates whether the UV instance is in protected mode.
    // In protected mode, the UV instance do things like clear the environment variables before
    // use, etc.
    protected_mode: bool,
}

impl Uv {
    pub async fn new(cache_dir: Option<PathBuf>, protected_mode: bool) -> Result<Self, Error> {
        match install::find_or_setup_uv().await {
            Ok(uv_path) => {
                test_uv_path(&uv_path).await?;
                Ok(Uv {
                    uv_path,
                    cache_dir,
                    protected_mode,
                })
            }
            Err(e) => {
                debug!("Error setting up UV: {:?}", e);
                Err(e.into())
            }
        }
    }

    pub async fn venv(
        &self,
        cwd: &PathBuf,
        env_vars: &HashMap<String, String>,
    ) -> Result<Child, Error> {
        debug!("Executing UV ({:?}) venv in {:?}", &self.uv_path, cwd);

        let mut cmd = Command::new(&self.uv_path);
        cmd.kill_on_drop(true)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .current_dir(cwd)
            .arg("venv")
            .envs(env_vars);

        #[cfg(unix)]
        {
            cmd.process_group(0);
        }

        if let Some(dir) = &self.cache_dir {
            cmd.arg("--cache-dir").arg(dir);
        }

        let child = cmd.spawn()?;

        Ok(child)
    }

    pub async fn sync(
        &self,
        cwd: &PathBuf,
        env_vars: &HashMap<String, String>,
    ) -> Result<Child, Error> {
        // We need to figure out which sync strategy to apply. If there is a pyproject.toml, then
        // that's easy.
        if cwd.join("pyproject.toml").exists() {
            debug!("Executing UV ({:?}) sync in {:?}", &self.uv_path, cwd);
            let mut cmd = Command::new(&self.uv_path);
            cmd.kill_on_drop(true)
                .stdin(Stdio::null())
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .current_dir(cwd)
                .arg("--color")
                .arg("never")
                .arg("--no-progress")
                .arg("sync")
                .envs(env_vars);

            #[cfg(unix)]
            {
                cmd.process_group(0);
            }

            if let Some(dir) = &self.cache_dir {
                cmd.arg("--cache-dir").arg(dir);
            }

            let child = cmd.spawn()?;

            Ok(child)
        } else if cwd.join("requirements.txt").exists() {
            debug!(
                "Executing UV ({:?}) sync with requirements in {:?}",
                &self.uv_path, cwd
            );

            // If there is a requirements.txt, then we can use that to sync.
            let mut cmd = Command::new(&self.uv_path);
            cmd.kill_on_drop(true)
                .stdin(Stdio::null())
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .current_dir(cwd)
                .arg("--color")
                .arg("never")
                .arg("pip")
                .arg("install")
                .arg("-r")
                .arg(cwd.join("requirements.txt"))
                .envs(env_vars);

            #[cfg(unix)]
            {
                cmd.process_group(0);
            }

            if let Some(dir) = &self.cache_dir {
                cmd.arg("--cache-dir").arg(dir);
            }

            let child = cmd.spawn()?;

            Ok(child)
        } else {
            // If there is no pyproject.toml or requirements.txt, then we can't sync.
            Err(Error::MissingPyprojectToml)
        }
    }

    pub async fn run(
        &self,
        cwd: &PathBuf,
        program: &PathBuf,
        env_vars: &HashMap<String, String>,
    ) -> Result<Child, Error> {
        debug!(
            "Executing UV ({:?}) run {:?} in {:?}",
            &self.uv_path, program, cwd
        );

        // Sometimes, we need to copy some env vars out of the current environment and into the new
        // one!
        let env_vars = normalize_env_vars(env_vars);

        let mut cmd = Command::new(&self.uv_path);
        cmd.kill_on_drop(true)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .current_dir(cwd)
            .arg("--color")
            .arg("never")
            .arg("--no-progress")
            .arg("run")
            .arg(program);

        #[cfg(unix)]
        {
            cmd.process_group(0);
        }

        if self.protected_mode {
            cmd.env_clear();
        }

        // Need to do this after env_clear intentionally.
        cmd.envs(env_vars);

        if let Some(dir) = &self.cache_dir {
            cmd.arg("--cache-dir").arg(dir);
        }

        let child = cmd.spawn()?;
        Ok(child)
    }

    pub async fn is_valid(&self) -> bool {
        test_uv_path(&self.uv_path).await.is_ok()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn test_compute_uv_lock_file_path_is_deterministic() {
        let path = Path::new("/some/project/path");

        let lock_path_1 = compute_uv_lock_file_path(path);
        let lock_path_2 = compute_uv_lock_file_path(path);

        assert_eq!(lock_path_1, lock_path_2);
    }

    #[test]
    fn test_compute_uv_lock_file_path_different_paths_produce_different_hashes() {
        let path_a = Path::new("/project/a");
        let path_b = Path::new("/project/b");

        let lock_path_a = compute_uv_lock_file_path(path_a);
        let lock_path_b = compute_uv_lock_file_path(path_b);

        assert_ne!(lock_path_a, lock_path_b);
    }

    #[test]
    fn test_compute_uv_lock_file_path_format() {
        let path = Path::new("/test/path");
        let lock_path = compute_uv_lock_file_path(path);

        let file_name = lock_path.file_name().unwrap().to_str().unwrap();
        assert!(file_name.starts_with("uv-"));
        assert!(file_name.ends_with(".lock"));

        // Hash should be 16 hex characters (8 bytes as hex)
        let hash_part = &file_name[3..file_name.len() - 5];
        assert_eq!(hash_part.len(), 16);
        assert!(hash_part.chars().all(|c| c.is_ascii_hexdigit()));
    }

    #[test]
    fn test_cleanup_lock_file_for_cwd_removes_unlocked_file() {
        let temp_dir = std::env::temp_dir();
        let test_cwd = temp_dir.join("test-cleanup-cwd");

        // Compute where the lock file would be
        let lock_path = compute_uv_lock_file_path(&test_cwd);

        // Create the lock file manually
        {
            let mut file = fs::File::create(&lock_path).unwrap();
            file.write_all(b"test").unwrap();
        }

        assert!(lock_path.exists());

        // Clean it up
        let result = cleanup_lock_file_for_cwd(&test_cwd);

        assert!(result);
        assert!(!lock_path.exists());
    }

    #[test]
    fn test_cleanup_lock_file_for_cwd_returns_false_for_nonexistent() {
        let nonexistent_cwd = Path::new("/nonexistent/path/that/does/not/exist");

        let result = cleanup_lock_file_for_cwd(nonexistent_cwd);

        assert!(!result);
    }

    #[test]
    fn test_cleanup_lock_file_for_cwd_respects_lock() {
        let temp_dir = std::env::temp_dir();
        let test_cwd = temp_dir.join("test-cleanup-locked-cwd");

        let lock_path = compute_uv_lock_file_path(&test_cwd);

        // Create and hold a lock on the file
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(true)
            .open(&lock_path)
            .unwrap();
        file.lock_exclusive().unwrap();

        // Try to clean up while locked - should fail
        let result = cleanup_lock_file_for_cwd(&test_cwd);

        assert!(!result);
        assert!(lock_path.exists());

        // Release the lock and clean up
        drop(file);
        let _ = fs::remove_file(&lock_path);
    }

    #[test]
    fn test_cleanup_stale_uv_lock_files_only_removes_uv_lock_files() {
        let temp_dir = std::env::temp_dir();

        // Create a valid UV lock file (matches uv-<16 hex chars>.lock pattern)
        let uv_lock_file = temp_dir.join("uv-0123456789abcdef.lock");
        {
            let mut file = fs::File::create(&uv_lock_file).unwrap();
            file.write_all(b"test uv lock").unwrap();
        }

        // Create a non-UV file that should NOT be touched
        let non_uv_file = temp_dir.join("not-a-uv-lock-file.txt");
        {
            let mut file = fs::File::create(&non_uv_file).unwrap();
            file.write_all(b"other file").unwrap();
        }

        assert!(uv_lock_file.exists());
        assert!(non_uv_file.exists());

        // Run the cleanup
        cleanup_stale_uv_lock_files();

        // UV lock file should be removed (it wasn't locked)
        assert!(!uv_lock_file.exists(), "UV lock file should have been cleaned up");

        // Non-UV file should still exist
        assert!(non_uv_file.exists(), "Non-UV file should not have been touched");

        // Clean up the non-UV file
        let _ = fs::remove_file(&non_uv_file);
    }
}
