Feature: CLI JSON Output
  As a developer scripting against the Tower CLI
  I want --json output to be valid JSON on stdout
  So that I can pipe it into jq or parse it programmatically

  Scenario: Detached run with JSON mode emits parseable output with the run link
    Given I have a valid Towerfile in the current directory
    When I run "tower deploy --create" via CLI
    And I run "tower run --detached --json" via CLI
    Then the output should be valid JSON
    And the output should show "See more"

  Scenario: Run of an unknown app with JSON mode emits a parseable error
    Given I have a simple hello world application
    When I run "tower run --json" via CLI
    Then the output should be valid JSON
    And the output should show "tower deploy"

  Scenario: Empty schedules list with JSON mode emits an empty JSON array
    When I run "tower schedules list --json" via CLI
    Then the output should be valid JSON
    And the JSON should be an empty array

  Scenario: Teams list with JSON mode emits parseable output
    When I run "tower teams list --json" via CLI with a temporary session
    Then the output should be valid JSON

  Scenario: Version with JSON mode emits parseable output
    When I run "tower version --json" via CLI
    Then the output should be valid JSON
    And the output should show "version"
