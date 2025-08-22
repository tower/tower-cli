Feature: MCP Towerfile Management
  As a developer using Tower MCP server
  I want to manipulate Towerfile configurations through MCP commands
  So that I can programmatically manage my app configurations

  Background:
    Given I have a valid Tower configuration
    And I am using the Tower MCP server

  Scenario: Read existing Towerfile
    Given I have a valid Towerfile in the current directory
    When I read the Towerfile via MCP tower_file_read
    Then I should receive the parsed Towerfile configuration
    And it should contain app name, script, and build information

  Scenario: Update Towerfile app configuration
    Given I have a valid Towerfile in the current directory
    When I update the app name to "updated-app-name" via MCP tower_file_update
    Then the Towerfile should be modified successfully
    And the new app name should be persisted

  Scenario: Add parameter to Towerfile
    Given I have a valid Towerfile in the current directory
    When I add a parameter "batch_size" with default "1000" via MCP tower_file_add_parameter
    Then the parameter should be added to the Towerfile
    And it should be available for the application

  Scenario: Validate Towerfile configuration
    Given I have a valid Towerfile in the current directory
    When I validate the Towerfile via MCP tower_file_validate
    Then the validation should pass
    And I should receive a success response

  Scenario: Generate Towerfile from pyproject.toml
    Given I have a valid pyproject.toml file
    When I generate a Towerfile via MCP tower_file_generate
    Then a new Towerfile should be created
    And it should contain the correct Python configuration

  Scenario: Handle missing Towerfile gracefully
    Given I am in a directory without a Towerfile
    When I try to read the Towerfile via MCP tower_file_read
    Then I should receive an appropriate error message
    And the MCP server should not crash

  Scenario: Handle invalid Towerfile gracefully
    Given I have an invalid Towerfile in the current directory
    When I try to validate the Towerfile via MCP tower_file_validate
    Then the validation should fail
    And I should receive detailed error information