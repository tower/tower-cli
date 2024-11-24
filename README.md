# Tower CLI

The Tower CLI is one of the main ways to interact with the Tower environment.
You can do basically everything you need inside the Tower CLI, including run
your code locally or remotely in the Tower cloud. 

## Installing the Tower CLI

The main way to install the CLI is using the `pip` package manager.

```bash
$ pip install -U tower-cli
```

You can also download the CLI directly from one of our [releases](https://github.com/tower/tower-cli/releases/latest).

## Using the Tower CLI

There are two big components in the Tower CLI reposiory: The CLI itself and the
runtime environment for the Tower cloud. We host the runtime in this repository
and pull it in to our internal code because we want to ensure that the
environments behave *exactly the same* locally and in our cloud!

### Using the CLi

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
