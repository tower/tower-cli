#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Context {
    /// runid is the ID of the run in the current context.
    pub runid: Option<String>,
    /// runner_id is the ID of the runner instance in the current context.
    pub runner_id: String,
}

impl Context {
    pub fn new(runner_id: String) -> Self {
        Self {
            runid: None,
            runner_id,
        }
    }

    pub fn with_runid(mut self, runid: &str) -> Self {
        self.runid = Some(runid.to_string());
        self
    }
}
