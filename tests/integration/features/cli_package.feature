Feature: CLI Package
  As a developer scripting against the Tower CLI
  I want `tower package` to exit non-zero when it cannot build a package
  So that a broken Towerfile fails my pipeline instead of passing silently

  Scenario: Packaging a Towerfile with no script fails loudly
    Given I have a Towerfile that is missing its script
    When I run "tower package -d . -o pkg.tar.gz" via CLI
    Then the command should exit with a non-zero status
    And the output should show "script"

  Scenario: Packaging without any Towerfile fails loudly
    When I run "tower package -d . -o pkg.tar.gz" via CLI
    Then the command should exit with a non-zero status
    And the output should show "Towerfile"

  Scenario: Packaging a valid app succeeds
    Given I have a valid Towerfile in the current directory
    When I run "tower package -d . -o pkg.tar.gz" via CLI
    Then the command should exit with status 0
    And the output should show "Package created successfully"
