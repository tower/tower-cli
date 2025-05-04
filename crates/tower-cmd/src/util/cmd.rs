use crate::output;
use clap::ArgMatches;

pub fn get_string_flag(args: &ArgMatches, name: &str) -> String {
    args.get_one::<String>(name)
        .unwrap_or_else(|| {
            output::die(&format!("{} is required", name));
        })
        .to_string()
}

pub fn get_bool_flag(args: &ArgMatches, name: &str) -> bool {
    args.get_one::<bool>(name)
        .unwrap_or_else(|| {
            output::die(&format!("{} is required", name));
        })
        .to_owned()
}
