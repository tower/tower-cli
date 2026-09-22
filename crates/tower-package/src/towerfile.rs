use crate::core::Error;
use serde::de::DeserializeOwned;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// Compute sizes accepted by `[app] run_size`. Managed runners apply the size;
/// self-hosted runners ignore it and use their own configured resources. When
/// the Towerfile omits it, the server applies its own default, so this list
/// deliberately has no default of its own.
pub const RUN_SIZES: [&str; 4] = ["basic.xsmall", "basic.small", "basic.medium", "basic.large"];

#[derive(Clone, Deserialize, Serialize, Debug)]
pub struct Parameter {
    #[serde(default)]
    pub name: String,

    #[serde(default)]
    pub description: String,

    #[serde(default)]
    pub default: String,

    #[serde(default)]
    pub hidden: bool,
}

#[derive(Serialize, Debug)]
pub struct App {
    #[serde(default)]
    pub name: String,

    #[serde(default)]
    pub script: String,

    #[serde(default)]
    pub source: Vec<String>,

    #[serde(default)]
    pub schedule: String,

    /// Optional short description of the app. `None` means the Towerfile
    /// didn't set one (and the key is omitted when serializing), which is
    /// distinct from an explicitly empty description.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,

    #[serde(default)]
    pub import_paths: Vec<PathBuf>,

    /// Compute size every run of this app gets, e.g. "basic.medium". `None`
    /// means the Towerfile didn't set one (and the key is omitted when
    /// serializing), leaving the server to apply its default.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub run_size: Option<String>,

    /// Keys under `[app]` that this version of the CLI doesn't model. They are
    /// carried through unchanged so that editing a Towerfile never drops
    /// something a newer server, or the user, put there.
    ///
    /// `flatten` is only used for serializing. Deserializing through it would
    /// buffer the leftover values through serde's generic representation,
    /// which turns TOML datetimes into an inline table with a private marker
    /// key — so `from_table` fills this in from the parsed table directly.
    #[serde(flatten)]
    pub extra: toml::Table,
}

/// take removes `key` from `table` and converts it into `T`, falling back to
/// `T::default()` when the key is absent — the same semantics `#[serde(default)]`
/// gave these fields before unknown keys were preserved. `path` is the dotted
/// location used in error messages.
fn take<T: DeserializeOwned + Default>(
    table: &mut toml::Table,
    key: &str,
    path: &str,
) -> Result<T, Error> {
    match table.remove(key) {
        Some(value) => {
            toml::Value::try_into(value).map_err(|err: toml::de::Error| Error::InvalidTowerfile {
                message: format!("invalid value for `{}`: {}", path, err.message()),
            })
        }
        None => Ok(T::default()),
    }
}

impl App {
    /// from_table builds an App from the parsed `[app]` table. Known keys are
    /// removed and converted; whatever is left over lands in `extra` with its
    /// values untouched.
    pub fn from_table(mut table: toml::Table) -> Result<Self, Error> {
        Ok(App {
            name: take(&mut table, "name", "app.name")?,
            script: take(&mut table, "script", "app.script")?,
            source: take(&mut table, "source", "app.source")?,
            schedule: take(&mut table, "schedule", "app.schedule")?,
            description: take(&mut table, "description", "app.description")?,
            import_paths: take(&mut table, "import_paths", "app.import_paths")?,
            run_size: take(&mut table, "run_size", "app.run_size")?,
            extra: table,
        })
    }
}

impl<'de> Deserialize<'de> for App {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let table = toml::Table::deserialize(deserializer)?;
        App::from_table(table).map_err(<D::Error as serde::de::Error>::custom)
    }
}

#[derive(Serialize, Debug)]
pub struct Towerfile {
    /// file_path is the path to where this file was read on disk. It's always populated by the
    /// parser/application, never by the data.
    #[serde(skip)]
    pub file_path: PathBuf,

    pub app: App,

    #[serde(default)]
    pub parameters: Vec<Parameter>,

    /// Top-level sections other than `[app]` and `[[parameters]]`, e.g. `[build]`.
    /// Preserved verbatim across read → modify → save. See `App::extra` for why
    /// this is filled in by hand rather than through `flatten`.
    #[serde(flatten)]
    pub extra: toml::Table,
}

impl Towerfile {
    /// from_table builds a Towerfile from the parsed document. `[app]` is
    /// required; every other top-level key the CLI doesn't know about is kept
    /// in `extra`.
    pub fn from_table(mut table: toml::Table) -> Result<Self, Error> {
        let app = match table.remove("app") {
            Some(toml::Value::Table(app)) => App::from_table(app)?,
            Some(other) => {
                return Err(Error::InvalidTowerfile {
                    message: format!("`app` must be a table, found {}", other.type_str()),
                })
            }
            None => {
                return Err(Error::InvalidTowerfile {
                    message: "missing `[app]` section".to_string(),
                })
            }
        };

        Ok(Towerfile {
            file_path: PathBuf::new(),
            app,
            parameters: take(&mut table, "parameters", "parameters")?,
            extra: table,
        })
    }
}

impl<'de> Deserialize<'de> for Towerfile {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let table = toml::Table::deserialize(deserializer)?;
        Towerfile::from_table(table).map_err(<D::Error as serde::de::Error>::custom)
    }
}

impl Towerfile {
    pub fn default() -> Self {
        Self {
            file_path: PathBuf::new(),
            parameters: vec![],
            extra: toml::Table::new(),
            app: App {
                name: String::from(""),
                script: String::from(""),
                source: vec![],
                schedule: String::from("0 0 * * *"),
                description: None,
                import_paths: vec![],
                run_size: None,
                extra: toml::Table::new(),
            },
        }
    }

    /// from_toml parses a new Towerfile from a TOML string. It's not exposed externally because
    /// the base_dir field always needs to be set after parsing.
    pub fn from_toml(toml: &str) -> Result<Self, Error> {
        let towerfile: Towerfile = toml::from_str(toml)?;
        towerfile.validate()?;
        Ok(towerfile)
    }

    /// validate checks the semantic rules that TOML parsing alone can't enforce.
    /// It runs both when a Towerfile is read and before one is written back, so a
    /// mutation can't leave an invalid file on disk.
    pub fn validate(&self) -> Result<(), Error> {
        if self.app.name.is_empty() {
            return Err(Error::MissingRequiredAppField {
                field: "name".to_string(),
            });
        }

        if self.app.script.is_empty() {
            return Err(Error::MissingRequiredAppField {
                field: "script".to_string(),
            });
        }

        for import_path in &self.app.import_paths {
            let as_str = import_path.to_string_lossy();
            if as_str.is_empty() {
                return Err(Error::InvalidTowerfile {
                    message: "import_paths entries must not be empty".to_string(),
                });
            }
            // PATH-style separators in a single entry would break PYTHONPATH construction at
            // runtime, since each entry is joined with the platform path separator.
            if as_str.contains(|c: char| c == ':' || c == ';') {
                return Err(Error::InvalidTowerfile {
                    message: format!(
                        "import_paths entry {:?} contains an illegal character (':' or ';')",
                        as_str
                    ),
                });
            }
        }

        if let Some(run_size) = &self.app.run_size {
            // The server rejects unknown sizes at deploy time. Catching it here
            // means the user finds out before the upload rather than after.
            if !RUN_SIZES.contains(&run_size.as_str()) {
                return Err(Error::InvalidTowerfile {
                    message: format!(
                        "run_size {:?} is not a valid size (expected one of: {})",
                        run_size,
                        RUN_SIZES.join(", ")
                    ),
                });
            }
        }

        Ok(())
    }

    /// set_parameter upserts a parameter by lookup name. If a parameter with the given name
    /// exists, it is replaced. Otherwise, the parameter is appended.
    pub fn set_parameter(&mut self, lookup_name: &str, param: Parameter) {
        if let Some(existing) = self.parameters.iter_mut().find(|p| p.name == lookup_name) {
            *existing = param;
        } else {
            self.parameters.push(param);
        }
    }

    /// remove_parameter removes a parameter by name, returning true if it was found
    pub fn remove_parameter(&mut self, name: &str) -> bool {
        let len_before = self.parameters.len();
        self.parameters.retain(|p| p.name != name);
        self.parameters.len() < len_before
    }
}

#[cfg(feature = "native")]
impl Towerfile {
    /// from_path reads a Towerfile from a path and parses it as TOML content.
    pub fn from_path(path: PathBuf) -> Result<Self, crate::error::Error> {
        use crate::error::Error as OuterError;

        if !path.exists() {
            return Err(OuterError::MissingTowerfile);
        }

        let contents =
            std::fs::read_to_string(&path).map_err(|source| OuterError::Io { source })?;
        let mut towerfile = Self::from_toml(&contents)?;
        towerfile.file_path = path;

        Ok(towerfile)
    }

    /// from_local_file looks for a new, local Towerfile in the current working directory.
    pub fn from_local_file() -> Result<Self, crate::error::Error> {
        Self::from_dir_str(".")
    }

    /// from_dir_str reads a Towerfile from a directory represented by a string. This is useful in
    /// the context of the `tower` CLI, where the user may specify a directory to read the
    /// Towerfile on the command line as an argument or whatever.
    pub fn from_dir_str(dir: &str) -> Result<Self, crate::error::Error> {
        Self::from_path(PathBuf::from(dir).join("Towerfile"))
    }

    /// save writes the Towerfile as TOML to the specified path, defaulting to current dir
    pub fn save(&self, path: Option<&std::path::Path>) -> Result<(), crate::error::Error> {
        use crate::error::Error as OuterError;

        self.validate()?;

        let target_path = path.unwrap_or_else(|| std::path::Path::new("Towerfile"));
        let serialized =
            toml::to_string_pretty(self).map_err(|err| OuterError::InvalidTowerfile {
                message: err.to_string(),
            })?;
        std::fs::write(target_path, serialized).map_err(|source| OuterError::Io { source })?;
        Ok(())
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
        assert_eq!(
            err.to_string(),
            "Missing required app field `name` in Towerfile"
        );
    }

    #[ignore]
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
        assert!(matches!(err, crate::error::Error::MissingTowerfile));
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
        assert_eq!(towerfile.file_path, PathBuf::from("./Towerfile"));

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
        let towerfile_path = temp_dir.join("Towerfile");
        let mut tempfile = TestFile::new(towerfile_path.clone()).unwrap();
        let file = tempfile.file();
        file.write_all(toml.as_bytes()).unwrap();

        let towerfile = crate::Towerfile::from_path(towerfile_path.clone()).unwrap();
        assert_eq!(towerfile.file_path, temp_dir.join("Towerfile"));

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
        assert!(!towerfile.parameters[0].hidden);
    }

    #[test]
    fn test_parses_secret_parameters() {
        let toml = r#"
            [app]
            name = "my-app"
            script = "./script.py"
            source = ["*.py"]

            [[parameters]]
            name = "MY_PARAMETER"
            hidden = true
        "#;

        let towerfile = crate::Towerfile::from_toml(toml).unwrap();
        assert_eq!(towerfile.parameters.len(), 1);
        assert_eq!(towerfile.parameters[0].name, "MY_PARAMETER");
        assert!(towerfile.parameters[0].hidden);
    }

    #[test]
    fn test_set_parameter() {
        let mut towerfile = crate::Towerfile::default();
        assert_eq!(towerfile.parameters.len(), 0);

        towerfile.set_parameter(
            "test-param",
            crate::Parameter {
                name: "test-param".to_string(),
                description: "A test parameter".to_string(),
                default: "default-value".to_string(),
                hidden: false,
            },
        );

        assert_eq!(towerfile.parameters.len(), 1);
        assert_eq!(towerfile.parameters[0].name, "test-param");
        assert_eq!(towerfile.parameters[0].description, "A test parameter");
        assert_eq!(towerfile.parameters[0].default, "default-value");
        assert!(!towerfile.parameters[0].hidden);

        // upsert should replace, not duplicate
        towerfile.set_parameter(
            "test-param",
            crate::Parameter {
                name: "test-param".to_string(),
                description: "Updated".to_string(),
                default: "new-value".to_string(),
                hidden: false,
            },
        );

        assert_eq!(towerfile.parameters.len(), 1);
        assert_eq!(towerfile.parameters[0].description, "Updated");
    }

    #[test]
    fn test_remove_parameter() {
        let mut towerfile = crate::Towerfile::default();
        towerfile.set_parameter(
            "param1",
            crate::Parameter {
                name: "param1".to_string(),
                description: "".to_string(),
                default: "".to_string(),
                hidden: false,
            },
        );

        assert!(towerfile.remove_parameter("param1"));
        assert_eq!(towerfile.parameters.len(), 0);
        assert!(!towerfile.remove_parameter("param1"));
    }

    #[test]
    fn test_description_absent_when_not_set() {
        let toml = r#"
            [app]
            name = "test"
            script = "./script.py"
        "#;

        let towerfile = crate::Towerfile::from_toml(toml).unwrap();
        assert_eq!(towerfile.app.description, None);

        // Serializing a Towerfile without a description omits the key.
        let serialized = toml::to_string_pretty(&towerfile).unwrap();
        assert!(!serialized.contains("description"));
    }

    #[test]
    fn test_description_distinguishes_empty_from_absent() {
        let toml = r#"
            [app]
            name = "test"
            script = "./script.py"
            description = ""
        "#;

        let towerfile = crate::Towerfile::from_toml(toml).unwrap();
        assert_eq!(towerfile.app.description, Some(String::new()));
    }

    #[test]
    fn test_description_roundtrips_when_present() {
        let toml = r#"
            [app]
            name = "test"
            script = "./script.py"
            description = "My app"
        "#;

        let towerfile = crate::Towerfile::from_toml(toml).unwrap();
        assert_eq!(towerfile.app.description.as_deref(), Some("My app"));

        let serialized = toml::to_string_pretty(&towerfile).unwrap();
        assert!(serialized.contains(r#"description = "My app""#));
    }

    #[test]
    fn test_run_size_absent_when_not_set() {
        let toml = r#"
            [app]
            name = "test"
            script = "./script.py"
        "#;

        let towerfile = crate::Towerfile::from_toml(toml).unwrap();
        assert_eq!(towerfile.app.run_size, None);

        // An unset run_size must not be written into the user's Towerfile, so
        // the server keeps applying its own default.
        let serialized = toml::to_string_pretty(&towerfile).unwrap();
        assert!(!serialized.contains("run_size"));
    }

    #[test]
    fn test_run_size_accepts_every_known_size() {
        for size in crate::RUN_SIZES {
            let toml = format!(
                r#"
                [app]
                name = "test"
                script = "./script.py"
                run_size = "{}"
            "#,
                size
            );

            let towerfile = crate::Towerfile::from_toml(&toml).unwrap();
            assert_eq!(towerfile.app.run_size.as_deref(), Some(size));
        }
    }

    #[test]
    fn test_run_size_rejects_unknown_size() {
        let toml = r#"
            [app]
            name = "test"
            script = "./script.py"
            run_size = "basic.enormous"
        "#;

        let err = crate::Towerfile::from_toml(toml).unwrap_err();
        let message = err.to_string();
        assert!(message.contains("basic.enormous"), "was: {}", message);
        assert!(message.contains("basic.medium"), "was: {}", message);
    }

    #[test]
    fn test_run_size_is_case_and_prefix_sensitive() {
        // The size names are matched exactly; near misses must not slip through
        // to the server.
        for bad in ["medium", "basic.Medium", "BASIC.MEDIUM", " basic.medium"] {
            let toml = format!(
                r#"
                [app]
                name = "test"
                script = "./script.py"
                run_size = "{}"
            "#,
                bad
            );

            assert!(
                crate::Towerfile::from_toml(&toml).is_err(),
                "expected {:?} to be rejected",
                bad
            );
        }
    }

    #[test]
    fn test_run_size_survives_read_modify_write() {
        // Regression: every MCP write round-trips the Towerfile through this
        // struct, so a field that isn't modelled is silently dropped from the
        // user's file. Editing an unrelated field must leave run_size intact.
        let toml = r#"
            [app]
            name = "test"
            script = "./script.py"
            run_size = "basic.large"
        "#;

        let mut towerfile = crate::Towerfile::from_toml(toml).unwrap();
        towerfile.app.description = Some("edited".to_string());

        let serialized = toml::to_string_pretty(&towerfile).unwrap();
        let reparsed = crate::Towerfile::from_toml(&serialized).unwrap();

        assert_eq!(reparsed.app.run_size.as_deref(), Some("basic.large"));
        assert_eq!(reparsed.app.description.as_deref(), Some("edited"));
    }

    #[test]
    fn test_save_refuses_to_persist_an_invalid_run_size() {
        // MCP edits mutate the struct and write it straight back, so save() has
        // to hold the mutation to the same rules as a read. Otherwise a bad
        // value lands on disk and the user only finds out on the next read.
        let toml = r#"
            [app]
            name = "test"
            script = "./script.py"
            run_size = "basic.small"
        "#;

        let mut towerfile = crate::Towerfile::from_toml(toml).unwrap();
        towerfile.app.run_size = Some("basic.enormous".to_string());

        let tempfile =
            TestFile::new("Towerfile-save-invalid").expect("Failed to create temporary file");
        let path = PathBuf::from("Towerfile-save-invalid");

        let err = towerfile.save(Some(&path)).unwrap_err();
        assert!(err.to_string().contains("basic.enormous"), "was: {}", err);

        // The file must be untouched, not half-written.
        assert_eq!(std::fs::read_to_string(&path).unwrap(), "");

        drop(tempfile);
    }

    #[test]
    fn test_unknown_keys_survive_read_modify_write() {
        // The struct is not the whole schema: the server reads the raw
        // Towerfile, and users add sections the CLI doesn't know about. An
        // MCP edit of one field must not delete any of that.
        let toml = r#"
            [app]
            name = "test"
            script = "./script.py"
            python_version = "3.12"

            [build]
            python = "3.11"
        "#;

        let mut towerfile = crate::Towerfile::from_toml(toml).unwrap();
        assert_eq!(towerfile.app.extra["python_version"].as_str(), Some("3.12"));
        assert_eq!(towerfile.extra["build"]["python"].as_str(), Some("3.11"));

        towerfile.app.description = Some("edited".to_string());

        let serialized = toml::to_string_pretty(&towerfile).unwrap();
        let reparsed = crate::Towerfile::from_toml(&serialized).unwrap();

        assert_eq!(reparsed.app.description.as_deref(), Some("edited"));
        assert_eq!(reparsed.app.extra["python_version"].as_str(), Some("3.12"));
        assert_eq!(reparsed.extra["build"]["python"].as_str(), Some("3.11"));
    }

    #[test]
    fn test_unknown_keys_are_flattened_not_nested() {
        // A plain Towerfile must serialize exactly as before: no `extra` key
        // or `[extra]` table may leak into the user's file.
        let toml = r#"
            [app]
            name = "test"
            script = "./script.py"
        "#;

        let towerfile = crate::Towerfile::from_toml(toml).unwrap();
        assert!(towerfile.extra.is_empty());
        assert!(towerfile.app.extra.is_empty());

        let serialized = toml::to_string_pretty(&towerfile).unwrap();
        assert!(!serialized.contains("extra"), "was: {}", serialized);
    }

    #[test]
    fn test_unknown_datetime_values_survive_round_trip() {
        // TOML datetimes take a special path through serde; make sure they
        // don't get mangled when buffered through the flattened map.
        let toml = r#"
            [app]
            name = "test"
            script = "./script.py"

            [release]
            date = 2024-06-01
            at = 2024-06-01T12:30:00Z
        "#;

        let towerfile = crate::Towerfile::from_toml(toml).unwrap();
        assert!(towerfile.extra["release"]["date"].is_datetime());
        assert!(towerfile.extra["release"]["at"].is_datetime());

        // Assert on the written text, not the re-parsed value: toml's Value
        // visitor recognises its own private marker key on the way back in, so
        // a corrupted `date = { "$__toml_private_datetime" = ... }` would
        // silently round-trip into a datetime again and hide the damage.
        let serialized = toml::to_string_pretty(&towerfile).unwrap();
        assert!(
            serialized.contains("date = 2024-06-01"),
            "datetime was not written as a TOML literal:\n{}",
            serialized
        );
        assert!(
            !serialized.contains("$__toml_private_datetime"),
            "private marker leaked into the file:\n{}",
            serialized
        );
    }

    #[test]
    fn test_wrong_type_for_known_key_is_rejected() {
        let toml = r#"
            [app]
            name = 123
            script = "./script.py"
        "#;

        let err = crate::Towerfile::from_toml(toml).unwrap_err().to_string();
        assert!(err.contains("app.name"), "was: {}", err);
    }

    #[test]
    fn test_missing_app_section_is_rejected() {
        let err = crate::Towerfile::from_toml("[build]\npython = \"3.11\"\n")
            .unwrap_err()
            .to_string();
        assert!(err.contains("[app]"), "was: {}", err);
    }

    #[test]
    fn test_roundtrip_serialization() {
        let original_toml = r#"[app]
name = "test-app"
script = "./script.py"
source = ["*.py", "src/*.py"]
description = "A test application"
schedule = "0 9 * * *"

[[parameters]]
name = "param1"
description = "First parameter"
default = "value1"

[[parameters]]
name = "param2"
description = "Second parameter"
default = "value2"
"#;

        let towerfile = crate::Towerfile::from_toml(original_toml).unwrap();
        let serialized = toml::to_string_pretty(&towerfile).unwrap();
        let reparsed = crate::Towerfile::from_toml(&serialized).unwrap();

        assert_eq!(towerfile.app.name, reparsed.app.name);
        assert_eq!(towerfile.app.script, reparsed.app.script);
        assert_eq!(towerfile.app.source, reparsed.app.source);
        assert_eq!(towerfile.parameters.len(), reparsed.parameters.len());
        assert_eq!(towerfile.parameters[0].name, reparsed.parameters[0].name);
    }
}
