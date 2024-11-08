use crate::Error;
use serde::Deserialize;
use std::path::PathBuf;

#[derive(Deserialize)]
pub struct App {
    pub name: String,
    pub script: String,
    pub source: Vec<String>,
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
        Ok(towerfile)
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
}
