use crate::output;
use http::StatusCode;
use promptly::prompt_default;
use tower_api::apis::{
    configuration::Configuration,
    default_api::{self, CreateAppParams, DescribeAppParams},
};
use tower_api::models::CreateAppParams as CreateAppParamsModel;

pub async fn ensure_app_exists(
    api_config: &Configuration,
    app_name: &str,
    description: &str,
    create_app: bool,
) -> Result<(), tower_api::apis::Error<default_api::DescribeAppError>> {
    // Try to describe the app first
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

    // If the app exists, return Ok
    if describe_result.is_ok() {
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

    // If it's not a 404 error, return the original error
    if !is_not_found {
        return Err(err);
    }

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
        return Err(err);
    }

    // Try to create the app
    let create_result = default_api::create_app(
        api_config,
        CreateAppParams {
            create_app_params: CreateAppParamsModel {
                schema: None,
                name: app_name.to_string(),
                short_description: Some(description.to_string()),
                slug: None,
                is_externally_accessible: None, // Add the missing field
            },
        },
    )
    .await;

    match create_result {
        Ok(_) => {
            output::success(&format!("Created app '{}'", app_name));
            Ok(())
        }
        Err(create_err) => {
            // Convert any creation error to a response error
            Err(tower_api::apis::Error::ResponseError(
                tower_api::apis::ResponseContent {
                    tower_trace_id: "".to_string(),
                    status: match &create_err {
                        tower_api::apis::Error::ResponseError(resp) => resp.status,
                        _ => StatusCode::INTERNAL_SERVER_ERROR,
                    },
                    content: match &create_err {
                        tower_api::apis::Error::ResponseError(resp) => resp.content.clone(),
                        _ => create_err.to_string(),
                    },
                    entity: None,
                },
            ))
        }
    }
}
