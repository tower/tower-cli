# Tower CLI — Installation and Reference

Detailed installation options, optional features, and CLI reference for advanced setups.

For a quick start, see the main [README.md](README.md). For contributor development setup, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Installing the Tower CLI

### Recommended (most users)

The main way to install the CLI is using the `pip` package manager:

```bash
pip install -U tower
```

Verify installation:

```bash
tower version
```

You can also download the CLI from [releases](https://github.com/tower/tower-cli/releases/latest).

### Nix Flake

If you have Nix installed with flakes enabled, you can install the latest version of the Tower CLI as follows.

#### Profile

```bash
nix profile install github:tower/tower-cli
```

#### NixOS / nix-darwin

If you use [NixOS](https://nixos.org) or [nix-darwin](https://github.com/nix-darwin/nix-darwin) with flakes:

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

If you use [devenv](https://devenv.sh), add tower-cli to your project:

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

## Using the CLI

Both the Tower CLI and the cloud runtime live in this repository to ensure that Tower local and cloud execution environments behave identically.

### Command overview

```bash
tower
```

```
Tower is a compute platform for modern data projects

Usage: tower [OPTIONS] [COMMAND]

Commands:
  login         Create a session with Tower
  apps          Manage the apps in your current Tower account
  schedules     Manage schedules for your Tower apps
  secrets       Interact with the secrets in your Tower account
  environments  Manage the environments in your current Tower account
  deploy        Deploy your latest code to Tower
  run           Run your code in Tower or locally
  version       Print the current version of Tower
  teams         View information about team membership and switch between teams
  mcp-server    Runs an MCP server for LLM interaction
  help          Print this message or the help of the given subcommand(s)

Options:
  -j, --json  Output results in JSON format
  -h, --help  Print help
```

## Optional features

Tower supports optional installation extras. Install only what you need.

### AI/LLM support

```bash
pip install "tower[ai]"
```

- `tower.llms`: language model integration

### Apache Iceberg support

```bash
pip install "tower[iceberg]"
```

- `tower.create_table`: create Iceberg tables  
- `tower.load_table`: load data from Iceberg tables  

### dbt Core support

```bash
pip install "tower[dbt]"
```

Provides dbt Core integration for running dbt workflows:

```python
import tower

workflow = tower.dbt(
    project_path="path/to/dbt_project",
    profile_payload=tower.dbt.load_profile_from_env("DBT_PROFILE_YAML"),
    commands="deps,seed,build",
)

results = workflow.run()
```

Available helpers:
- `tower.dbt.load_profile_from_env()`: load dbt profile from environment variables
- `tower.dbt.parse_command_plan()`: parse comma-separated commands into a command plan
- `tower.dbt.DbtCommand`: represents a dbt CLI command invocation
- `tower.dbt.DbtRunnerConfig`: low-level configuration class
- `tower.dbt.run_dbt_workflow()`: low-level execution function

For a complete example, see the [dbt Core Ecommerce Analytics app](https://github.com/tower/tower-examples/tree/main/14-dbt-core-ecommerce-analytics).

### All optional features

```bash
pip install "tower[all]"
```

### Check available features

```python
import tower
import pprint

pprint.pprint(tower.get_available_features())
print(tower.is_feature_enabled("ai"))
```

## Packages API

The `tower.packages` namespace provides utilities for building Tower packages
programmatically.  These are **core** features included in every installation —
no extras are required.

### `tower.packages.build_package`

Build a Tower package from a directory containing a `Towerfile`.

```python
tower.packages.build_package(dir: str, output: str) -> None
```

Compiles the application defined by the `Towerfile` in `dir` into a compressed
`.tar.gz` archive and writes it to `output`.  The build pipeline runs natively
via the `tower_package` Rust crate, so it is fast and does not require
Python-side dependency resolution.

#### How it works

| Step | Description |
|------|-------------|
| **1. Towerfile Discovery** | Reads the `Towerfile` in `dir` to build a `PackageSpec` (app name, entry-point script, source globs, optional schedule, parameters, …). |
| **2. Native Resolution** | The `tower_package` Rust crate resolves source-file globs and assembles the `MANIFEST` JSON, including a content checksum. |
| **3. Tokio Runtime** | An embedded async Rust runtime handles concurrent file I/O and any network operations required during the build. |
| **4. Artifact Generation** | Source files are staged in a temporary build directory, compressed into a `.tar.gz` archive, and copied to `output`. |

#### Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `dir` | `str` | Path to the directory that contains your `Towerfile`. |
| `output` | `str` | Destination path for the built `.tar.gz` package (e.g. `"./dist/app_v1.tar.gz"`). |

#### Errors

Raises `RuntimeError` if:

- `dir` does not exist or does not contain a `Towerfile`
- The `Towerfile` is invalid TOML or is missing required fields (e.g. `app.name`)
- The native build pipeline fails for any other reason

#### Example

```python
import tower

try:
    tower.packages.build_package(
        dir="./projects/my-app",
        output="./dist/app_v1.tar.gz",
    )
    print("Build successful!")
except RuntimeError as e:
    print(f"Build failed: {e}")
```

The generated archive is a standard `.tar.gz` file containing:

- `Towerfile` — the original Towerfile
- `MANIFEST` — JSON metadata (app name, entry point, version, checksum, …)
- `app/<source files>` — all source files matched by the `source` glob(s) in
  the Towerfile, with `__pycache__` directories excluded automatically
