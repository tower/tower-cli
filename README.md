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

If you need to get the latest OpenAPI SDK, you can run
`./scripts/generate-python-api-client.sh`.
