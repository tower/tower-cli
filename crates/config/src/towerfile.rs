use crate::Error;
use serde::Deserialize;

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
