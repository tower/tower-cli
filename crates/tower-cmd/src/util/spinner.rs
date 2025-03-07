use crate::output;
use serde::de::DeserializeOwned;
use std::future::Future;

/// Helper function to handle operations with spinner
pub async fn with_spinner<T, F, V>(message: &str, operation: F, resource_name: Option<&str>) -> T
where
    F: Future<Output = Result<T, tower_api::apis::Error<V>>>,
    V: std::fmt::Debug + DeserializeOwned,
{
    let mut spinner = output::spinner(message);
    match operation.await {
        Ok(result) => {
            spinner.success();
            result
        }
        Err(err) => {
            spinner.failure();
            match err {
                tower_api::apis::Error::ResponseError(err) => {
                    // Check for 404 Not Found errors and provide a more user-friendly message
                    if err.status == 404 {
                        // Extract the resource type from the message
                        let resource_type = message
                            .trim_end_matches("...")
                            .trim_start_matches("Fetching ")
                            .trim_start_matches("Creating ")
                            .trim_start_matches("Updating ")
                            .trim_start_matches("Deleting ");

                        if let Some(name) = resource_name {
                            output::failure(&format!("{} '{}' not found", resource_type, name));
                        } else {
                            output::failure(&format!("The {} was not found", resource_type));
                        }
                    } else {
                        output::failure(&format!("{}: {}", err.status, err.content));
                    }
                    std::process::exit(1);
                }
                _ => {
                    output::tower_error(err);
                    std::process::exit(1);
                }
            }
        }
    }
}
