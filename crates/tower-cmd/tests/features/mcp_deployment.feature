Feature: MCP Deployment Operations
  As a developer using Tower MCP server
  I want to deploy applications through MCP commands
  So that I can automate my deployment workflow

  Background:
    Given I have a valid Tower configuration with authentication
    And I am using the Tower MCP server

  Scenario: Deploy application to Tower cloud
    Given I have a valid Towerfile in the current directory
    And the application is ready for deployment
    When I deploy the application via MCP tower_deploy
    Then the deployment should initiate successfully
    And I should receive confirmation of the deployment

  Scenario: Handle deployment with missing Towerfile
    Given I am in a directory without a Towerfile
    When I try to deploy via MCP tower_deploy
    Then the deployment should fail gracefully
    And I should receive an appropriate error message

  Scenario: Handle deployment timeout
    Given I have a complex application that takes time to deploy
    When I deploy the application via MCP tower_deploy
    Then the deployment should not hang indefinitely
    And I should receive feedback about the deployment status

  Scenario: Verify deployment doesn't interfere with local runs
    Given I have deployed an application to Tower cloud
    When I run the same application locally via MCP tower_run
    Then the local run should work independently
    And it should not conflict with the deployed version