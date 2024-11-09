use crate::Error;
use serde::Deserialize;
use std::path::PathBuf;

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
    pub app: App,
}

impl Towerfile {
    pub fn default() -> Self {
        Self {
            app: App {
                name: String::from(""),
                script: String::from(""),
                source: vec![],
                schedule: String::from("0 0 * * *"),
            },
        }
    }

    pub fn from_toml(toml: &str) -> Result<Self, Error> {
        let towerfile: Towerfile = toml::from_str(toml)?;

        if towerfile.app.name.is_empty() {
            return Err(Error::MissingRequiredAppField{ field: "name".to_string() });
        } else {
            Ok(towerfile)
        }
    }

    pub fn from_path(path: PathBuf) -> Result<Self, Error> {
        Self::from_toml(&std::fs::read_to_string(path)?)
    }

    pub fn from_local_file() -> Result<Self, Error> {
        let dir = std::env::current_dir()?;
        let path = dir.join("Towerfile");

        if !path.exists() {
            Err(Error::MissingTowerfile)
        } else {
            Self::from_path(path)
        }
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

mod test {
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
}
