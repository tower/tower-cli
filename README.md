# Tower CLI

The Tower CLI is one of the main ways to interact with the Tower environment.
You can do basically everything you need inside the Tower CLI, including run
your code locally or remotely in the Tower cloud.

## Installing the Tower CLI

The main way to install the CLI is using the `pip` package manager.

```bash
$ pip install -U tower
```

You can also download the CLI directly from one of our [releases](https://github.com/tower/tower-cli/releases/latest).

### Nix Flake

If you have Nix installed with flakes enabled, you can install the latest version
of tower CLI with the following:

#### Profile

```bash
$ nix profile install github:tower/tower-cli#tower
```

#### NixOS/nix-darwin

If you are using [NixOS]()/[nix-darwin](https://github.com/nix-darwin/nix-darwin)
with flakes then you can add the following:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    tower-cli.url = "github:tower/tower-cli";
  };

  outputs = { self, nixpkgs, tower-cli, ... }@inputs: {
    # with nix-darwin:
    # darwinConfigurations.your-hostname = darwin.lib.darwinSystem {
    nixosConfigurations.nixos = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [{
        environment.systemPackages = [ tower-cli.packages.${system}.tower ];
      }];
    };
  };
}
```

#### Devenv

If you're using [devenv](https://devenv.sh), you can add tower-cli to your project:

```yaml
# devenv.yaml
inputs:
  tower-cli:
    url: github:tower/tower-cli
```

```nix
# devenv.nix
{ inputs, pkgs, ... }:
{
  packages = [
    inputs.tower-cli.packages.${pkgs.stdenv.system}.tower
  ];
}
```

## Using the Tower CLI

There are two big components in the Tower CLI reposiory: The CLI itself and the
runtime environment for the Tower cloud. We host the runtime in this repository
and pull it in to our internal code because we want to ensure that the
environments behave _exactly the same_ locally and in our cloud!

### Using the CLI

It's pretty straight forward! But here's what it looks like right now.

```bash
$ tower
Tower is a compute platform for modern data projects

Usage: tower [OPTIONS] <COMMAND>

Commands:
  login    Create a session with Tower
  apps     Interact with the apps that you own
  secrets  Interact with the secrets in your Tower account
  deploy   Deploy your latest code to Tower
  run      Run your code in Tower or locally
  version  Print the current version of Tower
  help     Print this message or the help of the given subcommand(s)

Options:
  -h, --help                   Print help
```

### Optional Features

Tower supports several optional features that can be installed as needed:

#### AI/LLM Support

```bash
pip install "tower[ai]"
```

Provides integration with language models through:

- `tower.llms`: Access to language model functionality

#### Apache Iceberg Support

```bash
pip install "tower[iceberg]"
```

Provides Apache Iceberg table support:
- `tower.create_table`: Create Iceberg tables
- `tower.load_table`: Load data from Iceberg tables
- `tower.tables`: Access Iceberg table functionality

#### dbt Core Support

```bash
pip install "tower[dbt]"
```

Provides dbt Core integration for running dbt workflows:

```python
import tower

# Configure and run a dbt workflow
workflow = tower.dbt(
    project_path="path/to/dbt_project",
    profile_payload=tower.dbt.load_profile_from_env("DBT_PROFILE_YAML"),
    commands="deps,seed,build",
)

results = workflow.run()
```

Available helper functions and classes:
- `tower.dbt.load_profile_from_env()`: Load dbt profile from environment variables
- `tower.dbt.parse_command_plan()`: Parse comma-separated commands into a command plan
- `tower.dbt.DbtCommand`: Represents a dbt CLI command invocation
- `tower.dbt.DbtRunnerConfig`: Low-level configuration class
- `tower.dbt.run_dbt_workflow()`: Low-level execution function

For a complete example, see the [dbt Core Ecommerce Analytics app](https://github.com/tower/tower-examples/tree/main/14-dbt-core-ecommerce-analytics).

#### Install All Optional Features

```bash
pip install "tower[all]"
```

#### Check Available Features

You can check which features are available in your installation:

```python
import tower
import pprint

# Print information about all features
pprint.pprint(tower.get_available_features())

# Check if a specific feature is enabled
print(tower.is_feature_enabled("ai"))
```

### MCP Server Integration

Tower CLI includes an MCP (Model Context Protocol) server that allows AI assistants and editors to interact with your Tower account directly. The MCP server provides tools for managing apps, secrets, teams, and deployments.

#### Prerequisites

Before using the MCP server, ensure you're logged into Tower:

```bash
tower login
```

The MCP server will use your existing Tower CLI authentication and configuration.


#### Available Tools

The MCP server exposes the following tools:
- `tower_apps_list` - List all Tower apps in your account
- `tower_apps_create` - Create a new Tower app
- `tower_apps_show` - Show details for a Tower app and its recent runs
- `tower_apps_logs` - Get logs for a specific Tower app run
- `tower_apps_delete` - Delete a Tower app
- `tower_secrets_list` - List secrets in your Tower account
- `tower_secrets_create` - Create a new secret in Tower
- `tower_secrets_delete` - Delete a secret from Tower
- `tower_teams_list` - List teams you belong to
- `tower_teams_switch` - Switch context to a different team
- `tower_deploy` - Deploy your app to Tower cloud
- `tower_run` - Run your app locally

#### Starting the MCP Server

The Tower MCP server uses Server-Sent Events (SSE) for communication and runs on port 34567 by default. Start the server:

```bash
tower mcp-server
```

Or specify a custom port:

```bash
tower mcp-server --port 8080
```

The server will display a message showing the URL it's running on:
```
SSE server running on http://127.0.0.1:34567
```

It's important to keep the terminal with the MCP server open until you're finished. Alternatively, you can launch it in the background with:

``` bash
tower mcp-server &
```

It's also important to be logged in. If you haven't already, you can open another terminal window and type `tower login` in order to open the login in a browser window.

#### Client Configuration

##### Claude Code

Add the Tower MCP server to Claude Code using SSE transport:

```bash
claude mcp add tower http://127.0.0.1:34567/sse --transport sse
```

Or with the JSON configuration directly:

```json
{
  "mcpServers": {
    "tower": {
      "url": "http://127.0.0.1:34567/sse",
      "transport": "sse"
    }
  }
}
```

For custom ports, adjust the URL accordingly (e.g., `http://127.0.0.1:8080/sse`).

##### Cursor

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=tower&config=eyJ1cmwiOiJodHRwOi8vMTI3LjAuMC4xOjM0NTY3L3NzZSJ9)

If that doesn't work, try opening the following link in your browser or in your terminal with `open` on macOS, or `xdg-open` on Linux: 
```
cursor://anysphere.cursor-deeplink/mcp/install?name=tower&config=eyJ1cmwiOiJodHRwOi8vMTI3LjAuMC4xOjM0NTY3L3NzZSJ9
```

Or manually, add this to your Cursor MCP settings (`mcp.json`):

```json
{
  "mcpServers": {
    "tower": {
      "url": "http://127.0.0.1:34567/sse"
    }
  }
}
```

##### VS Code

In VS Code, first you should enable MCP integrations by setting `Chat>MCP:Enabled` to true in your settings.

For adding the server, you can try copying and pasting the following link into your URL bar:
```
vscode:mcp/install?%7B%22name%22%3A%22tower%22%2C%22type%22%3A%22sse%22%2C%22url%22%3A%22http%3A%2F%2F127.0.0.1%3A34567%2Fsse%22%7D
```

Alternatively, you can add the following to your `mcp.json`:

```json
{
  "servers": {
    "tower": {
      "type": "sse",
      "url": "http://127.0.0.1:34567/sse"
    }
  }
}
```

##### Gemini CLI

In your `settings.json`, add the following:

``` json
{
  "mcpServers": {
    "tower": {
        "url": "http://127.0.0.1:34567/sse"
    }
  }
}
```

### About the runtime environment

The [tower-runtime](crates/tower-runtime) crate has the Rust library that makes
up the runtime environment itself. All the interfaces are defined in the main
crate, and the `local` package contains the invokation logic for invoking tower
packages locally.

To learn more about tower packages, see the
[tower-package](crates/tower-package) crate.

## Contributing

We welcome contributions to the Tower CLI and runtime environment! Please see
the [CONTRIBUTING.md](CONTRIBUTING.md) file for more information.

### Code of Conduct

All contributions must abide by our code of conduct. Please see
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for more information.

## Development

Here are a few handy tips and common workflows when developing the Tower CLI.

### Getting Started

1. Install development dependencies:
   ```bash
   uv sync --group dev
   ```

2. Set up pre-commit hooks for code formatting:
   ```bash
   uv run --group dev pre-commit install
   ```

This will automatically run Black formatter on Python files before each commit.

### Python SDK development

We use `uv` for all development. You can spawn a REPL in context using `uv` very
easily. Then you can `import tower` and you're off to the races!

```bash
uv run python
```

To run tests:

```bash
uv sync --locked --all-extras --dev
uv run pytest tests
```

### Code Formatting

We use Black for Python code formatting. The pre-commit hooks will automatically format your code, but you can also run it manually:

```bash
# Format all Python files in the project
uv run --group dev black .

# Check formatting without making changes
uv run --group dev black --check .
```

If you need to get the latest OpenAPI SDK, you can run
`./scripts/generate-python-api-client.sh`.

## Testing
We use pytest to run tests. Copy `pytest.ini.template` to `pytest.ini` and 
replace the values of environment variables 
