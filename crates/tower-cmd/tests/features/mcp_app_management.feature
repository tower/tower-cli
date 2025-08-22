Feature: MCP App Management
  As a developer using Tower MCP server
  I want to manage Tower applications through MCP commands
  So that I can create, deploy, and monitor my apps programmatically

  Background:
    Given I have a valid Tower configuration with authentication
    And I am using the Tower MCP server

  Scenario: Create a new Tower app
    Given I want to create an app named "test-app-123"
    When I create the app via MCP tower_apps_create
    Then the app should be created successfully
    And I should be able to see it in the app list

  Scenario: List existing Tower apps
    Given I have at least one app in my Tower account
    When I list apps via MCP tower_apps_list
    Then I should receive a list of apps
    And each app should have name, description, and status

  Scenario: Show app details and runs
    Given I have an app named "existing-app"
    When I show app details via MCP tower_apps_show
    Then I should receive detailed app information
    And I should see recent runs for the app

  Scenario: Delete a Tower app
    Given I have an app named "app-to-delete"
    When I delete the app via MCP tower_apps_delete
    Then the app should be removed successfully
    And it should no longer appear in the app list

  Scenario: Handle non-existent app gracefully
    Given I reference a non-existent app "fake-app-999"
    When I try to show app details via MCP tower_apps_show
    Then I should receive an appropriate error message
    And the MCP server should not crash