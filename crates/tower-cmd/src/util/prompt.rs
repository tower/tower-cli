use inquire::{
    Confirm,
    InquireError::{OperationCanceled, OperationInterrupted},
};
use snafu::Snafu;

#[derive(Debug, Snafu)]
pub enum Error {
    #[snafu(display("Something went wrong while attempting to confirm"))]
    ConfirmationPromptError,

    ConfirmationPromptCancelled,
}

// Create a confirmation prompt with `message` and the default value `default`.
pub fn confirm(message: &str, default: bool) -> Result<bool, Error> {
    match Confirm::new(message).with_default(default).prompt() {
        Ok(response) => Ok(response),

        // Treat cancelled (esc) and interrupted (ctrl+c) the same in this context.
        Err(OperationCanceled | OperationInterrupted) => Err(Error::ConfirmationPromptCancelled),

        // Any other error just treat as a generic error.
        Err(_) => Err(Error::ConfirmationPromptError),
    }
}
