use crate::Error;
use std::fs;
use std::path::Path;

pub struct TowerfileGenerator;

impl TowerfileGenerator {
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
}
