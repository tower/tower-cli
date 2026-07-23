#!/usr/bin/env bash
# Reproducible DuckDB -> wasm32-wasi build for the sandbox spike.
#
# On first run this downloads wasi-sdk and the DuckDB amalgamation, then
# compiles a tiny test program that opens an in-memory DuckDB and runs a query.
# Run the result with:
#   wasmtime run -W exceptions=y -W function-references=y -W gc=y \
#     -W unknown-imports-default=y duckdb-wasi.wasm
#
# The compile is a single ~25MB translation unit, so it takes minutes. -O0 is
# used here for a fast viability signal; switch to -Oz for a shippable module.
set -euo pipefail
cd "$(dirname "$0")"

WASI_SDK_VERSION=33
DUCKDB_VERSION=v1.5.5   # amalgamation release; keep in step with the engine we ship

if [ ! -x wasi-sdk/bin/clang++ ]; then
  os=$(uname -s | tr 'A-Z' 'a-z'); arch=$(uname -m)
  case "$os-$arch" in
    darwin-arm64)   asset="arm64-macos" ;;
    darwin-x86_64)  asset="x86_64-macos" ;;
    linux-x86_64)   asset="x86_64-linux" ;;
    linux-aarch64)  asset="arm64-linux" ;;
    *) echo "unsupported $os-$arch; download wasi-sdk manually into ./wasi-sdk" >&2; exit 1 ;;
  esac
  echo "downloading wasi-sdk-$WASI_SDK_VERSION ($asset) ..."
  curl -sL "https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-$WASI_SDK_VERSION/wasi-sdk-$WASI_SDK_VERSION.0-$asset.tar.gz" | tar xz
  mv "wasi-sdk-$WASI_SDK_VERSION.0-$asset" wasi-sdk
fi

if [ ! -f duckdb.cpp ]; then
  echo "downloading DuckDB $DUCKDB_VERSION amalgamation ..."
  curl -sL -o libduckdb-src.zip "https://github.com/duckdb/duckdb/releases/download/$DUCKDB_VERSION/libduckdb-src.zip"
  unzip -o -q libduckdb-src.zip duckdb.cpp duckdb.hpp
fi

CXX=wasi-sdk/bin/clang++
SR=wasi-sdk/share/wasi-sysroot

echo "compiling duckdb.cpp -> duckdb-wasi.wasm (minutes) ..."
time "$CXX" --target=wasm32-wasip1 \
  -fwasm-exceptions -mllvm -wasm-use-legacy-eh=false \
  -DDUCKDB_NO_THREADS -DDUCKDB_DISABLE_BUILTIN_HTTPLIB \
  -D_WASI_EMULATED_MMAN -D_WASI_EMULATED_SIGNAL -D_WASI_EMULATED_PROCESS_CLOCKS -D_WASI_EMULATED_GETPID \
  -std=c++17 -O0 -I. -idirafter stubs -include wasi_stubs.h \
  -nostdlib++ duckdb.cpp main.cpp \
  -L"$SR/lib/wasm32-wasip1/eh" -lc++ -lc++abi -lunwind \
  -lwasi-emulated-mman -lwasi-emulated-signal -lwasi-emulated-process-clocks -lwasi-emulated-getpid \
  -Wl,--allow-undefined -o duckdb-wasi.wasm

echo "built duckdb-wasi.wasm ($(du -h duckdb-wasi.wasm | cut -f1))"
echo "run: wasmtime run -W exceptions=y -W function-references=y -W gc=y -W unknown-imports-default=y duckdb-wasi.wasm"
