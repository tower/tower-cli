Feature: MCP App Management
  As a developer using Tower MCP server
  I want to manage Tower applications through MCP tool commands
  So that I can create, deploy, and monitor my apps with an LLM

  Background:
    Given I have a running Tower MCP server

  Scenario: List existing Tower apps
    When I call tower_apps_list via MCP
    Then I should receive a response with apps data

  Scenario: Show app details for non-existent app
    When I call tower_apps_show with new app name "fake-app-999"
    Then I should receive an error response
    And the MCP server should remain responsive

  # if not using mock, make sure you've logged in and have a valid session
  Scenario: Create a new Tower app
    When I call tower_apps_create with new app name "test-app-123"
    Then I should receive a success response

  Scenario: Validate Towerfile without file
    When I call tower_file_validate via MCP
    Then I should receive an error response about missing Towerfile

  Scenario: Validate valid Towerfile
    Given I have a valid Towerfile in the current directory
    When I call tower_file_validate via MCP
    Then I should receive a success response

  Scenario: Read valid Towerfile
    Given I have a valid Towerfile in the current directory
    When I call tower_file_read via MCP
    Then I should receive the parsed Towerfile configuration

  Scenario: Run simple application successfully locally
    Given I have a simple hello world application
    When I call tower_run_local via MCP
    Then I should receive a response about the run

  Scenario: Attempt remote run without deployed app
    Given I have a simple hello world application
    When I call tower_run_remote via MCP
    Then I should receive an error response about app not deployed
    And the MCP server should remain responsive

  Scenario: Remote run succeeds after proper deployment
    Given I have a simple hello world application
    When I call tower_deploy via MCP
    Then I should receive a success response about deployment
    When I call tower_run_remote via MCP
    Then I should receive a response about the run

  Scenario: Generate Towerfile from pyproject.toml
    Given I have a pyproject.toml file with project metadata
    When I call tower_file_generate via MCP
    Then I should receive a valid TOML Towerfile
    And the Towerfile should contain the project name and description

  Scenario: List schedules when none exist
    When I call tower_schedules_list via MCP
    Then I should receive a response with empty schedules data

  Scenario: Create a new schedule for an app
    When I call tower_schedules_create with app "predeployed-test-app", cron "0 9 * * *", and environment "default"
    Then I should receive a success response about schedule creation

  Scenario: List schedules after creating one
    Given I have created a schedule for "predeployed-test-app"
    When I call tower_schedules_list via MCP
    Then I should receive a response with schedule data for "predeployed-test-app"

  Scenario: Update an existing schedule
    Given I have created a schedule for "predeployed-test-app"
    When I call tower_schedules_update with new cron "0 10 * * *"
    Then I should receive a success response about schedule update

  Scenario: Delete an existing schedule
    Given I have created a schedule for "predeployed-test-app"
    When I call tower_schedules_delete with the schedule ID
    Then I should receive a success response about schedule deletion

  Scenario: Remote run succeeds after proper deployment
    Given I have a simple hello world application
    When I call tower_deploy via MCP
    Then I should receive a success response about deployment
    When I call tower_run_remote via MCP
    Then I should receive a response about the run

  Scenario: MCP local run output should be plain text without color codes
    Given I have a simple hello world application
    When I call tower_run_local via MCP
    Then the response should contain plain text log lines
    And the response should not contain ANSI color codes
    And each log line should be properly formatted with timestamp

  Scenario: MCP remote run should show detailed validation errors
    Given I have a simple hello world application
    When I call tower_deploy via MCP
    Then I call tower_run_remote with invalid parameter "nonexistent_param=test"
    Then I should receive a detailed validation error
    And the error should mention "Unknown parameter"
    And the error should not just be a status code

  Scenario: Local run should detect exit code failures
    Given I have a simple hello world application that exits with code 1
    When I call tower_run_local via MCP
    Then the response should indicate the app crashed
    And the response should contain "failed" message

  Scenario: Deploy auto-creates app when it doesn't exist
    Given I have a simple hello world application
    When I call tower_deploy via MCP
    Then I should receive a success response about deployment
    And the app "hello-world" should be visible in Tower

  Scenario: MCP workflow help via stdio transport
    When I call tower_workflow_help via stdio MCP
    Then I should receive workflow help content via stdio
