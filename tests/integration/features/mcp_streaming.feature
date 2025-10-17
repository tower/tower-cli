@streaming
Feature: MCP Streaming Transports
  As a developer using Tower MCP server with SSE/HTTP transports
  I want to test streaming functionality and different transport modes
  So that I can verify logging notifications and transport-specific features

  Background:
    Given I have a running Tower MCP server

  Scenario: Local run streams logging notifications via SSE
    Given I have a running Tower MCP server
    Given I have a simple hello world application
    When I call tower_run_local via SSE MCP for streaming
    Then I should receive logging notifications
    And the logs should contain process output
    And the logs should have tower-process logger

  Scenario: Local run streams logging notifications via HTTP
    Given I have a running Tower MCP server with transport "http"
    Given I have a simple hello world application
    When I call tower_run_local via SSE MCP for streaming
    Then I should receive logging notifications
    And the logs should contain process output
    And the logs should have tower-process logger

  Scenario: MCP server works with SSE transport
    Given I have a running Tower MCP server
    When I call tower_workflow_help via SSE MCP
    Then I should receive workflow help content via SSE

  Scenario: MCP server works with HTTP transport
    Given I have a running Tower MCP server with transport "http"
    When I call tower_workflow_help via HTTP MCP
    Then I should receive workflow help content via HTTP