#!/usr/bin/env bash
set -euo pipefail

if [ "${MODE:-}" = "sleep" ]; then
  # Start a child and wait on it, so tests can check that cancelling stops it too.
  sleep 300 &
  echo "child pid: $!"
  wait
  exit 0
fi

echo "The greeting is: ${GREETING:-unset}"
echo "The parent variable is: ${BASH_TEST_PARENT_VARIABLE:-unset}"

# More than a pipe buffer (64 KiB), so the script blocks unless its output is read.
pad=$(printf '%0.sx' $(seq 1 90))
for i in $(seq 1 2000); do
  echo "filler $i $pad"
done
