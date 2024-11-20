use crate::Error;
use serde::Deserialize;
use std::path::{Path, PathBuf};

#[derive(Deserialize)]
pub struct Parameter{
    #[serde(default)]
    pub name: String,

    #[serde(default)]
    pub description: String,

    #[serde(default)]
    pub default: String,
}

#[derive(Deserialize)]
pub struct App {
    #[serde(default)]
    pub name: String,

    #[serde(default)]
    pub script: String,

    #[serde(default)]
    pub source: Vec<String>,

    #[serde(default)]
    pub schedule: String,
}

#[derive(Deserialize)]
pub struct Towerfile {
    /// base_dir is the directory in which the Towerfile is located. It's always populated by the
    /// parser/application, never by the data.
    #[serde(skip_deserializing)]
    pub base_dir: PathBuf,

    pub app: App,

    #[serde(default)]
    pub parameters: Vec<Parameter>,
}

impl Towerfile {
    pub fn default() -> Self {
        Self {
            base_dir: PathBuf::new(),
            parameters: vec![],
            app: App {
                name: String::from(""),
                script: String::from(""),
                source: vec![],
                schedule: String::from("0 0 * * *"),
            },
        }
    }

    /// from_toml parses a new Towerfile from a TOML string. It's not exposed externally because
    /// the base_dir field always needs to be set after parsing.
    fn from_toml(toml: &str) -> Result<Self, Error> {
        let towerfile: Towerfile = toml::from_str(toml)?;

        if towerfile.app.name.is_empty() {
            return Err(Error::MissingRequiredAppField{ field: "name".to_string() });
        } else {
            Ok(towerfile)
        }
    }

    /// from_path reads a Towerfile from a path and parses it as TOML content.
    pub fn from_path(path: PathBuf) -> Result<Self, Error> {
        if !path.exists() {
            return Err(Error::MissingTowerfile);
        }

        let mut towerfile = Self::from_toml(&std::fs::read_to_string(path.to_path_buf())?)?;
        let parent = path.parent().unwrap_or_else(|| Path::new(".")).to_path_buf();
        towerfile.base_dir = parent;

        Ok(towerfile)
    }

    /// from_local_file looks for a new, local Towerfile in the current working directory.
    pub fn from_local_file() -> Result<Self, Error> {
        Self::from_dir_str(".")
    }

    /// from_dir_str reads a Towerfile from a directory represented by a string. This is useful in
    /// the context of the `tower` CLI, where the user may specify a directory to read the
    /// Towerfile on the command line as an argument or whatever.
    pub fn from_dir_str(dir: &str) -> Result<Self, Error> {
        let dir = PathBuf::from(dir);
        let path = dir.join("Towerfile");

        if !path.exists() {
            Err(Error::MissingTowerfile)
        } else {
            Self::from_path(path)
        }
    }
}

#[cfg(test)]
mod test {
    use std::io::Write;
    use std::path::PathBuf;
    use testutils::fs::TestFile;

    #[test]
    fn test_towerfile_from_toml() {
        let toml = r#"
            [app]
            name = "test"
            script = "./script.py"
            source = ["*.py"]
            schedule = "0 0 * * *"
        "#;

        let towerfile = crate::Towerfile::from_toml(toml).unwrap();
        assert_eq!(towerfile.app.name, "test");
        assert_eq!(towerfile.app.script, "./script.py");
        assert_eq!(towerfile.app.source, vec!["*.py"]);
        assert_eq!(towerfile.app.schedule, "0 0 * * *");
    }

    #[test]
    fn test_towerfile_with_missing_fields_from_toml() {
        let toml = r#"
            [app]
            name = "test"
            script = "./script.py"
            source = ["*.py"]
        "#;

        let towerfile = crate::Towerfile::from_toml(toml).unwrap();
        assert_eq!(towerfile.app.name, "test");
        assert_eq!(towerfile.app.script, "./script.py");
        assert_eq!(towerfile.app.source, vec!["*.py"]);
        assert_eq!(towerfile.app.schedule, "");
    }

    #[test]
    fn test_towerfile_missing_name_field() {
        let toml = r#"
            [app]
            script = "./script.py"
            source = ["*.py"]
        "#;

        let err = crate::Towerfile::from_toml(toml).err().unwrap();
        assert_eq!(err.to_string(), "Missing required app field `name` in Towerfile");
    }

    #[test]
    fn test_returns_error_when_missing_local_towerfile() {
        // this is a bit of a hack to make sure any local Towerfile is indeed gone. Leaks from
        // other tests occassionally.
        std::fs::remove_file("Towerfile").ok();

        // First test case tests for failure mode: There is no local file. A MissingTowerfile error
        // should be returned
        let res = crate::Towerfile::from_local_file();
        assert!(res.is_err());

        let opt = res.err();
        assert!(opt.is_some());

        let err = opt.unwrap();
        assert!(matches!(err, crate::Error::MissingTowerfile));
    }

    #[test]
    fn test_parses_valid_local_towerfile() {
        // Second test case tests for success mode: There is a local file. A Towerfile should be
        // parsed and validly returned.
        let toml = r#"
            [app]
            name = "my-app"
            script = "./script.py"
            source = ["*.py"]
        "#;

        let mut tempfile = TestFile::new("Towerfile").expect("Failed to create temporary file");
        let file = tempfile.file();
        file.write_all(toml.as_bytes()).unwrap();

        let towerfile = crate::Towerfile::from_local_file().expect("Failed to parse Towerfile");
        assert_eq!(towerfile.base_dir, PathBuf::from("."));

        // explicitly drop this file so it's cleaned up when other test cases run.
        drop(tempfile);
    }

    #[test]
    fn test_parses_tempfiles_located_elsewhere() {
        // Second test case tests for success mode: There is a local file. A Towerfile should be
        // parsed and validly returned.
        let toml = r#"
            [app]
            name = "my-app"
            script = "./script.py"
            source = ["*.py"]
        "#;

        let temp_dir = std::env::temp_dir();
        let towerfile_path= temp_dir.join("Towerfile");
        let mut tempfile = TestFile::new(towerfile_path.clone()).unwrap();
        let file = tempfile.file();
        file.write_all(toml.as_bytes()).unwrap();

        let towerfile = crate::Towerfile::from_path(towerfile_path.clone()).unwrap();
        assert_eq!(towerfile.base_dir, temp_dir);

        // explicitly drop this file so it's cleaned up when other test cases run.
        drop(tempfile);
    }

    #[test]
    fn test_parses_parameters() {
        // Second test case tests for success mode: There is a local file. A Towerfile should be
        // parsed and validly returned.
        let toml = r#"
            [app]
            name = "my-app"
            script = "./script.py"
            source = ["*.py"]

            [[parameters]]
            name = "my_first_param"
            description = "Some type of parameter."
            default = ""

            [[parameters]]
            name = "my_second_param"
            description = "Some other type of parameter."
            default = ""
        "#;

        let towerfile = crate::Towerfile::from_toml(toml).unwrap();
        assert_eq!(towerfile.parameters.len(), 2);
        assert_eq!(towerfile.parameters[0].name, "my_first_param");
        assert_eq!(towerfile.parameters[1].name, "my_second_param");
    }
}
