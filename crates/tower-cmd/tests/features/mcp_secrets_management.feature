Feature: MCP Secrets Management
  As a developer using Tower MCP server
  I want to manage secrets securely through MCP commands
  So that I can configure my applications with sensitive data

  Background:
    Given I have a valid Tower configuration with authentication
    And I am using the Tower MCP server

  Scenario: Create a new secret
    Given I want to create a secret named "test-secret-123"
    And the secret value is "my-secret-value"
    When I create the secret via MCP tower_secrets_create
    Then the secret should be created successfully
    And it should be encrypted on the server

  Scenario: List existing secrets
    Given I have at least one secret in my Tower account
    When I list secrets via MCP tower_secrets_list
    Then I should receive a list of secrets with previews
    And the actual values should not be exposed

  Scenario: Create secret in specific environment
    Given I want to create a secret for the "staging" environment
    When I create a secret via MCP tower_secrets_create with environment "staging"
    Then the secret should be created in the staging environment
    And it should be isolated from other environments

  Scenario: Delete a secret
    Given I have a secret named "secret-to-delete"
    When I delete the secret via MCP tower_secrets_delete
    Then the secret should be removed successfully
    And it should no longer appear in the secrets list

  Scenario: Handle encryption key operations
    When I request the secrets encryption key via MCP
    Then I should receive a valid public key
    And it should be in the correct PEM format

  Scenario: Handle invalid secret operations gracefully
    Given I reference a non-existent secret "fake-secret-999"
    When I try to delete the secret via MCP tower_secrets_delete
    Then I should receive an appropriate error message
    And the MCP server should not crash