Feature: Tower Run Timeout Behavior
  As a developer using Tower MCP server
  I want tower_run commands to have proper timeout handling
  So that my development environment doesn't hang indefinitely

  Background:
    Given I have a valid Tower configuration
    And I am using the Tower MCP server

  Scenario: Quick applications complete without timeout
    Given I have a simple hello world application
    When I run the application via MCP tower_run
    Then the operation should complete within 30 seconds
    And the result should be successful

  Scenario: Long-running ETL applications timeout gracefully
    Given I have a long-running ETL application that takes 6 minutes
    When I run the application via MCP tower_run
    Then the operation should timeout after approximately 5 minutes
    And the MCP server should return a timeout message
    And the server should remain responsive

  Scenario: Infinite loop applications are terminated
    Given I have an application with an infinite loop
    When I run the application via MCP tower_run
    Then the operation should timeout after approximately 5 minutes
    And the MCP server should return a timeout message
    And no processes should be left hanging

  Scenario: Multiple concurrent runs don't interfere
    Given I have two different applications
    When I run both applications concurrently via MCP tower_run
    Then both operations should be handled independently
    And neither should hang indefinitely
    And both should respect the 5-minute timeout

  Scenario: Error conditions are handled quickly
    Given I am in a directory without a Towerfile
    When I try to run an application via MCP tower_run
    Then the operation should fail within 10 seconds
    And an appropriate error message should be returned