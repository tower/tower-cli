# duckdb-wasm in V8 via deno_core (reference only)

This is the working host from approach 2 in the parent README. We are not taking
it forward, since approach 3 (WASI in wasmtime) is better for our one-shot use
case, but the code is kept because two pieces of it carry directly over to the
WASI host.

Worth reusing:

- **The egress allowlist.** `op_http_sync` in `src/main.rs` is the single choke
  point for all engine network I/O. It checks the request host against an
  allowlist, serves bundled extensions from local files, and denies everything
  else. The WASI host needs the same logic behind wasmtime host functions.
- **Arrow-IPC marshaling.** The host drives `runQuery` to get raw Arrow IPC
  bytes and decodes them in Rust with the `arrow` crate, which avoids pulling
  apache-arrow's JavaScript into the sandbox. The WASI host wants the same.

What this proved, for the record: duckdb-wasm's blocking API runs headless under
`deno_core` on stable Rust, a real Iceberg-over-S3 query runs end to end with all
network forced through the allowlist, and a native-versus-wasm benchmark on 1M
rows over MinIO (warm query competitive, cold start 1820ms then 755ms after
bundling extensions locally).

This is captured as-is and is not runnable without edits. Paths to the DuckDB
wasm and the arrow package are hardcoded to my spike environment, and the wasm
plus the benchmark's native DuckDB arm are not included. Read it, do not build
it.
