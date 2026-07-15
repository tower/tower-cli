use std::io::{self, IsTerminal};

use tower_telemetry::debug;

use crate::output::{self, Out};

pub(crate) struct BetaFeature {
    id: &'static str,
    message: &'static str,
    docs_url: Option<&'static str>,
}

impl BetaFeature {
    pub fn short_about(&self, description: &str) -> String {
        format!("{description} [beta]")
    }

    pub fn notice(&self) -> String {
        match self.docs_url {
            Some(url) => format!("{} Learn more: {url}", self.message),
            None => self.message.to_string(),
        }
    }
}

pub(crate) const STORAGE_BETA_MESSAGE: &str = "Tower Storage is in beta. Core functionality is stable, but some featues and interfaces might change before general availability.";

pub(crate) const STORAGE: BetaFeature = BetaFeature {
    id: "storage-beta-v1",
    message: STORAGE_BETA_MESSAGE,
    docs_url: None,
};

pub(crate) fn notify_once(out: &Out, feature: &BetaFeature) {
    let stderr_is_terminal = io::stderr().is_terminal();

    if !should_notify(out.interactive(), out.foreground(), stderr_is_terminal) {
        return;
    }

    match config::claim_notice(feature.id) {
        Ok(true) => output::notice_to_stderr("Beta:", &feature.notice()),
        Ok(false) => {}
        Err(err) => debug!("Failed to persist CLI notice {}: {}", feature.id, err),
    }
}

/// The notice only goes out for a foreground CLI driving an interactive terminal:
/// human output on a stdout TTY (never JSON or MCP capture), with stderr also a
/// TTY so the notice itself is seen.
fn should_notify(interactive: bool, foreground: bool, stderr_is_terminal: bool) -> bool {
    interactive && foreground && stderr_is_terminal
}

#[cfg(test)]
mod tests {
    use super::{should_notify, BetaFeature, STORAGE, STORAGE_BETA_MESSAGE};

    #[test]
    fn short_about_has_one_beta_suffix() {
        let about = STORAGE.short_about("Use Tower Storage");

        assert_eq!(about, "Use Tower Storage [beta]");
        assert_eq!(about.matches("[beta]").count(), 1);
    }

    #[test]
    fn notice_omits_docs_sentence_without_a_url() {
        let notice = STORAGE.notice();

        assert_eq!(notice, STORAGE_BETA_MESSAGE);
        assert!(!notice.contains("Learn more:"));
    }

    #[test]
    fn notice_includes_docs_url_when_configured() {
        let feature = BetaFeature {
            id: "example-beta-v1",
            message: "Example is in beta. Its interface may change.",
            docs_url: Some("https://example.com/beta"),
        };

        assert_eq!(
            feature.notice(),
            "Example is in beta. Its interface may change. Learn more: https://example.com/beta"
        );
    }

    #[test]
    fn notice_requires_interactive_foreground_and_stderr_terminal() {
        assert!(should_notify(true, true, true));
        // stdout not an interactive terminal (redirected, JSON, or MCP capture)
        assert!(!should_notify(false, true, true));
        // not a foreground CLI (MCP or discarded output)
        assert!(!should_notify(true, false, true));
        // stderr not a terminal
        assert!(!should_notify(true, true, false));
        assert!(!should_notify(false, false, false));
    }
}
