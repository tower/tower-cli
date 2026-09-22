@serial
Feature: MCP Run Size
  As an agent launching a run through the Tower MCP server
  I want tower_run_remote to accept a run_size
  So that I can give one run more compute without editing the Towerfile

  Background:
    Given I have a running Tower MCP server

  Scenario: Remote run forwards run_size to the server
    Given I have a simple hello world application
    And the run log is reset
    When I call tower_deploy via MCP
    Then I should receive a success response about deployment
    When I call tower_run_remote with run_size "basic.small"
    Then I should receive a response about the run
    And the last run should have been sent with run size "basic.small"

  Scenario: Remote run rejects an unknown run_size
    Given I have a simple hello world application
    When I call tower_run_remote with run_size "basic.enormous"
    Then I should receive an error response
    And the MCP server should remain responsive
