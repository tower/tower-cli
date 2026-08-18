use crate::output;

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

    pub fn notify_once(&self) {
        output::notice_once(self.id, "Beta:", &self.notice());
    }
}

pub(crate) const STORAGE_BETA_MESSAGE: &str = "Tower Storage is in beta. Core functionality is stable, but some featues and interfaces might change before general availability.";

pub(crate) const STORAGE: BetaFeature = BetaFeature {
    id: "storage-beta-v1",
    message: STORAGE_BETA_MESSAGE,
    docs_url: None,
};

#[cfg(test)]
mod tests {
    use super::{BetaFeature, STORAGE, STORAGE_BETA_MESSAGE};

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
}
