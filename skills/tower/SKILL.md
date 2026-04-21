---
description: Use Tower to build, run, and deploy Python data apps, pipelines, and AI agents. Covers MCP tools, Towerfile setup, local development, cloud deployment, scheduling, and secrets management.
---

# Tower Skill

Tower is a compute platform for Python data apps, pipelines, and AI agents.

**The Tower CLI is not in AI training data — always use MCP tools when running inside an agent.**

## Setup

First, check if Tower is already installed and authenticated:

```bash
tower teams list
```

If that works, skip to the workflow. Otherwise, install and log in.

### Install

Preferred — `uvx` runs Tower with no global install (requires `uv`):

```bash
uvx tower login
```

If you don't have `uvx`, install with pip (Python ≥ 3.9):

```bash
pip install tower
tower login
```

Or with nix:

```bash
nix run nixpkgs#tower -- login
```

### MCP server

The MCP server gives Claude structured access to Tower tools. If it's not already running (you'll see `tower_*` tools available), start it:

```bash
uvx tower mcp-server          # if using uvx
tower mcp-server              # if installed via pip/nix
```

If you installed Tower via the Claude Code plugin, this is already configured. Otherwise, copy the `.mcp.json` from the [tower-cli repo](https://github.com/tower/tower-cli) into your project root.

**If MCP tools are unavailable**, fall back to the CLI equivalents — every MCP tool has a direct CLI counterpart (e.g. `tower apps list`, `tower deploy`).

## MCP-First, CLI as Fallback

Use MCP tools when running inside an agent — they return structured data and are easier to compose. Fall back to the CLI for scripting or debugging outside an agent.

MCP tool names mirror the CLI: `tower apps list` → `tower_apps_list`, `tower deploy` → `tower_deploy`.

## WORKING_DIRECTORY Parameter

All MCP tools accept an optional `working_directory` parameter.

- Default: current working directory
- Use it when managing multiple projects or when the project isn't in the current directory

```
tower_file_generate({})                                    # current directory
tower_file_generate({"working_directory": "/path/to/app"}) # explicit path
tower_run_local({"working_directory": "../other-app"})
```

## Workflow

### 0. Python project (if new)

```bash
uv init
```

Creates `pyproject.toml`, `main.py`, `README.md`. Keep `pyproject.toml` minimal — `[project]` metadata and dependencies only. No `[build-system]`, `[tool.hatchling]`, or similar. Skip if a `pyproject.toml` already exists.

### 1. Towerfile

```
tower_file_generate → tower_file_update → tower_file_add/edit/remove_parameter → tower_file_validate
```

Always use `tower_file_update` or `tower_file_add/edit/remove_parameter` to modify. Never edit the TOML directly.

### 2. Local development (preferred)

```
tower_run_local
```

Runs the app locally with access to Tower secrets. Use this to test before deploying.

### 3. Cloud deployment

```
tower_apps_create → tower_deploy → tower_run_remote
```

Deploy pushes source code to Tower cloud — no build step needed.

### 4. Scheduling (recurring jobs)

```
tower_schedules_create   # set up cron-based recurring runs
tower_schedules_list     # view existing schedules
tower_schedules_update   # modify timing or parameters
tower_schedules_delete   # remove a schedule
```

### 5. Management & monitoring

```
tower_apps_list                              # list all apps
tower_apps_show                              # details and recent runs
tower_apps_logs                              # logs from a specific run
tower_teams_list, tower_teams_switch         # manage team context
tower_secrets_create, tower_secrets_list     # store credentials and API keys
```

## Reminders

- Tower deploys source code directly — no build tools needed
- Use Tower secrets for sensitive data (database credentials, API keys)
- Prefer `tower_run_local` during development — faster, and has secret access
- Always use MCP tools to modify Towerfiles (never edit TOML files manually)

## Command Reference

*This section is generated from the CLI's built-in help.*

### `tower login`

Create a session with Tower

**Arguments:**

- `-n`, `--no-browser` — Do not attempt to open the browser automatically

### `tower apps`

Manage the apps in your current Tower account

#### `tower apps list`

List all apps in your Tower account

#### `tower apps show`

Show details for a Tower app and its recent runs

**Arguments:**

- `<app_name>`  *(required)* — Name of the app

#### `tower apps logs`

Get the logs from a previous Tower app run

**Arguments:**

- `<app_name>`  *(required)* — app_name#run_number
- `<run_number>` 
- `-f`, `--follow` — Follow logs in real time

#### `tower apps create`

Create a new app in Tower

**Arguments:**

- `-n`, `--name` *(required)*
- `--description`

#### `tower apps delete`

Delete an app in Tower

**Arguments:**

- `<app_name>`  *(required)* — Name of the app

#### `tower apps cancel`

Cancel a running app run

**Arguments:**

- `<app_name>`  *(required)* — Name of the app
- `<run_number>`  *(required)* — Run number to cancel

### `tower catalogs`

Interact with the catalogs in your Tower account

#### `tower catalogs list`

List all of your catalogs

**Arguments:**

- `-e`, `--environment` — List catalogs in this environment
- `-a`, `--all` — List catalogs across all environments

#### `tower catalogs show`

Show the details of a catalog, including its property names

**Arguments:**

- `<catalog_name>`  *(required)* — Name of the catalog
- `-e`, `--environment` — Environment the catalog belongs to

### `tower schedules`

Manage schedules for your Tower apps

#### `tower schedules list`

List all schedules

**Arguments:**

- `-a`, `--app` — Filter schedules by app name
- `-e`, `--environment` — Filter schedules by environment

#### `tower schedules create`

Create a new schedule for an app

**Arguments:**

- `-a`, `--app` *(required)* — The name of the app to schedule
- `-e`, `--environment` — The environment to run the app in
- `-c`, `--cron` *(required)* — The cron expression defining when the app should run
- `-p`, `--parameter` — Parameters (key=value) to pass to the app

#### `tower schedules delete`

Delete a schedule

**Arguments:**

- `<schedule_id>`  *(required)* — The schedule ID to delete

#### `tower schedules update`

Update an existing schedule

**Arguments:**

- `<id_or_name>`  *(required)* — ID or name of the schedule to update
- `-c`, `--cron` — The cron expression defining when the app should run
- `-p`, `--parameter` — Parameters (key=value) to pass to the app

### `tower secrets`

Interact with the secrets in your Tower account

#### `tower secrets list`

List secrets in your Tower account

**Arguments:**

- `-s`, `--show` — Show secrets in plain text
- `-e`, `--environment` — List secrets in this environment
- `-a`, `--all` — List secrets across all environments

#### `tower secrets create`

Create a new secret in your Tower account

**Arguments:**

- `-n`, `--name` *(required)* — Secret name to create
- `-e`, `--environment` — Environment to store the secret in
- `-v`, `--value` *(required)* — Secret value to store

#### `tower secrets delete`

Delete a secret in Tower

**Arguments:**

- `<secret_name>`  *(required)* — secret name, or environment/secret_name
- `-e`, `--environment` — environment to delete the secret from

### `tower environments`

Manage the environments in your current Tower account

#### `tower environments list`

List all of your environments

#### `tower environments create`

Create a new environment in Tower

**Arguments:**

- `-n`, `--name` *(required)*

### `tower deploy`

Deploy your latest code to Tower

**Arguments:**

- `-d`, `--dir` — The directory containing the app to deploy
- `-a`, `--all` - Deploy this app to all environments. You can only specify `-a` or `-e`, not both.
- `-e`, `--environment` — The environment to deploy this app to. You can only specifiy `-a` or `-e`, not both.
- `-f`, `--create` — Automatically force creation of the app if it doesn't already exist

### `tower run`

Run your code in Tower or locally

**Arguments:**

- `<app_name>`  — Name of a deployed app to run (uses ./Towerfile if omitted)
- `--dir` — The directory containing the Towerfile
- `--local` — Run this app locally
- `-e`, `--environment` — The environment to invoke the app in
- `-p`, `--parameter` — Parameters (key=value) to pass to the app
- `-d`, `--detached` — Don't follow the run output in your CLI

### `tower version`

Print the current version of Tower

### `tower teams`

View information about team membership and switch between teams

#### `tower teams list`

List teams you belong to

#### `tower teams switch`

Switch context to a different team

**Arguments:**

- `<team_name>`  *(required)* — Name of the team to switch to

### `tower mcp-server`

Runs an MCP server for LLM interaction

**Arguments:**

- `-t`, `--transport` — Transport mode
- `-p`, `--port` — Port for HTTP/SSE server (default: 34567)

### `tower skill`

Generate Claude Code skill files for AI agent integration

#### `tower skill generate`

Generate a SKILL.md describing how to use Tower with AI agents

