use crate::Error;
use std::fs;
use std::path::Path;
use tower_package::is_bun_script;

pub struct TowerfileGenerator;

impl TowerfileGenerator {
    /// Generates a Towerfile from the project file in `dir`: pyproject.toml when there is one,
    /// otherwise package.json for a bun app.
    pub fn from_dir(dir: &Path, script_path: Option<&str>) -> Result<String, Error> {
        let pyproject_path = dir.join("pyproject.toml");
        if pyproject_path.exists() {
            return Self::from_pyproject(pyproject_path.to_str(), script_path);
        }

        let package_json_path = dir.join("package.json");
        if package_json_path.exists() {
            return Self::from_package_json(package_json_path.to_str(), script_path);
        }

        Err(Error::ProjectFileNotFound {
            dir: dir.display().to_string(),
        })
    }

    pub fn from_package_json(
        package_json_path: Option<&str>,
        script_path: Option<&str>,
    ) -> Result<String, Error> {
        let package_json_path = package_json_path.unwrap_or("package.json");
        let package_dir = Path::new(package_json_path)
            .parent()
            .unwrap_or(Path::new("."));

        if !Path::new(package_json_path).exists() {
            return Err(Error::PackageJsonNotFound {
                path: package_json_path.to_string(),
            });
        }

        let content = fs::read_to_string(package_json_path)?;
        let package: serde_json::Value = serde_json::from_str(&content)
            .map_err(|source| Error::InvalidPackageJson { source })?;

        // An npm scope (`@acme/report`) isn't part of the app's name.
        let app_name = package
            .get("name")
            .and_then(|n| n.as_str())
            .map(|n| {
                n.strip_prefix('@')
                    .and_then(|scoped| scoped.split_once('/'))
                    .map_or(n, |(_, name)| name)
            })
            .filter(|n| !n.is_empty())
            .unwrap_or("my-app");

        let description = package
            .get("description")
            .and_then(|d| d.as_str())
            .unwrap_or("");

        let script = script_path
            .map(String::from)
            .or_else(|| Self::find_bun_script(package_dir, &package))
            .unwrap_or_else(|| "./index.ts".to_string());

        let towerfile = toml::toml! {
            [app]
            name = app_name
            script = script
            source = []
            description = description
            runtime = "bun"
        };

        Ok(toml::to_string(&towerfile)?)
    }

    /// The first runnable file named by package.json (`module`, `main`, then the `start`
    /// script), then a conventional entry point, then any JS/TS file in `dir`.
    fn find_bun_script(dir: &Path, package: &serde_json::Value) -> Option<String> {
        let start_script = package
            .get("scripts")
            .and_then(|scripts| scripts.get("start"))
            .and_then(|start| start.as_str())
            .unwrap_or("");

        let declared = ["module", "main"]
            .into_iter()
            .filter_map(|field| package.get(field).and_then(|v| v.as_str()))
            .chain(start_script.split_whitespace());

        let conventional = [
            "index.ts",
            "main.ts",
            "src/index.ts",
            "src/main.ts",
            "index.js",
            "main.js",
        ];

        declared
            .chain(conventional)
            .map(|candidate| candidate.trim_start_matches("./"))
            // `main` often names a build output that doesn't exist yet.
            .find(|candidate| is_bun_script(candidate) && dir.join(candidate).is_file())
            .map(|candidate| format!("./{}", candidate))
            .or_else(|| Self::find_any_bun_file(dir))
    }

    fn find_any_bun_file(dir: &Path) -> Option<String> {
        let mut files: Vec<String> = fs::read_dir(dir)
            .ok()?
            .flatten()
            .filter(|entry| entry.path().is_file())
            .filter_map(|entry| entry.file_name().to_str().map(String::from))
            // Type declarations and tool configs are never the app.
            .filter(|name| {
                is_bun_script(name) && !name.ends_with(".d.ts") && !name.contains(".config.")
            })
            .collect();
        files.sort();
        files.into_iter().next().map(|name| format!("./{}", name))
    }

    pub fn from_pyproject(
        pyproject_path: Option<&str>,
        script_path: Option<&str>,
    ) -> Result<String, Error> {
        let pyproject_path = pyproject_path.unwrap_or("pyproject.toml");
        let pyproject_dir = Path::new(pyproject_path).parent().unwrap_or(Path::new("."));

        if !Path::new(pyproject_path).exists() {
            return Err(Error::PyprojectNotFound {
                path: pyproject_path.to_string(),
            });
        }

        let content = fs::read_to_string(pyproject_path)?;
        let pyproject: serde_json::Value = toml::from_str(&content)?;

        let project = pyproject
            .get("project")
            .ok_or(Error::MissingProjectSection)?;

        let app_name = project
            .get("name")
            .and_then(|n| n.as_str())
            .unwrap_or("my-app");

        let description = project
            .get("description")
            .and_then(|d| d.as_str())
            .unwrap_or("");

        let script = script_path
            .map(String::from)
            .or_else(|| Self::find_main_script(pyproject_dir))
            .unwrap_or_else(|| "./main.py".to_string());

        let towerfile = toml::toml! {
            [app]
            name = app_name
            script = script
            source = []
            description = description
        };

        Ok(toml::to_string(&towerfile)?)
    }

    fn find_main_script(dir: &Path) -> Option<String> {
        Self::find_script_from_pyproject(dir)
            .or_else(|| Self::find_script_with_main(dir))
            .or_else(|| Self::find_common_script(dir))
            .or_else(|| Self::find_any_python_file(dir))
    }

    fn find_common_script(dir: &Path) -> Option<String> {
        ["main.py", "app.py", "run.py", "task.py"]
            .into_iter()
            .find(|&candidate| dir.join(candidate).exists())
            .map(|candidate| format!("./{}", candidate))
    }

    fn find_script_from_pyproject(dir: &Path) -> Option<String> {
        let content = fs::read_to_string(dir.join("pyproject.toml")).ok()?;
        let pyproject: serde_json::Value = toml::from_str(&content).ok()?;

        let script_path = pyproject
            .get("project")?
            .get("scripts")?
            .as_object()?
            .values()
            .next()?
            .as_str()?;

        let module = script_path.split(':').next()?;
        let py_file = format!("{}.py", module.replace('.', "/"));

        dir.join(&py_file)
            .exists()
            .then(|| format!("./{}", py_file))
    }

    fn get_python_files(dir: &Path) -> Vec<String> {
        fs::read_dir(dir)
            .ok()
            .into_iter()
            .flat_map(|entries| entries.flatten())
            .filter_map(|entry| entry.file_name().to_str().map(String::from))
            .filter(|name| name.ends_with(".py"))
            .collect()
    }

    fn find_script_with_main(dir: &Path) -> Option<String> {
        Self::get_python_files(dir)
            .into_iter()
            .find(|name| {
                fs::read_to_string(dir.join(name))
                    .map(|content| content.contains("if __name__ == \"__main__\":"))
                    .unwrap_or(false)
            })
            .map(|name| format!("./{}", name))
    }

    fn find_any_python_file(dir: &Path) -> Option<String> {
        Self::get_python_files(dir)
            .into_iter()
            .next()
            .map(|name| format!("./{}", name))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    fn create_test_env() -> TempDir {
        TempDir::new().expect("Failed to create temp dir")
    }

    #[test]
    fn test_from_pyproject_basic() {
        let temp_dir = create_test_env();
        let pyproject_path = temp_dir.path().join("pyproject.toml");
        let main_py_path = temp_dir.path().join("main.py");

        fs::write(
            &pyproject_path,
            r#"
[project]
name = "test-project"
description = "A test project"
"#,
        )
        .unwrap();

        fs::write(&main_py_path, "# test script").unwrap();

        let result =
            TowerfileGenerator::from_pyproject(Some(pyproject_path.to_str().unwrap()), None)
                .unwrap();

        assert!(result.contains(r#"name = "test-project""#));
        assert!(result.contains(r#"description = "A test project""#));
        assert!(result.contains(r#"source = []"#));
    }

    #[test]
    fn test_from_pyproject_with_custom_script() {
        let temp_dir = create_test_env();
        let pyproject_path = temp_dir.path().join("pyproject.toml");

        fs::write(
            &pyproject_path,
            r#"
[project]
name = "custom-script-project"
"#,
        )
        .unwrap();

        let result = TowerfileGenerator::from_pyproject(
            Some(pyproject_path.to_str().unwrap()),
            Some("./run.py"),
        )
        .unwrap();

        assert!(result.contains(r#"name = "custom-script-project""#));
        assert!(result.contains(r#"script = "./run.py""#));
    }

    #[test]
    fn test_from_pyproject_missing_file() {
        let result =
            TowerfileGenerator::from_pyproject(Some("/nonexistent/path/pyproject.toml"), None);
        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("pyproject.toml not found"));
    }

    #[test]
    fn test_from_pyproject_no_project_section() {
        let temp_dir = create_test_env();
        let pyproject_path = temp_dir.path().join("pyproject.toml");

        fs::write(
            &pyproject_path,
            r#"
[build-system]
requires = ["setuptools"]
"#,
        )
        .unwrap();

        let result =
            TowerfileGenerator::from_pyproject(Some(pyproject_path.to_str().unwrap()), None);
        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("No [project] section found"));
    }

    #[test]
    fn test_find_script_from_pyproject() {
        let temp_dir = create_test_env();

        // Create pyproject.toml with script entry
        fs::write(
            temp_dir.path().join("pyproject.toml"),
            r#"
[project]
name = "test-project"

[project.scripts]
my-script = "src.main:main"
"#,
        )
        .unwrap();

        // Create the referenced script file
        fs::create_dir_all(temp_dir.path().join("src")).unwrap();
        fs::write(temp_dir.path().join("src/main.py"), "def main(): pass").unwrap();

        let result = TowerfileGenerator::find_script_from_pyproject(temp_dir.path());
        assert_eq!(result, Some("./src/main.py".to_string()));
    }

    #[test]
    fn test_find_script_from_pyproject_no_file() {
        let temp_dir = create_test_env();

        let result = TowerfileGenerator::find_script_from_pyproject(temp_dir.path());
        assert_eq!(result, None);
    }

    #[test]
    fn test_find_script_with_main() {
        let temp_dir = create_test_env();

        // Create files with and without __main__
        fs::write(temp_dir.path().join("script1.py"), "print('hello')").unwrap();
        fs::write(
            temp_dir.path().join("script2.py"),
            r#"
def main():
    print("hello")

if __name__ == "__main__":
    main()
"#,
        )
        .unwrap();
        fs::write(temp_dir.path().join("script3.py"), "import sys").unwrap();

        let result = TowerfileGenerator::find_script_with_main(temp_dir.path());
        assert_eq!(result, Some("./script2.py".to_string()));
    }

    #[test]
    fn test_find_main_script_priority() {
        let temp_dir = create_test_env();

        // Create pyproject.toml with script entry (highest priority)
        fs::write(
            temp_dir.path().join("pyproject.toml"),
            r#"
[project.scripts]
cli = "main:run"
"#,
        )
        .unwrap();
        fs::write(
            temp_dir.path().join("main.py"),
            r#"
def run():
    pass

if __name__ == "__main__":
    run()
"#,
        )
        .unwrap();

        // Also create other files that should be lower priority
        fs::write(
            temp_dir.path().join("app.py"),
            r#"
if __name__ == "__main__":
    print("app")
"#,
        )
        .unwrap();

        let result = TowerfileGenerator::find_main_script(temp_dir.path());
        assert_eq!(result, Some("./main.py".to_string()));
    }

    /// Generates from `package_json` in a fresh dir holding `files`, and parses the result back
    /// so it must also pass Towerfile validation.
    fn generate_from_package_json(
        package_json: &str,
        files: &[&str],
        script_path: Option<&str>,
    ) -> tower_package::Towerfile {
        let temp_dir = create_test_env();
        let package_json_path = temp_dir.path().join("package.json");
        fs::write(&package_json_path, package_json).unwrap();
        for file in files {
            let path = temp_dir.path().join(file);
            fs::create_dir_all(path.parent().unwrap()).unwrap();
            fs::write(path, "console.log('hello');").unwrap();
        }

        let content = TowerfileGenerator::from_package_json(
            Some(package_json_path.to_str().unwrap()),
            script_path,
        )
        .unwrap();
        tower_package::Towerfile::from_toml(&content).unwrap()
    }

    #[test]
    fn test_from_package_json_bun_init() {
        // What `bun init -y` writes.
        let towerfile = generate_from_package_json(
            r#"{
  "name": "my-report",
  "module": "index.ts",
  "type": "module",
  "private": true,
  "scripts": {
    "typecheck": "bun check"
  },
  "devDependencies": {
    "@types/bun": "latest"
  },
  "peerDependencies": {
    "typescript": "^7"
  }
}"#,
            &["index.ts"],
            None,
        );

        assert_eq!(towerfile.app.name, "my-report");
        assert_eq!(towerfile.app.script, "./index.ts");
        assert_eq!(towerfile.app.runtime.as_deref(), Some("bun"));
    }

    #[test]
    fn test_from_package_json_drops_the_npm_scope() {
        let towerfile = generate_from_package_json(
            r#"{"name": "@acme/report", "description": "Weekly report"}"#,
            &["index.ts"],
            None,
        );

        assert_eq!(towerfile.app.name, "report");
        assert_eq!(towerfile.app.description.as_deref(), Some("Weekly report"));
    }

    #[test]
    fn test_from_package_json_skips_a_main_that_does_not_exist() {
        let towerfile = generate_from_package_json(
            r#"{"name": "app", "main": "dist/index.js"}"#,
            &["src/index.ts"],
            None,
        );

        assert_eq!(towerfile.app.script, "./src/index.ts");
    }

    #[test]
    fn test_from_package_json_reads_the_start_script() {
        let towerfile = generate_from_package_json(
            r#"{"name": "app", "scripts": {"start": "bun run --watch ./src/job.ts"}}"#,
            &["src/job.ts", "index.ts"],
            None,
        );

        assert_eq!(towerfile.app.script, "./src/job.ts");
    }

    #[test]
    fn test_from_package_json_falls_back_to_any_script_file() {
        let towerfile = generate_from_package_json(
            r#"{"name": "app"}"#,
            &["env.d.ts", "vite.config.ts", "job.ts"],
            None,
        );

        assert_eq!(towerfile.app.script, "./job.ts");
    }

    #[test]
    fn test_from_package_json_with_custom_script() {
        let towerfile = generate_from_package_json(
            r#"{"name": "app", "module": "index.ts"}"#,
            &["index.ts"],
            Some("./run.ts"),
        );

        assert_eq!(towerfile.app.script, "./run.ts");
    }

    #[test]
    fn test_from_package_json_errors() {
        let missing =
            TowerfileGenerator::from_package_json(Some("/nonexistent/path/package.json"), None);
        assert!(missing
            .unwrap_err()
            .to_string()
            .contains("package.json not found"));

        let temp_dir = create_test_env();
        let package_json_path = temp_dir.path().join("package.json");
        fs::write(&package_json_path, "{ not json").unwrap();
        let invalid =
            TowerfileGenerator::from_package_json(Some(package_json_path.to_str().unwrap()), None);
        assert!(invalid
            .unwrap_err()
            .to_string()
            .contains("Failed to parse package.json"));
    }

    #[test]
    fn test_from_dir_prefers_pyproject() {
        let temp_dir = create_test_env();
        fs::write(
            temp_dir.path().join("pyproject.toml"),
            "[project]\nname = \"python-app\"\n",
        )
        .unwrap();
        fs::write(temp_dir.path().join("main.py"), "print('hello')").unwrap();
        fs::write(
            temp_dir.path().join("package.json"),
            r#"{"name": "js-tools"}"#,
        )
        .unwrap();

        let content = TowerfileGenerator::from_dir(temp_dir.path(), None).unwrap();
        let towerfile = tower_package::Towerfile::from_toml(&content).unwrap();

        assert_eq!(towerfile.app.name, "python-app");
        assert_eq!(towerfile.app.runtime, None);
    }

    #[test]
    fn test_from_dir_uses_package_json_without_pyproject() {
        let temp_dir = create_test_env();
        fs::write(
            temp_dir.path().join("package.json"),
            r#"{"name": "js-app", "module": "index.ts"}"#,
        )
        .unwrap();
        fs::write(temp_dir.path().join("index.ts"), "console.log('hello');").unwrap();

        let content = TowerfileGenerator::from_dir(temp_dir.path(), None).unwrap();
        let towerfile = tower_package::Towerfile::from_toml(&content).unwrap();

        assert_eq!(towerfile.app.name, "js-app");
        assert_eq!(towerfile.app.runtime.as_deref(), Some("bun"));
    }

    #[test]
    fn test_from_dir_without_a_project_file() {
        let temp_dir = create_test_env();

        let err = TowerfileGenerator::from_dir(temp_dir.path(), None).unwrap_err();
        assert!(err
            .to_string()
            .contains("No pyproject.toml or package.json found"));
    }
}
