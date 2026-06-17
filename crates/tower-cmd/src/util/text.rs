pub fn join_with_and(eles: Vec<String>) -> String {
    match eles.len() {
        0 | 1 | 2 => {
            return eles.join(" and ");
        }
        l => {
            let butlast: Vec<_> = eles.iter().cloned().take(l - 1).collect();
            let last = eles.iter().last().unwrap();

            return format!("{}, and {}", butlast.join(", "), last);
        }
    }
}

pub fn pluralize(noun: &str, count: i64, plural: Option<&str>) -> String {
    match count {
        1 => noun.to_string(),
        _ => match plural {
            Some(plural) => plural.to_string(),
            None => format!("{noun}s"),
        },
    }
}

#[cfg(test)]
mod tests {
    use super::{join_with_and, pluralize};

    #[test]
    fn test_join_with_and() {
        assert_eq!(join_with_and(vec![]), "");
        assert_eq!(join_with_and(vec!["lisa".to_owned()]), "lisa");
        assert_eq!(
            join_with_and(vec!["lisa".to_owned(), "bart".to_owned()]),
            "lisa and bart"
        );
        assert_eq!(
            join_with_and(vec![
                "lisa".to_owned(),
                "bart".to_owned(),
                "homer".to_owned()
            ]),
            "lisa, bart, and homer"
        );
        assert_eq!(
            join_with_and(vec![
                "lisa".to_owned(),
                "bart".to_owned(),
                "homer".to_owned(),
                "marge".to_owned()
            ]),
            "lisa, bart, homer, and marge"
        );
    }

    #[test]
    fn test_pluralize() {
        assert_eq!(pluralize("foo", 0, None), "foos");
        assert_eq!(pluralize("foo", 1, None), "foo");
        assert_eq!(pluralize("foo", 2, None), "foos");
        assert_eq!(pluralize("foo", 2, Some("bars")), "bars");
    }
}
