# DuckDB on wasm32-wasi, run in wasmtime

This is the spike behind approach 3 in the parent README. It builds DuckDB core
to `wasm32-wasi` and runs a query in wasmtime with no V8 and no JavaScript. The
point is to prove the pioneering part is real, since there is no upstream WASI
build of DuckDB, and to capture the exact recipe so we do not have to rediscover
it.

## Run it

```
./build.sh
wasmtime run -W exceptions=y -W function-references=y -W gc=y \
  -W unknown-imports-default=y duckdb-wasi.wasm
# => DUCKDB_WASI_RESULT=1042
```

`build.sh` downloads wasi-sdk and the DuckDB amalgamation on first run. Requires
`wasmtime`, `curl`, and `unzip` on PATH. The compile is one ~25MB translation
unit, so expect a few minutes; the resulting `-O0` module is large (~100MB) and
shrinks a lot at `-Oz`.

## Toolchain

- wasi-sdk 33 (clang 22), which ships an exception-handling multilib.
- DuckDB amalgamation from `libduckdb-src.zip` of a DuckDB release, so no CMake.
- wasmtime 47 or newer, for the exceptions proposal.

## The gaps I had to close, and why

Each of these is a standard WASI-port fix. None was a wall, which is the main
result: a WASI DuckDB is buildable, just tedious.

- **Exceptions.** DuckDB needs C++ exceptions. clang's `-fwasm-exceptions`
  emits the legacy EH opcodes by default, which wasmtime 47 rejects, so I pass
  `-mllvm -wasm-use-legacy-eh=false` to get the new exnref model that wasmtime
  runs under `-W exceptions=y`. wasi-sdk's default libc++ is built without EH,
  so I link the `eh` multilib explicitly (`-nostdlib++ -L.../wasm32-wasip1/eh
  -lc++ -lc++abi -lunwind`).
- **Threads.** DuckDB has a first-class thread-free build, `-DDUCKDB_NO_THREADS`,
  which avoids pthreads entirely on single-threaded wasip1.
- **Bundled HTTP client.** The amalgamation bundles cpp-httplib, which uses
  POSIX sockets that WASI does not have. `-DDUCKDB_DISABLE_BUILTIN_HTTPLIB`
  excludes it. We route httpfs through host functions instead, so we do not want
  cpp-httplib anyway.
- **mmap and friends.** DuckDB uses mmap, signals, process clocks, and getpid.
  wasi-sdk provides emulated libraries for all of these
  (`-D_WASI_EMULATED_MMAN` and the matching `-lwasi-emulated-*`).
- **A handful of missing macros and declarations.** File locking constants,
  `struct winsize`/`TIOCGWINSZ`, `madvise`/`MADV_DONTNEED`, and `sched_getcpu`.
  These are in `wasi_stubs.h`, force-included on the compile line.
- **Stub imports.** Linking with `-Wl,--allow-undefined` turns a few unused
  symbols (`mlock`, sockets) into wasm imports. `wasmtime run
  -W unknown-imports-default=y` satisfies them with default-returning stubs for
  the spike. The real host supplies actual host functions.

## What this does not do yet

- No extensions. This is DuckDB core only. iceberg, parquet, and avro are not in
  the amalgamation and are the main open item, since they need their extension
  sources compiled and statically linked.
- No host. It runs standalone under `wasmtime run`. The real thing needs a Rust
  host with a WASI context that grants no filesystem and HTTP host functions
  that carry the egress allowlist.
- Not optimized. `-O0`, no `-Oz`, no wasmtime AOT cache. Those are what turn the
  slow first run into a fast cached one-shot.
