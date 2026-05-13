@serial @pagination
Feature: CLI Apps List Pagination
  As a developer using Tower CLI
  I want all of my apps to be returned from list commands
  So that I don't miss apps due to pagination limits

  Scenario: CLI apps list returns every app across multiple pages
    Given I have created 3 apps via CLI
    When I run "tower --page 1 --page-size 2 apps list" via CLI
    Then the output should contain all created app names

  Scenario: CLI apps list in JSON mode returns every app across multiple pages
    Given I have created 3 apps via CLI
    When I run "tower --page 1 --page-size 2 apps list --json" via CLI
    Then the output should be valid JSON
    And the JSON should contain all created app names
