@serial
Feature: CLI Run Size
  As a developer who needs more compute for one run
  I want tower run --run-size to override the Towerfile's run_size
  So that I don't have to redeploy to change the size once

  Scenario: Run forwards an explicit run size to the server
    Given I have a valid Towerfile in the current directory
    And the run log is reset
    When I run "tower deploy --create" via CLI
    And I run "tower run --detached --run-size basic.large" via CLI
    Then the last run should have been sent with run size "basic.large"

  Scenario: Run without --run-size leaves the size to the server
    Given I have a valid Towerfile in the current directory
    And the run log is reset
    When I run "tower deploy --create" via CLI
    And I run "tower run --detached" via CLI
    Then the last run should have been sent without a run size

  Scenario: Run rejects a size that is not one of the known names
    Given I have a valid Towerfile in the current directory
    When I run "tower run --detached --run-size basic.enormous" via CLI
    Then the output should show "basic.xsmall"

  Scenario: Run size is meaningless for a local run
    Given I have a valid Towerfile in the current directory
    When I run "tower run --local --run-size basic.small" via CLI
    Then the output should show "cannot be used with"
