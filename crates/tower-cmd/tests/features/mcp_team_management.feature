Feature: MCP Team Management
  As a developer using Tower MCP server
  I want to manage team contexts through MCP commands
  So that I can work with multiple teams and switch contexts

  Background:
    Given I have a valid Tower configuration with authentication
    And I am using the Tower MCP server

  Scenario: List available teams
    Given I belong to at least one team
    When I list teams via MCP tower_teams_list
    Then I should receive a list of teams I belong to
    And each team should show if it's the active team

  Scenario: Switch to a different team
    Given I belong to multiple teams
    And I am currently in team "team-a"
    When I switch to team "team-b" via MCP tower_teams_switch
    Then my active team should be changed to "team-b"
    And subsequent operations should use the new team context

  Scenario: Handle team switching for non-existent team
    Given I want to switch to a team I don't belong to
    When I try to switch to team "non-existent-team" via MCP tower_teams_switch
    Then I should receive an appropriate error message
    And my current team context should remain unchanged

  Scenario: Verify team context affects app operations
    Given I belong to multiple teams with different apps
    When I switch teams and list apps
    Then I should see different apps for each team
    And operations should be scoped to the active team