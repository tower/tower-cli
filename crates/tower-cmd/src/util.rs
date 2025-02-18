use tower_api::apis::{
    configuration::Configuration,
    default_api::{self, DescribeAppParams, CreateAppsParams},
};
use http::StatusCode;
use tower_api::models::CreateAppParams;
use promptly::prompt_default;
use crate::output;

pub async fn ensure_app_exists(
    configuration: &Configuration,
    app_name: &str,
    description: &str,
    schedule: &str
) -> Result<(), tower_api::apis::Error<default_api::DescribeAppError>> {
    match default_api::describe_app(configuration, DescribeAppParams {
        name: app_name.to_string(),
        runs: None,
    }).await {
        Ok(_) => Ok(()),
        Err(err) => {
            // Check if it's a response error and try to parse as ErrorModel
            if let tower_api::apis::Error::ResponseError(response) = &err {
                if let Ok(error_model) = serde_json::from_str::<tower_api::models::ErrorModel>(&response.content) {
                    if error_model.status == Some(404) {
                        if prompt_default(
                            format!("App '{}' does not exist. Would you like to create it?", app_name),
                            false
                        ).unwrap_or(false) {
                            match default_api::create_apps(configuration, CreateAppsParams {
                                create_app_params: CreateAppParams {
                                    schema: None,
                                    name: app_name.to_string(),
                                    short_description: Some(description.to_string()),
                                    schedule: Some(schedule.to_string()),
                                }
                            }).await {
                                Ok(_) => {
                                    output::success(&format!("Created app '{}'", app_name));
                                    Ok(())
                                },
                                Err(create_err) => Err(tower_api::apis::Error::ResponseError(
                                    tower_api::apis::ResponseContent {
                                        status: match &create_err {
                                            tower_api::apis::Error::ResponseError(resp) => resp.status,
                                            _ => StatusCode::INTERNAL_SERVER_ERROR
                                        },
                                        content: create_err.to_string(),
                                        entity: None
                                    }
                                ))
                            }
                        } else {
                            Err(err)
                        }
                    } else {
                        Err(err)
                    }
                } else {
                    Err(err)
                }
            } else {
                Err(err)
            }
        }
    }
}
