//! Static gates on untrusted SQL text, applied before a statement runs. They are
//! defence in depth on top of read-only credentials and the session hardening:
//! they reject write/DDL input and multi-statement input, and cap how many rows
//! an agent query may pull back.

/// Row cap for agent-issued queries. Rows past this are dropped and the result
/// is flagged truncated, so a model cannot pull an unbounded table into memory
/// or its context.
pub const AGENT_MAX_ROWS: usize = 1_000;

/// Leading keywords that write data or schema, or repoint the session. A query
/// starting with one of these is refused before it runs.
const WRITE_LEADING_KEYWORDS: &[&str] = &[
    "insert", "update", "delete", "merge", "create", "drop", "alter", "truncate", "replace",
    "copy", "attach", "detach",
];

/// The leading SQL keyword, lowercased, after skipping leading whitespace and
/// `--` / `/* */` comments.
pub fn first_keyword(sql: &str) -> String {
    let mut s = sql.trim_start();
    loop {
        if let Some(rest) = s.strip_prefix("--") {
            match rest.find('\n') {
                Some(nl) => s = rest[nl + 1..].trim_start(),
                None => return String::new(),
            }
        } else if let Some(rest) = s.strip_prefix("/*") {
            match rest.find("*/") {
                Some(end) => s = rest[end + 2..].trim_start(),
                None => return String::new(),
            }
        } else {
            break;
        }
    }
    s.chars()
        .take_while(|c| c.is_ascii_alphabetic())
        .collect::<String>()
        .to_lowercase()
}

/// True when `sql` starts with a write/DDL keyword.
pub fn is_write_statement(sql: &str) -> bool {
    WRITE_LEADING_KEYWORDS.contains(&first_keyword(sql).as_str())
}

/// True when `sql` holds more than one statement. A `;` inside a string literal
/// or comment is data, not a separator, so those spans are skipped. This gate
/// matters because duckdb-rs `prepare` runs every statement but the last as a
/// side effect, so unguarded multi-statement SQL would execute its leading
/// statements even though only the final one is returned.
pub fn is_multi_statement(sql: &str) -> bool {
    #[derive(PartialEq)]
    enum State {
        Normal,
        Single,
        Double,
        Line,
        Block,
    }

    let mut state = State::Normal;
    let mut statements = 0usize;
    let mut current_has_content = false;
    let mut chars = sql.chars().peekable();

    while let Some(c) = chars.next() {
        match state {
            State::Normal => match c {
                '\'' => {
                    state = State::Single;
                    current_has_content = true;
                }
                '"' => {
                    state = State::Double;
                    current_has_content = true;
                }
                '-' if chars.peek() == Some(&'-') => {
                    chars.next();
                    state = State::Line;
                }
                '/' if chars.peek() == Some(&'*') => {
                    chars.next();
                    state = State::Block;
                }
                ';' => {
                    if current_has_content {
                        statements += 1;
                        if statements > 1 {
                            return true;
                        }
                    }
                    current_has_content = false;
                }
                c if c.is_whitespace() => {}
                _ => current_has_content = true,
            },
            State::Single => {
                if c == '\'' {
                    if chars.peek() == Some(&'\'') {
                        chars.next();
                    } else {
                        state = State::Normal;
                    }
                }
            }
            State::Double => {
                if c == '"' {
                    if chars.peek() == Some(&'"') {
                        chars.next();
                    } else {
                        state = State::Normal;
                    }
                }
            }
            State::Line => {
                if c == '\n' {
                    state = State::Normal;
                }
            }
            State::Block => {
                if c == '*' && chars.peek() == Some(&'/') {
                    chars.next();
                    state = State::Normal;
                }
            }
        }
    }

    if current_has_content {
        statements += 1;
    }
    statements > 1
}
