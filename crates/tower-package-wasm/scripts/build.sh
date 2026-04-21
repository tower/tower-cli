#!/usr/bin/env bash
# Build the tower-package-wasm npm package.
#
# Runs wasm-pack and replaces the generated `.d.ts` (which types inputs as
# `any`) with our hand-written typed interface.

set -euo pipefail

CRATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$CRATE_DIR"

TARGET="${1:-bundler}"
OUT_DIR="pkg"

wasm-pack build . --target "$TARGET" --release --out-dir "$OUT_DIR"

cp types.d.ts "$OUT_DIR/tower_package_wasm.d.ts"

echo "Built tower-package-wasm npm package at $CRATE_DIR/$OUT_DIR"
