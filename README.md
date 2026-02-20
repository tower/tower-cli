# Tower CLI

The CLI and Python runtime for Tower - deploy AI-generated and hand-written Python to production in minutes.

Built for teams shipping vertical AI services and SaaS.

> Bridge the last mile from code to production.

![PyPI Version](https://img.shields.io/pypi/v/tower)
![License](https://img.shields.io/pypi/l/tower)
![PyPI Downloads](https://img.shields.io/pypi/dm/tower)

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

Shipping AI-generated or hand-written Python but struggling to:

- Turn scripts into production services
- Expose APIs for users and tenants
- Store and query analytical data
- Run reliably across environments

Tower gives you:

- **Python-native orchestration** and control-plane APIs for pipelines and agents.
- **Same code locally and in the cloud** - one CLI; serverless or your own compute.
- **Observability, user/tenant management**, and managed Iceberg storage (Snowflake, Spark compatible).

---

## Quick Start

1. **Install** (see above) and **log in**:

   ```bash
   tower login
   ```

2. **Clone the example repo** (includes a `Towerfile` and hello-world app):

   ```bash
   git clone https://github.com/tower/tower-examples
   cd tower-examples/01-hello-world
   ```

3. **Create an app and run it**:

   ```bash
   tower apps create --name="hello-world"
   tower deploy
   tower run
   ```

4. **Expected output** (after a run is scheduled):

   ```
   ✔ Scheduling run... Done!
   Success! Run #1 for app `hello-world` has been scheduled
   ```

Full walkthrough: **[Quick Start](https://docs.tower.dev/docs/getting-started/quick-start)**

## Using Tower with Claude (MCP)

You can build, deploy, and manage Tower apps through natural language using the Tower MCP server. Tower includes an MCP (Model Context Protocol) server that allows AI coding assistants like Claude to interact directly with your Tower apps.

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

   > Create a Python app that fetches data from an API and prints a summary. Deploy it to Tower and run it.

Full walkthrough: **[Quickstart with MCP](https://docs.tower.dev/docs/getting-started/quickstart-with-mcp)**

If this saved you time, consider giving the repo a ⭐.

---

## Features

- **Same code locally and in the cloud** - `tower run` anywhere; your compute or Tower serverless. No environment drift.
- **Deploy in under 30 seconds** - `tower deploy` packages and ships; code encrypted at rest.
- **Secrets** - CLI-managed; injected as env vars in runner only (E2E encrypted).
- **Optional AI and Iceberg** - `tower[ai]` or `tower[iceberg]`; [details](INSTALL-AND-REFERENCE.md#optional-features).
- **MCP server** - Deploy and launch runs from AI coding assistants.

---

## Demo

**[▶ Tower demo (YouTube)](https://www.youtube.com/watch?v=r0TuiO7B-eQ)**

---

## Use Cases

- **Data pipelines** - ELT, dbt Core, notebooks, batch jobs.
- **Data agents** - Fresh data, Tower apps as tools, lakehouse queries.
- **Platforms and SaaS** - Multi-tenant apps, headless data stacks.
- **Sensitive / on-prem** - Self-hosted runners; data stays in your env.

In production at [Inflow](https://tower.dev), [dltHub](https://dlthub.com/blog/tower), [a-Gnostics](https://blog.softelegance.com/a-gnostics/how-a-gnostics-improved-electricity-consumption-forecasts-with-a-faster-and-more-cost-effective-weather-service-and-tower-dev/), and others.

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

- GUI-first pipeline design (Tower is code/CLI-first).
- GPU-heavy model training or inference as the primary workload.

---

## Contributing

PRs and issues are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and [DEVELOPMENT.md](DEVELOPMENT.md).

If this helped you ship, consider giving the repo a ⭐.

---

## License and maintenance

- **License:** [MIT](LICENSE).
- Actively maintained; issues responded to promptly.

[Full install options and optional features →](INSTALL-AND-REFERENCE.md)
