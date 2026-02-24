# Tower CLI

The CLI and Python runtime for Tower - deploy your AI and hand-written Python code to production in minutes.

> Bridge the last mile from code to production.

![PyPI Version](https://img.shields.io/pypi/v/tower?style=flat&color=blue)
![License](https://img.shields.io/pypi/l/tower?style=flat&color=blue)
[![Monthly Downloads](https://static.pepy.tech/personalized-badge/tower?period=monthly&units=INTERNATIONAL_SYSTEM&left_color=blue&right_color=blue&left_text=monthly%20downloads)](https://pepy.tech/projects/tower)
[![Discord](https://img.shields.io/badge/Discord-Tower.dev-blue?style=flat&logo=discord&logoColor=white)](https://discord.gg/7vjtmk2X5e)

[![Tower demo](https://img.youtube.com/vi/r0TuiO7B-eQ/maxresdefault.jpg)](https://www.youtube.com/watch?v=r0TuiO7B-eQ)

## What is [Tower](https://tower.dev)?

Code-first platform for deploying Python data apps, pipelines, and AI agents, with built-in orchestration, analytical storage, and multi-tenant APIs. Works natively with AI coding assistants via MCP.

## Install

```bash
pip install -U tower
```

[Other install options](INSTALL-AND-REFERENCE.md#installing-the-tower-cli) (Nix, Devenv, releases).

---

## Why Tower?

Are you shipping your Python code to prod but struggling to:

- Turn scripts into production services
- Expose APIs for users and customers/tenants
- Store and query analytical data
- Run reliably across environments

Tower gives you:

- **Python-native orchestration** and control-plane APIs for pipelines and agents.
- **Consistent execution environment** for your code; run on serverless or your own compute.
- **Observability, user and tenant management**, and managed Iceberg storage (Snowflake, Spark compatible).

---

## Quick Start

1. **Install** (see above) and **log in**:

   ```bash
   tower login
   ```

2. **Clone the example repo** (includes the hello-world app):

   ```bash
   git clone https://github.com/tower/tower-examples
   cd tower-examples/01-hello-world
   ```

3. **Create an app and run it**:

   ```bash
   tower deploy
   tower run
   ```

4. **Expected output**:

   ```
   ✔ Scheduling run... Done!
   Success! Run #1 for app `hello-world` has been scheduled
   ```

Full walkthrough: **[Quick Start](https://docs.tower.dev/docs/getting-started/quick-start)**

## Using Tower with Claude, Cursor and other AI assistants (MCP)

You can build, deploy, and manage Tower apps through natural language using the Tower MCP server. Tower includes an MCP (Model Context Protocol) server that allows AI code assistants like Claude or Cursor to interact directly with your Tower apps.

Full walkthrough: **[Quickstart with MCP](https://docs.tower.dev/docs/getting-started/quickstart-with-mcp)**

### Add Tower to Claude

1. **Add the MCP server to Claude:**

   ```bash
   claude mcp add tower tower mcp-server
   ```

2. **Clone the examples and start a Claude session:**

   ```bash
   git clone https://github.com/tower/tower-examples
   cd tower-examples
   claude
   ```

3. **Ask Claude to build and deploy** — for example:

   > Create a Python app that fetches stock ticker data from the Yahoo Finance API and prints a summary. Deploy it to Tower and run it.


### Add Tower to Cursor

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en-US/install-mcp?name=tower&config=eyJjb21tYW5kIjoidG93ZXIiLCJhcmdzIjpbIm1jcC1zZXJ2ZXIiXX0=) 

Or [open this link directly](cursor://anysphere.cursor-deeplink/mcp/install?name=tower&config=eyJjb21tYW5kIjoidG93ZXIiLCJhcmdzIjpbIm1jcC1zZXJ2ZXIiXX0=).

If that doesn't work, see the **[MCP Server reference](https://docs.tower.dev/docs/reference/mcp-server)** for additional setup instructions.

### Add Tower to other AI Assistants 

Using a different AI assistant like Zed, VS Code or Gemini? See the **[MCP Server reference](https://docs.tower.dev/docs/reference/mcp-server)** for setup instructions across all supported clients.


If you find Tower useful, consider giving the repo a ⭐.

---

## Features

- **Consistent execution environment everywhere** - `tower run` on Tower serverless or your own compute.
- **Deploy in under 30 seconds** - `tower deploy` packages and ships.
- **Secrets** - CLI-managed; injected as env vars in runner only (E2E encrypted).
- **Optional AI inference, Iceberg or dbt** - `tower[ai]`, `tower[iceberg]` or `tower[dbt]`; [details](INSTALL-AND-REFERENCE.md#optional-features).
- **MCP server** - Deploy and launch runs from AI coding assistants; [details](https://docs.tower.dev/docs/reference/mcp-server).

---

## Demo

**[▶ Tower demo (YouTube)](https://www.youtube.com/watch?v=r0TuiO7B-eQ)**

---

## Use Cases

- **Data pipelines** - ELT, dbt Core, dltHub, batch jobs.
- **Interactive apps and APIs** - Marimo notebooks, FastAPI endpoints.
- **Data agents** - Fresh, company-specific data, Tower apps as Agentic Tools, lakehouse as facts database.
- **Platforms and SaaS** - Multi-tenant apps, headless data stacks.
- **Sensitive data workloads / on-prem** - Self-hosted runners; data stays in your environment.

In production at [CosmoLaser](https://tower.dev/blog/how-cosmolaser-s-chief-marketer-uses-claude-code-to-run-his-etl-pipelines-on-tower), [Inflow](http://tower.dev/#testimonials), [dltHub](https://dlthub.com/blog/tower), [a-Gnostics](https://blog.softelegance.com/a-gnostics/how-a-gnostics-improved-electricity-consumption-forecasts-with-a-faster-and-more-cost-effective-weather-service-and-tower-dev/), and others.

---

## Comparison

Tower replaces the typical stack of Airflow + custom APIs + storage with one platform.

| Feature | GitHub Actions | Airflow + self‑managed compute | Dagster | Tower |
|--------|----------------|--------------------------------|--------|--------|
| **Flow orchestration** (data/control flows) | Partial (1) | Yes | Yes | Yes |
| **Flexible compute** (self‑hosted + serverless) | Yes | Partial (2) | Partial (3) | Yes |
| **Analytical storage** (lakehouse tooling) | No | No | No | Yes |
| **Multi-tenant platform** (APIs, users, apps) | No | No | Partial (4) | Yes |

(1) GH Actions has orchestration primitives but no flow support.  
(2) Typically requires a managed Airflow service.  
(3) Self-hosted Dagster requires hosting both data and control planes.  
(4) Run-triggering APIs exist; user management depends on Dagster Cloud vs self-hosted.

---

## How It Works

```
┌────────────┐     ┌─────┐     ┌──────────────────────┐     ┌────────┐     ┌───────────┐
│ Developer  │ ──► │ CLI │ ──► │ Tower Control Plane  │ ──► │ Runner │ ──► │ Lakehouse │
└────────────┘     └─────┘     └──────────────────────┘     └────────┘     └───────────┘
```

With an AI coding assistant (e.g. Claude, Cursor), the flow goes through the Tower MCP server:

```
┌────────────┐     ┌────────┐     ┌──────────────────┐     ┌──────────────────────┐
│ Developer  │ ──► │ Claude │ ──► │ MCP (Tower CLI)  │ ──► │ Tower Control Plane  │ ──► ...
└────────────┘     └────────┘     └──────────────────┘     └──────────────────────┘
```

- **Apps** - Python + `requirements.txt` + **Towerfile** (entrypoint, source). Any Python; no SDK required.
- **Deploy** - `tower deploy` builds, uploads, stores encrypted. Tower cannot read your code.
- **Secrets** - `tower secrets`; env vars in runner only (AES-256).
- **Runtime** - Runner pulls app/config, decrypts, runs in sandboxed Python. Same model locally and in cloud.

[How Tower works](https://docs.tower.dev/docs/architecture/how-tower-works).

---

## Roadmap

- [x] Code-first orchestration
- [x] Observability
- [x] Self-hosted runners
- [x] Interactive apps
- [ ] Organizations
- [ ] RBAC
- [ ] Iceberg ingestion

---

## Not For

- GUI-first pipeline design (Tower is natural language / code / CLI-first).
- GPU-heavy model training or inference as the primary workload (Tower offloads GPU inference to cloud services).

---

## Contributing

PRs and issues are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and [DEVELOPMENT.md](DEVELOPMENT.md).

If you found Tower useful, consider giving the repo a ⭐.

---

## License

- **License:** [MIT](LICENSE).

[Full installation options and optional features →](INSTALL-AND-REFERENCE.md)
