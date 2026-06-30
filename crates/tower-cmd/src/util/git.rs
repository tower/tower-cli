use std::path::Path;
use std::process::Command;
use tower_telemetry::debug;

/// Resolves the commit SHA of `HEAD` for the git worktree containing `dir`, but
/// only when the working tree is clean. Returns `None` when:
///
/// - `dir` is not inside a git worktree,
/// - the working tree has uncommitted changes (we must not claim provenance the
///   bundle doesn't actually have),
/// - `git` isn't installed or any git invocation fails.
///
/// This is used to auto-populate the `X-Tower-Idempotency-Key` header on deploy.
pub fn clean_head_sha(dir: &Path) -> Option<String> {
    if !is_inside_work_tree(dir) {
        debug!("{:?} is not inside a git worktree; skipping idempotency key", dir);
        return None;
    }

    if is_dirty(dir) {
        debug!("git worktree at {:?} is dirty; omitting idempotency key", dir);
        return None;
    }

    let sha = head_sha(dir)?;
    debug!("resolved clean git HEAD {} for {:?}", sha, dir);
    Some(sha)
}

fn git(dir: &Path, args: &[&str]) -> Option<std::process::Output> {
    match Command::new("git").arg("-C").arg(dir).args(args).output() {
        Ok(output) => Some(output),
        Err(err) => {
            debug!("failed to invoke git {:?}: {}", args, err);
            None
        }
    }
}

fn is_inside_work_tree(dir: &Path) -> bool {
    let output = match git(dir, &["rev-parse", "--is-inside-work-tree"]) {
        Some(output) => output,
        None => return false,
    };

    output.status.success()
        && String::from_utf8_lossy(&output.stdout).trim() == "true"
}

/// Returns `true` when there are staged, unstaged, or untracked changes in the
/// worktree. Anything other than a confidently-clean tree is treated as dirty.
fn is_dirty(dir: &Path) -> bool {
    let output = match git(dir, &["status", "--porcelain"]) {
        Some(output) => output,
        None => return true,
    };

    if !output.status.success() {
        return true;
    }

    !String::from_utf8_lossy(&output.stdout).trim().is_empty()
}

fn head_sha(dir: &Path) -> Option<String> {
    let output = git(dir, &["rev-parse", "HEAD"])?;

    if !output.status.success() {
        return None;
    }

    let sha = String::from_utf8_lossy(&output.stdout).trim().to_string();

    if sha.is_empty() {
        None
    } else {
        Some(sha)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::process::Command;
    use tempfile::TempDir;

    fn run(dir: &Path, args: &[&str]) {
        let status = Command::new("git")
            .arg("-C")
            .arg(dir)
            .args(args)
            .status()
            .expect("git invocation failed");
        assert!(status.success(), "git {:?} failed", args);
    }

    fn init_repo() -> TempDir {
        let tmp = TempDir::new().unwrap();
        let dir = tmp.path();
        run(dir, &["init", "--quiet"]);
        run(dir, &["config", "user.email", "test@example.com"]);
        run(dir, &["config", "user.name", "Test User"]);
        tmp
    }

    #[test]
    fn non_git_dir_returns_none() {
        let tmp = TempDir::new().unwrap();
        assert_eq!(clean_head_sha(tmp.path()), None);
    }

    #[test]
    fn clean_tree_returns_head_sha() {
        let tmp = init_repo();
        let dir = tmp.path();
        std::fs::write(dir.join("file.txt"), "hello").unwrap();
        run(dir, &["add", "."]);
        run(dir, &["commit", "--quiet", "-m", "initial"]);

        let sha = clean_head_sha(dir).expect("expected a sha on a clean tree");
        assert_eq!(sha.len(), 40, "expected a full 40-char sha, got {sha}");
    }

    #[test]
    fn dirty_tree_returns_none() {
        let tmp = init_repo();
        let dir = tmp.path();
        std::fs::write(dir.join("file.txt"), "hello").unwrap();
        run(dir, &["add", "."]);
        run(dir, &["commit", "--quiet", "-m", "initial"]);

        // Untracked file makes the tree dirty.
        std::fs::write(dir.join("dirty.txt"), "uncommitted").unwrap();
        assert_eq!(clean_head_sha(dir), None);
    }
}
