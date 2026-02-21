# Tower CLI — Development Guide

Development setup and tooling for contributors.

For contribution guidelines (reporting bugs, suggesting features, code of conduct), see [CONTRIBUTING.md](CONTRIBUTING.md).

## Runtime architecture (Rust + Python)

The [tower-runtime](crates/tower-runtime) crate is the Rust runtime used to execute Tower apps. The main crate defines the interfaces; the `local` package implements running Tower packages locally.

See the [tower-package](crates/tower-package) crate for how Tower packages are built and run.

## Development setup

Make sure you have [`uv`](https://github.com/astral-sh/uv) installed.

To interactively test your changes, start a REPL with the project installed in development mode:

```bash
uv run python
```

```python
>>> import tower
>>> tower.some_function()
```

## Running the CLI locally

```bash
uv run tower --help
```

## Running tests

Copy `pytest.ini.template` to `pytest.ini`:

```bash
cp pytest.ini.template pytest.ini
```

Set the required environment variables (e.g. `TOWER_INFERENCE_ROUTER_API_KEY`) to your own or test values.

Then install dependencies and run the tests:

```bash
uv sync --locked --all-extras --dev
uv run pytest tests
```

## Development flow

Typical development loop:

1. Make changes
2. Run `uv run pytest tests`
3. Run `uv run tower --help` or other CLI commands to verify behavior

## OpenAPI SDK

When the OpenAPI spec changes, regenerate the Python API client:

```bash
./scripts/generate-python-api-client.sh
```

## Code of conduct

Contributions must follow our [Code of Conduct](CODE_OF_CONDUCT.md).
