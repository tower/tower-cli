use chrono::{DateTime, Utc};

pub fn format_str(ts: &str) -> String {
    let dt: DateTime<Utc> = DateTime::parse_from_rfc3339(ts)
        .unwrap()
        .with_timezone(&Utc);

    format(dt)
}
pub fn format(dt: DateTime<Utc>) -> String {
    dt.format("%F %T").to_string()
}
