# DuckDB query sandbox: runtime options

This directory records the sandboxing work for agent-issued catalog queries so
we can choose a direction deliberately. It is a design record plus the spike
code behind it. None of it is wired into the shipped CLI yet.

## Why this matters

The MCP server lets an agent run SQL against a customer's Iceberg catalog, and
the agent is driven by a model, so a prompt injection can steer it into hostile
SQL. DuckDB SQL is close to arbitrary code: it can read local files, reach the
network, load extensions, and consume unbounded resources. Without a sandbox a
single poisoned prompt could read `~/.aws/credentials` off the developer's
machine, exfiltrate it over httpfs, or write a payload to disk. So the question
is not whether to sandbox but which mechanism to run the engine inside.

I evaluated three approaches, from least to most isolation.

## 1. Native DuckDB with configuration hardening (shipped)

This is the approach on the PR branch (`features/add-catalog-querying-to-mcp-server`,
PR #328). It runs the normal in-process native DuckDB and locks the session
down with DuckDB's own settings: `disabled_filesystems = 'LocalFileSystem'`,
`allow_community_extensions = false`, and `lock_configuration = true`, applied
after the catalog is attached, plus a read-only credential vend, a single
read-only statement gate, and a row cap. See `crates/tower-cmd/src/catalogs.rs`
on that branch, including the adversarial regression suite and the
MinIO-backed integration test.

What I confirmed:

- It blocks the attacks that matter. The adversarial suite exercises host file
  reads and writes, configuration escapes, arbitrary extension loads, write and
  DDL statements, statement smuggling, and network SSRF through table
  functions, and all are refused.
- It does not break the real read path. The MinIO integration test seeds a real
  Iceberg table on object storage and reads it back with the full hardening on,
  which passes. `disabled_filesystems` only disables local disk, so the S3 reads
  Iceberg does still work.

The stakes with this approach: it is defense by configuration, not isolation.
The engine still runs in-process, so a memory-safety bug in DuckDB is a host
compromise, and the network is only narrowed as a side effect (table functions
happen to glob through the disabled local filesystem). It is a solid interim
baseline and I would ship it, but it is not the end state.

## 2. duckdb-wasm hosted in V8 via deno_core

I embedded the prebuilt `@duckdb/duckdb-wasm` engine in an embedded V8 through
`deno_core`, on stable Rust, and ran a real Iceberg-over-S3 query end to end
inside the sandbox with every network call forced through a host op that
enforces an egress allowlist. The reference host is in `deno-core-reference/`.

The reason I did not stay here is cost. The measured numbers on a 1M-row
Iceberg table over local MinIO:

| metric | native | wasm (V8) |
| --- | --- | --- |
| warm query, count (metadata) | 9 ms | 7 ms |
| warm query, scan+aggregate | 11 ms | 16 ms |
| cold start | not measured | 1820 ms, then 755 ms |

Warm latency is competitive. The problem is cold start, which is what a one-shot
`tower catalogs query` pays every time. Bundling the extensions locally instead
of fetching them from the DuckDB CDN cut it from 1820 ms to 755 ms, and that is
required for packaging anyway. The remaining ~570 ms is V8 compiling the wasm on
every run. I checked whether we could cache the compiled module across runs, and
the `v8` crate does not expose serialization of a compiled wasm module, so we
cannot. Add roughly 30 MB of V8 plus a browser-shaped polyfill layer to
maintain, and the tradeoff is poor for a one-shot CLI.

## 3. Custom DuckDB on wasm32-wasi in wasmtime (recommended)

Brad's observation was the turning point: deno_core and V8 are only forced by
using the prebuilt Emscripten duckdb-wasm. If we build our own DuckDB we can
target `wasm32-wasi` and run it in wasmtime, with no V8 and no JavaScript at all.
I proved this is buildable. DuckDB core compiled to `wasm32-wasi` and ran
`SELECT 42 + count(*) FROM range(1000)` in wasmtime, returning the correct
`1042`. The build recipe and the exact gaps I had to close are in
`wasi-wasmtime/`.

Why this is the better end state:

- It fixes the cold start that killed approach 2. wasmtime has on-disk AOT
  compile caching, so the compile cost is paid once and cached, and later runs
  load precompiled machine code in milliseconds. That is the sub-200 ms one-shot
  latency V8 could not give us, with no daemon.
- It drops V8, so the binary is roughly 30 MB smaller and there is no polyfill
  layer to maintain.
- It is a capability sandbox by construction. wasmtime grants nothing by
  default, and the host functions are the only way out, so the egress allowlist
  is structural rather than a side effect.
- The networking work carries over. WASI has no sockets, so httpfs has to route
  through host functions regardless, which is the same allowlisted host op I
  already built for approach 2.

The build was tedious but bounded. Every gap had a standard WASI-port fix
(`DUCKDB_NO_THREADS`, the wasi-sdk exception multilib, the wasi emulated libs,
a small stub header, and excluding the bundled cpp-httplib), and none was a
wall. Details in `wasi-wasmtime/README.md`.

## A finding that reinforces the recommendation: extensions are not baked in

In both the native and the duckdb-wasm paths, httpfs, iceberg, parquet, and avro
are not compiled into the engine. They are downloaded from the DuckDB extension
CDN at runtime and cached to `~/.duckdb`. `duckdb_extensions()` shows an
`install_path` under `extensions.duckdb.org` rather than `(BUILT-IN)`. That means
a fresh machine needs network to `extensions.duckdb.org` on the first query, it
is a runtime supply-chain fetch, and the install and load must happen before the
filesystem lockdown. The custom WASI build is the one place we can statically
link those extensions at compile time, which removes the runtime fetch, makes it
work offline, and collapses packaging to a single self-contained module. The
native crate can static-link httpfs and parquet through cargo features, but there
is no iceberg feature, so native is stuck fetching iceberg regardless.

## Recommendation

Ship approach 1 as the interim baseline, since it blocks the real attacks today
and is already tested. Build approach 3 as the real sandbox: a custom
`wasm32-wasi` DuckDB with the extensions linked in, run in wasmtime behind host
functions. Skip approach 2. It works, but it is strictly worse than 3 for our
one-shot use case.

## Next steps

These are roughly independent, so they are easy to divide up.

1. Static-link iceberg, parquet, and avro into the WASI build. This is the main
   open unknown, since the core amalgamation does not include them and I have not
   tried their extension sources under wasi-sdk yet.
2. Build the Rust wasmtime host: a WASI context with no filesystem, HTTP host
   functions carrying the egress allowlist, and Arrow-IPC result marshaling back
   to Rust. The allowlist and marshaling designs come straight from
   `deno-core-reference/`.
3. Turn on `-Oz` and wasmtime's AOT cache, then measure real one-shot cold start.
4. Wire it into the CLI behind a flag, as a build step that produces and embeds
   the wasm, and run the adversarial suite from PR #328 against it as a
   conformance check.

## What is in this branch

- `wasi-wasmtime/` is the WASI build spike: a reproducible `build.sh`, the test
  program, and the stub headers, with the large downloads gitignored.
- `deno-core-reference/` is the working V8 host from approach 2, kept for the
  egress-allowlist and Arrow-IPC patterns even though we are not taking it
  forward.
- The native hardening and its tests live on the PR #328 branch, not here.
