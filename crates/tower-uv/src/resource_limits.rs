/// Subtracted from the detected limit before applying RLIMIT_AS to the child.
const HEADROOM_BYTES: u64 = 5 * 1024 * 1024;

/// Detect the effective memory limit for this environment.
///
/// Returns a byte count the subprocess should be constrained to, leaving
/// headroom for the parent process to report errors.
///
/// Detection order (all unix-only, returns `None` on other platforms):
/// 1. `RLIMIT_AS` — if already set to a finite value, subtract headroom
/// 2. cgroup v2 `memory.max`
/// 3. cgroup v1 `memory.limit_in_bytes`
#[cfg(unix)]
pub fn detect_memory_limit() -> Option<u64> {
    use nix::sys::resource::{getrlimit, Resource};

    if let Ok((soft, _hard)) = getrlimit(Resource::RLIMIT_AS) {
        let unlimited = nix::libc::RLIM_INFINITY;
        if soft != unlimited && soft > HEADROOM_BYTES {
            return Some(soft - HEADROOM_BYTES);
        }
    }

    if let Ok(contents) = std::fs::read_to_string("/sys/fs/cgroup/memory.max") {
        let trimmed = contents.trim();
        if trimmed != "max" {
            if let Ok(limit) = trimmed.parse::<u64>() {
                if limit > HEADROOM_BYTES {
                    return Some(limit - HEADROOM_BYTES);
                }
            }
        }
    }

    const CGROUP_V1_SENTINEL: u64 = 0x7FFF_FFFF_FFFF_F000;
    if let Ok(contents) = std::fs::read_to_string("/sys/fs/cgroup/memory/memory.limit_in_bytes") {
        if let Ok(limit) = contents.trim().parse::<u64>() {
            if limit < CGROUP_V1_SENTINEL && limit > HEADROOM_BYTES {
                return Some(limit - HEADROOM_BYTES);
            }
        }
    }

    None
}

#[cfg(not(unix))]
pub fn detect_memory_limit() -> Option<u64> {
    None
}
