@serial
Feature: CLI Pagination
  As a developer using Tower CLI
  I want all items to be returned from list commands
  So that I don't miss apps or resources due to pagination limits

  Scenario: CLI apps list fetches all pages when results exceed page size
    Given the mock API has 105 seeded apps
    When I run "tower apps list" via CLI
    Then the output should contain all 105 seeded app names

  Scenario: CLI apps list in JSON mode returns all paginated results
    Given the mock API has 105 seeded apps
    When I run "tower apps list --json" via CLI
    Then the output should be valid JSON
    And the JSON should contain at least 105 apps
