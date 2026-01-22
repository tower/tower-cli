Feature: CLI App Management
  As a developer using Tower CLI directly
  I want to manage Tower applications through CLI commands
  So that I can create, list, and view my apps

  Scenario: CLI apps list shows app names with descriptions
    When I run "tower apps list" via CLI
    Then the output should contain app names in green bold text
    And the output should show descriptions or "No description" placeholder

  Scenario: CLI apps show displays app details with yellow table headers
    When I run "tower apps show predeployed-test-app" via CLI
    Then the output should show "Name:" label in green bold
    And the output should show "Description" header in green bold
    And the output should show "Recent runs" header in green bold
    And the table headers should be yellow colored
    And the table should show columns "#", "Status", "Start Time", "Elapsed Time"

  Scenario: CLI apps show with JSON mode returns structured data
    When I run "tower apps show --json predeployed-test-app" via CLI
    Then the output should be valid JSON
    And the JSON should contain app information
    And the JSON should contain runs array

  Scenario: CLI apps create with JSON mode returns app data
    When I run "tower apps create --json --name test-cli-app-123 --description 'Test app'" via CLI
    Then the output should be valid JSON
    And the JSON should contain the created app information
    And the app name should be "test-cli-app-123"
    And the app description should be "Test app"

  Scenario: CLI deploy updates app description from Towerfile
    Given I have a valid Towerfile in the current directory
    And I run "tower apps create --json --name {app_name}" via CLI using created app name
    When I run "tower deploy --create" via CLI
    And I run "tower apps show --json {app_name}" via CLI using created app name
    Then the app description should be "A test app"

  Scenario: CLI deploy --create creates app with description from Towerfile
    Given I have a valid Towerfile in the current directory
    When I run "tower deploy --create" via CLI
    And I run "tower apps show --json {app_name}" via CLI using created app name
    Then the app description should be "A test app"

  Scenario: CLI deploy with empty description does not update app
    Given I have a Towerfile with empty description in the current directory
    And I run "tower apps create --json --name {app_name} --description 'Original description'" via CLI using created app name
    When I run "tower deploy --create" via CLI
    And I run "tower apps show --json {app_name}" via CLI using created app name
    Then the app description should be "Original description"

  Scenario: CLI deploy with no description field does not update app
    Given I have a Towerfile with no description in the current directory
    And I run "tower apps create --json --name {app_name} --description 'Original description'" via CLI using created app name
    When I run "tower deploy --create" via CLI
    And I run "tower apps show --json {app_name}" via CLI using created app name
    Then the app description should be "Original description"
