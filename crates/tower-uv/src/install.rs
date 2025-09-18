use std::env;
use std::path::PathBuf;
use std::sync::OnceLock;

use async_compression::tokio::bufread::GzipDecoder;
use async_zip::tokio::read::seek::ZipFileReader;
use futures_lite::io::AsyncReadExt;
use tokio::{process::Command, sync::Mutex};
use tokio_tar::Archive;

use tower_telemetry::debug;

// Copy the UV_VERSION locally to make this a bit more ergonomic.
const UV_VERSION: &str = crate::UV_VERSION;

static GLOBAL_LOCK: OnceLock<Mutex<()>> = OnceLock::new();

fn get_global_lock() -> &'static Mutex<()> {
    GLOBAL_LOCK.get_or_init(|| Mutex::new(()))
}

#[derive(Debug)]
pub enum Error {
    NotFound(String),
    UnsupportedPlatform,
    IoError(std::io::Error),
    Other(String),
}

impl From<std::io::Error> for Error {
    fn from(err: std::io::Error) -> Self {
        Error::IoError(err)
    }
}

impl From<String> for Error {
    fn from(err: String) -> Self {
        Error::Other(err)
    }
}

pub fn get_default_uv_bin_dir() -> Result<PathBuf, Error> {
    let dir = dirs::data_local_dir().ok_or(Error::UnsupportedPlatform)?;
    Ok(dir.join("tower").join("bin"))
}

#[derive(Debug)]
pub struct ArchiveSelector;

impl ArchiveSelector {
    /// Get the appropriate archive name for the current platform
    pub async fn get_archive_name() -> Result<String, String> {
        let arch = env::consts::ARCH;
        let os = env::consts::OS;

        match (arch, os) {
            // macOS
            ("aarch64", "macos") => Ok("uv-aarch64-apple-darwin.tar.gz".to_string()),
            ("x86_64", "macos") => Ok("uv-x86_64-apple-darwin.tar.gz".to_string()),

            // Windows
            ("aarch64", "windows") => Ok("uv-aarch64-pc-windows-msvc.zip".to_string()),
            ("x86_64", "windows") => Ok("uv-x86_64-pc-windows-msvc.zip".to_string()),
            ("x86", "windows") => Ok("uv-i686-pc-windows-msvc.zip".to_string()),

            // Linux
            ("aarch64", "linux") => {
                if Self::is_musl_target() {
                    Ok("uv-aarch64-unknown-linux-musl.tar.gz".to_string())
                } else if Self::check_glibc(2, 28).await {
                    Ok("uv-aarch64-unknown-linux-gnu.tar.gz".to_string())
                } else {
                    Ok("uv-aarch64-unknown-linux-musl.tar.gz".to_string())
                }
            }
            ("x86_64", "linux") => {
                if Self::is_musl_target() {
                    Ok("uv-x86_64-unknown-linux-musl.tar.gz".to_string())
                } else if Self::check_glibc(2, 17).await {
                    Ok("uv-x86_64-unknown-linux-gnu.tar.gz".to_string())
                } else {
                    Ok("uv-x86_64-unknown-linux-musl.tar.gz".to_string())
                }
            }
            ("x86", "linux") => {
                if Self::is_musl_target() {
                    Ok("uv-i686-unknown-linux-musl.tar.gz".to_string())
                } else if Self::check_glibc(2, 17).await {
                    Ok("uv-i686-unknown-linux-gnu.tar.gz".to_string())
                } else {
                    Ok("uv-i686-unknown-linux-musl.tar.gz".to_string())
                }
            }
            ("arm", "linux") => {
                // ARM v6 - only musl available
                Ok("uv-arm-unknown-linux-musleabihf.tar.gz".to_string())
            }
            ("armv7", "linux") => {
                if Self::is_musl_target() {
                    Ok("uv-armv7-unknown-linux-musleabihf.tar.gz".to_string())
                } else if Self::check_glibc(2, 17).await {
                    Ok("uv-armv7-unknown-linux-gnueabihf.tar.gz".to_string())
                } else {
                    Ok("uv-armv7-unknown-linux-musleabihf.tar.gz".to_string())
                }
            }
            ("powerpc64", "linux") => {
                if Self::check_glibc(2, 17).await {
                    Ok("uv-powerpc64-unknown-linux-gnu.tar.gz".to_string())
                } else {
                    Err("PowerPC64 requires glibc 2.17 or newer".to_string())
                }
            }
            ("powerpc64le", "linux") => {
                if Self::check_glibc(2, 17).await {
                    Ok("uv-powerpc64le-unknown-linux-gnu.tar.gz".to_string())
                } else {
                    Err("PowerPC64LE requires glibc 2.17 or newer".to_string())
                }
            }
            ("riscv64", "linux") => {
                if Self::check_glibc(2, 31).await {
                    Ok("uv-riscv64gc-unknown-linux-gnu.tar.gz".to_string())
                } else {
                    Err("RISC-V 64 requires glibc 2.31 or newer".to_string())
                }
            }
            ("s390x", "linux") => {
                if Self::check_glibc(2, 17).await {
                    Ok("uv-s390x-unknown-linux-gnu.tar.gz".to_string())
                } else {
                    Err("s390x requires glibc 2.17 or newer".to_string())
                }
            }

            _ => Err(format!("Unsupported platform: {} {}", arch, os)),
        }
    }

    /// Check if the current target uses musl libc
    fn is_musl_target() -> bool {
        // Check if we're compiled with musl
        cfg!(target_env = "musl")
    }

    /// Check if glibc version meets minimum requirements
    async fn check_glibc(major: u32, minor: u32) -> bool {
        // Only check glibc on Linux with gnu env
        if !cfg!(target_os = "linux") || cfg!(target_env = "musl") {
            return false;
        }

        // Try to get glibc version using ldd
        if let Ok(output) = Command::new("ldd").arg("--version").output().await {
            if let Ok(version_str) = String::from_utf8(output.stdout) {
                return Self::parse_glibc_version(&version_str, major, minor);
            }
        }

        // Fallback: try to read from /lib/libc.so.6
        if let Ok(output) = Command::new("/lib/libc.so.6").output().await {
            if let Ok(version_str) = String::from_utf8(output.stdout) {
                return Self::parse_glibc_version(&version_str, major, minor);
            }
        }

        // If we can't determine the version, assume it's old
        false
    }

    /// Parse glibc version string and compare with required version
    fn parse_glibc_version(version_str: &str, req_major: u32, req_minor: u32) -> bool {
        // Look for version pattern like "2.17" or "2.31"
        for line in version_str.lines() {
            if let Some(version_part) = line.split_whitespace().find(|part| {
                part.contains('.') && part.chars().next().unwrap_or('0').is_ascii_digit()
            }) {
                let version_clean =
                    version_part.trim_matches(|c: char| !c.is_ascii_digit() && c != '.');
                let parts: Vec<&str> = version_clean.split('.').collect();

                if parts.len() >= 2 {
                    if let (Ok(major), Ok(minor)) =
                        (parts[0].parse::<u32>(), parts[1].parse::<u32>())
                    {
                        return major > req_major || (major == req_major && minor >= req_minor);
                    }
                }
            }
        }
        false
    }
}

fn extract_package_name(archive: String) -> String {
    // Remove .tar.gz or .zip extension
    archive
        .strip_suffix(".tar.gz")
        .or(archive.strip_suffix(".zip"))
        .unwrap_or(&archive)
        .to_string()
}

async fn download_uv_archive(path: &PathBuf, archive: String) -> Result<PathBuf, Error> {
    debug!("Downloading UV archive: {}", archive);
    let url = format!(
        "https://github.com/astral-sh/uv/releases/download/{}/{}",
        UV_VERSION, archive
    );

    // Create the directory if it doesn't exist
    std::fs::create_dir_all(&path).map_err(Error::IoError)?;

    // Download the file
    let response = reqwest::get(url)
        .await
        .map_err(|e| Error::Other(e.to_string()))?;

    let bytes = response
        .bytes()
        .await
        .map_err(|e| Error::Other(e.to_string()))?;

    // Determine archive type from extension
    if archive.ends_with(".tar.gz") {
        let cursor = std::io::Cursor::new(bytes);
        let tar = GzipDecoder::new(cursor);

        // Extract the tar.gz archive
        Archive::new(tar).unpack(path).await?;

        let package_name = extract_package_name(archive.clone());
        Ok(path.join(package_name).join("uv"))
    } else if archive.ends_with(".zip") {
        // Write zip data to a temporary file since async-zip works with files
        let temp_path = path.join("temp.zip");
        tokio::fs::write(&temp_path, bytes).await?;

        // Open the zip file using seek reader with compression support
        let file = tokio::fs::File::open(&temp_path).await?;
        let mut zip = ZipFileReader::with_tokio(file)
            .await
            .map_err(|e| Error::Other(format!("Failed to open zip file: {}", e)))?;

        let package_name = extract_package_name(archive.clone());
        let uv_path = "uv".to_string();
        let uv_exe_path = "uv.exe".to_string();

        // Find the UV executable entry
        let entries = zip.file().entries();
        let entry_index = entries
            .iter()
            .enumerate()
            .find(|(_, entry)| {
                let name = entry.filename().as_str().unwrap_or("");
                name == uv_path || name == uv_exe_path
            })
            .map(|(index, _)| index)
            .ok_or_else(|| Error::Other("UV executable not found in archive".to_string()))?;

        // Create the package directory
        let target_dir = path.join(&package_name);
        std::fs::create_dir_all(&target_dir)?;

        // Extract the file with proper error handling for compression
        let filename = entries[entry_index]
            .filename()
            .as_str()
            .unwrap_or("uv")
            .to_string();
        let is_exe = filename.ends_with(".exe");
        let target_path = target_dir.join(if is_exe { "uv.exe" } else { "uv" });

        let mut reader = zip.reader_with_entry(entry_index).await.map_err(|e| {
            Error::Other(format!(
                "Failed to create entry reader for {}: {}",
                filename, e
            ))
        })?;
        let mut file = tokio::fs::File::create(&target_path).await?;

        // Manually copy data since ZipEntryReader doesn't implement AsyncRead
        let mut buffer = [0u8; 8192];
        let mut total_bytes = 0;
        loop {
            let bytes_read = reader
                .read(&mut buffer)
                .await
                .map_err(|e| Error::Other(format!("Failed to read from zip entry: {}", e)))?;
            if bytes_read == 0 {
                break;
            }
            tokio::io::AsyncWriteExt::write_all(&mut file, &buffer[..bytes_read])
                .await
                .map_err(|e| Error::Other(format!("Failed to write to output file: {}", e)))?;
            total_bytes += bytes_read;
        }

        debug!(
            "Successfully extracted {} bytes to {:?}",
            total_bytes, target_path
        );

        // Make the file executable on Unix systems
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let mut perms = std::fs::metadata(&target_path)?.permissions();
            perms.set_mode(0o755);
            std::fs::set_permissions(&target_path, perms)?;
        }

        // Clean up temporary zip file
        tokio::fs::remove_file(temp_path).await?;

        Ok(target_path)
    } else {
        return Err(Error::Other(format!(
            "Unsupported archive format: {}",
            archive
        )));
    }
}

pub async fn download_uv_for_arch(path: &PathBuf) -> Result<PathBuf, Error> {
    debug!("Starting download of UV for current architecture");
    let archive = ArchiveSelector::get_archive_name().await?;
    let path = download_uv_archive(path, archive).await?;
    debug!("Downloaded UV to: {:?}", path);
    Ok(path)
}

async fn find_uv_binary() -> Option<PathBuf> {
    if let Ok(default_path) = get_default_uv_bin_dir() {
        // Check if the default path exists
        if default_path.exists() {
            let uv_path = default_path.join("uv");
            if uv_path.exists() {
                return Some(uv_path);
            }
        }
    }

    None
}

pub async fn find_or_setup_uv() -> Result<PathBuf, Error> {
    // We only allow setup in the process space at a given time.
    let _guard = get_global_lock().lock().await;

    // If we get here, uv wasn't found in PATH, so let's download it
    if let Some(path) = find_uv_binary().await {
        debug!("UV binary found at {:?}", path);
        Ok(path)
    } else {
        let path = get_default_uv_bin_dir()?;
        debug!("UV binary not found in PATH, setting up UV at {:?}", path);

        // Create the directory if it doesn't exist
        std::fs::create_dir_all(&path).map_err(Error::IoError)?;

        let parent = path
            .parent()
            .ok_or_else(|| Error::NotFound("Parent directory not found".to_string()))?
            .to_path_buf();

        // We download this code to the UV directory
        let exe = download_uv_for_arch(&parent).await?;

        // Target is the UV binary we want.
        let target = path.join("uv");

        // Copy the `uv` binary into the default directory
        tokio::fs::copy(&exe, &target).await?;

        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let mut perms = std::fs::metadata(&target)?.permissions();
            perms.set_mode(0o755);
            std::fs::set_permissions(&target, perms)?;
        }

        debug!("Copied UV binary from {:?} to {:?}", exe, target);

        Ok(target)
    }
}
