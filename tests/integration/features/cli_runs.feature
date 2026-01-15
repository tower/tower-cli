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
    And the final status should show "Your local run crashed!" in red

  Scenario: CLI remote run should show detailed validation errors
    Given I have a valid Towerfile in the current directory
    When I run "tower deploy --create" via CLI
    Then I run "tower run -p nonexistent_param=test" via CLI
    Then the output should show "API Error:"
    And the output should show "Validation error"
    And the output should show "Unknown parameter"
    And the output should not just show "422"

  Scenario: CLI run should show spinners during execution
    Given I have a valid Towerfile in the current directory
    When I run "tower deploy --create" via CLI
    And I run "tower run" via CLI
    Then the output should show "Scheduling run..." spinner
    And the output should show "Waiting for run to start..." spinner
    And both spinners should complete successfully

  Scenario: CLI run should show logs that arrive after run completes
    Given I have a simple hello world application named "app-logs-after-completion"
    When I run "tower deploy --create" via CLI
    And I run "tower run" via CLI
    Then the output should show "First log before run completes"
    And the output should show "Second log after run completes"

  Scenario: CLI apps logs follow should stream logs and drain after completion
    Given I have a simple hello world application named "app-logs-after-completion"
    When I run "tower deploy --create" via CLI
    And I run "tower run --detached" via CLI and capture run number
    And I run "tower apps logs --follow {app_name}#{run_number}" via CLI using created app name and run number
    Then the output should show "First log before run completes"
    And the output should show "Second log after run completes"
