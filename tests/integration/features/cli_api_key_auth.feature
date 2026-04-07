Feature: API Key Authentication
  As a user authenticating with an API key
  I want the CLI to use the X-API-Key header
  So that I can interact with Tower without a session

  Scenario: List apps using API key auth
    When I run "tower --json apps list" via CLI with API key
    Then the output should be valid JSON
    And no session.json should exist in the temp home

  Scenario: List teams using API key auth
    When I run "tower teams list" via CLI with API key
    Then no session.json should exist in the temp home

  Scenario: Login warns when API key is set
    When I run "tower login --no-browser" via CLI with API key and input "y\n"
    Then the output should show "TOWER_API_KEY is set"
    And the output should show "ignore the session"
