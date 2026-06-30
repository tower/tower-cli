@serial @deploy
Feature: CLI Deploy Idempotency Key
  As a developer promoting unchanged source across environments
  I want tower deploy to send an X-Tower-Idempotency-Key
  So that consecutive deploys of identical source reuse a single version

  Scenario: Deploy forwards an explicit idempotency key to the server
    Given I have a valid Towerfile in the current directory
    And the deploy log is reset
    When I run "tower deploy --create --idempotency-key explicit-key-123" via CLI
    Then the last deploy should have been sent with idempotency key "explicit-key-123"

  Scenario: Deploy with --no-idempotency-key suppresses the header
    Given I have a valid Towerfile in the current directory
    And the current directory is a clean git repository
    And the deploy log is reset
    When I run "tower deploy --create --no-idempotency-key" via CLI
    Then the last deploy should have been sent without an idempotency key

  Scenario: Deploy auto-detects the git commit SHA on a clean tree
    Given I have a valid Towerfile in the current directory
    And the current directory is a clean git repository
    And the deploy log is reset
    When I run "tower deploy --create" via CLI
    Then the last deploy should have been sent with the current git commit SHA

  Scenario: Deploy omits the key on a dirty git tree
    Given I have a valid Towerfile in the current directory
    And the current directory is a clean git repository
    And the working tree has uncommitted changes
    And the deploy log is reset
    When I run "tower deploy --create" via CLI
    Then the last deploy should have been sent without an idempotency key

  Scenario: Re-deploying with the same key reuses the existing version
    Given I have a valid Towerfile in the current directory
    And the deploy log is reset
    When I run "tower deploy --create --idempotency-key reuse-key" via CLI
    And I run "tower deploy --idempotency-key reuse-key" via CLI
    Then the CLI output should indicate the version was reused
