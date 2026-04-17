use clap::Command;

pub fn skill_cmd() -> Command {
    Command::new("skill")
        .about("Generate Claude Code skill files for AI agent integration")
        .arg_required_else_help(true)
        .subcommand(
            Command::new("generate")
                .about("Generate a SKILL.md describing how to use Tower with AI agents"),
        )
}

pub async fn do_skill_generate(root: Command) {
    let content = generate_skill_md(root);
    print!("{}", content);
}

fn generate_skill_md(root: Command) -> String {
    let mut out = String::new();

    out.push_str(WORKFLOW_HEADER);
    out.push_str("\n\n");
    out.push_str("## Command Reference\n\n");
    out.push_str("*This section is generated from the CLI's built-in help.*\n\n");

    append_command(&mut out, &root, &[], 3);

    out
}

fn append_command(out: &mut String, cmd: &Command, path: &[&str], depth: usize) {
    let subcommands: Vec<_> = cmd
        .get_subcommands()
        .filter(|c| !c.is_hide_set())
        .collect();

    for sub in &subcommands {
        let name = sub.get_name();
        let mut full_path = path.to_vec();
        full_path.push(name);

        let heading = "#".repeat(depth);
        let cmd_str = format!("tower {}", full_path.join(" "));
        out.push_str(&format!("{} `{}`\n\n", heading, cmd_str));

        if let Some(about) = sub.get_about() {
            out.push_str(&format!("{}\n\n", about));
        }

        // Positional args
        let positional: Vec<_> = sub
            .get_arguments()
            .filter(|a| a.is_positional() && !a.is_hide_set())
            .collect();

        // Named args / flags
        let named: Vec<_> = sub
            .get_arguments()
            .filter(|a| !a.is_positional() && !a.is_hide_set() && a.get_long().is_some())
            .collect();

        if !positional.is_empty() || !named.is_empty() {
            out.push_str("**Arguments:**\n\n");
            for arg in &positional {
                let req = if arg.is_required_set() {
                    " *(required)*"
                } else {
                    ""
                };
                let help = arg
                    .get_help()
                    .map(|h| format!(" — {}", h))
                    .unwrap_or_default();
                out.push_str(&format!(
                    "- `<{}>` {}{}\n",
                    arg.get_id(),
                    req,
                    help
                ));
            }
            for arg in &named {
                let long = arg.get_long().unwrap();
                let req = if arg.is_required_set() {
                    " *(required)*"
                } else {
                    ""
                };
                let help = arg
                    .get_help()
                    .map(|h| format!(" — {}", h))
                    .unwrap_or_default();
                if let Some(short) = arg.get_short() {
                    out.push_str(&format!("- `-{}`, `--{}`{}{}\n", short, long, req, help));
                } else {
                    out.push_str(&format!("- `--{}`{}{}\n", long, req, help));
                }
            }
            out.push('\n');
        }

        let child_subs: Vec<_> = sub
            .get_subcommands()
            .filter(|c| !c.is_hide_set())
            .collect();

        if !child_subs.is_empty() {
            append_command(out, sub, &full_path, depth + 1);
        }
    }
}

const WORKFLOW_HEADER: &str = r#"---
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
- Always use MCP tools to modify Towerfiles (never edit TOML files manually)"#;
