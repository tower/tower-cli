#!/usr/bin/env bash
# Build the tower-package WebAssembly npm package.
#
# Runs wasm-pack against the tower-package crate with only the `wasm`
# feature, replaces the generated `.d.ts` (which types inputs as `any`)
# with the hand-written typed interface, and renames the npm package to
# `tower-package-wasm` so the Rust crate and the npm package can have
# different names.

set -euo pipefail

CRATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$CRATE_DIR"

TARGET="${1:-bundler}"
OUT_DIR="pkg"

wasm-pack build . \
    --target "$TARGET" \
    --release \
    --out-dir "$OUT_DIR" \
    -- \
    --no-default-features \
    --features wasm

cp types.d.ts "$OUT_DIR/tower_package.d.ts"

sed -i.bak 's/"name": "tower-package"/"name": "tower-package-wasm"/' "$OUT_DIR/package.json"
rm "$OUT_DIR/package.json.bak"

echo "Built tower-package-wasm npm package at $CRATE_DIR/$OUT_DIR"
