use crate::output;
use promptly::prompt_default;
use tower_api::apis::{
    configuration::Configuration,
    default_api::{self, CreateAppParams, DescribeAppParams},
};
use tower_api::models::CreateAppParams as CreateAppParamsModel;

pub async fn ensure_app_exists(
    api_config: &Configuration,
    app_name: &str,
    description: Option<&str>,
    create_app: bool,
) -> Result<(), crate::Error> {
    // Try to describe the app first (with spinner)
    let mut spinner = output::spinner("Checking app...");
    let describe_result = default_api::describe_app(
        api_config,
        DescribeAppParams {
            name: app_name.to_string(),
            runs: None,
            start_at: None,
            end_at: None,
            timezone: None,
        },
    )
    .await;

    // If the app exists, return Ok (description is create-only).
    if describe_result.is_ok() {
        spinner.success();
        return Ok(());
    }

    // Extract the error
    let err = describe_result.unwrap_err();

    // Check if it's a 404 Not Found error
    let is_not_found = match &err {
        tower_api::apis::Error::ResponseError(response) => {
            serde_json::from_str::<tower_api::models::ErrorModel>(&response.content)
                .map(|model| model.status == Some(404))
                .unwrap_or(false)
        }
        _ => false,
    };

    // If it's not a 404 error, fail the spinner and return the error
    if !is_not_found {
        spinner.failure();
        return Err(crate::Error::ApiDescribeAppError { source: err });
    }

    // App not found - stop spinner before prompting user
    drop(spinner);

    // Decide whether to create the app
    let create_app = create_app
        || prompt_default(
            format!(
                "App '{}' does not exist. Would you like to create it?",
                app_name
            ),
            false,
        )
        .unwrap_or(false);

    // If the user doesn't want to create the app, return the original error
    if !create_app {
        return Err(crate::Error::ApiDescribeAppError { source: err });
    }

    // Try to create the app (with a new spinner)
    let mut spinner = output::spinner("Creating app...");
    let create_result = default_api::create_app(
        api_config,
        CreateAppParams {
            create_app_params: CreateAppParamsModel {
                schema: None,
                name: app_name.to_string(),
                // API create expects short_description; CLI/Towerfile expose "description".
                short_description: description.map(|desc| desc.to_string()),
                slug: None,
                is_externally_accessible: None,
                subdomain: None,
            },
        },
    )
    .await;

    match create_result {
        Ok(_) => {
            spinner.success();
            output::success(&format!("Created app '{}'", app_name));
            Ok(())
        }
        Err(create_err) => {
            spinner.failure();
            Err(crate::Error::ApiCreateAppError {
                source: create_err,
            })
        }
    }
}
