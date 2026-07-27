@catalogs
Feature: MCP catalog querying
  As a developer using the Tower MCP server with an agent
  I want to query Tower-managed storage catalogs safely
  So that an agent can explore data without write access or unbounded results

  # These scenarios exercise the real attach -> Iceberg -> query path, so they
  # are skipped unless a storage catalog is configured (see environment.py):
  #   TOWER_TEST_CATALOG      name of a tower-catalog storage catalog
  #   TOWER_URL               a real server (not the mock) with a valid session
  #   TOWER_TEST_CATALOG_ENV  environment the catalog lives in (default: default)
  #   TOWER_TEST_CATALOG_TABLE  optional "cat"."ns"."tbl" for the data query below

  Scenario: Show a storage catalog lists its tables
    When I show the test catalog via MCP
    Then I should receive a success response
    And the catalog response should list tables

  Scenario: Run a read-only query against the catalog
    When I query the test catalog with SQL "SELECT 1 AS one" via MCP
    Then I should receive query results
    And the query result columns should include "one"

  Scenario: Write statements are rejected
    When I query the test catalog with SQL "DROP TABLE does_not_exist" via MCP
    Then I should receive an error response about a read-only query

  Scenario: Multiple statements are rejected
    When I query the test catalog with SQL "SELECT 1; SELECT 2" via MCP
    Then I should receive an error response about a single statement

  @catalog-data
  Scenario: Query a configured table returns positional rows
    When I query the configured catalog table via MCP
    Then I should receive query results
