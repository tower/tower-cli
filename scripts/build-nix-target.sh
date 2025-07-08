#!/usr/bin/env bash
cd "$(dirname "$0")/.."

VERSION=$(python scripts/semver.py)
export VERSION

TARGET=${1:-tower-deb-arm64}

nix build .#${TARGET} --impure

cp result/* ./ && rm result
