#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Context {
    /// runid is the ID of the run in the current context.
    pub runid: Option<String>,
}

impl Context {
    pub fn from_runid(runid: String) -> Self {
        Self {
            runid: Some(runid),
        }
    }

    pub fn new() -> Self {
        Self { runid: None }
    }
}
