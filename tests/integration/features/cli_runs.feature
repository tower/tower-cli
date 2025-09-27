Feature: CLI Run Commands
  As a developer using Tower CLI directly
  I want to run applications locally and remotely with proper feedback
  So that I can develop and deploy my applications effectively

  Scenario: CLI remote run should show red error message when API fails
    Given I have a simple hello world application
    When I run "tower run" via CLI
    Then the final crash status should show red "Error:"

  Scenario: CLI local run should have green timestamps and detect crashes
    Given I have a simple hello world application that exits with code 1
    When I run "tower run --local" via CLI
    Then timestamps should be green colored
    And each log line should be on a separate line
    And the final status should show "Your app crashed!" in red

  Scenario: CLI remote run should show detailed validation errors
    Given I have a pre-deployed test app
    When I run "tower run -p nonexistent_param=test" via CLI
    Then the output should show "API Error:"
    And the output should show "Validation error"
    And the output should show "Unknown parameter"
    And the output should not just show "422"

  Scenario: CLI run should show spinners during execution
    Given I have a pre-deployed test app
    When I run "tower run" via CLI
    Then the output should show "Scheduling run..." spinner
    And the output should show "Waiting for run to start..." spinner
    And both spinners should complete successfully