#!/usr/bin/env bash
# Install Lambda dependencies into build directories before terraform apply.
# Run from the project root: ./scripts/build-lambdas.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

PIP=$(command -v pip3 || command -v pip || true)
if [[ -z "$PIP" ]]; then
  echo "Error: pip not found. Install Python 3 or activate a virtualenv." >&2
  exit 1
fi

build() {
  local name="$1"
  local src="$2"
  local dest="$ROOT/terraform/modules/${name}/builds/package"
  echo "Building $name..."
  rm -rf "$dest"
  mkdir -p "$dest"
  cp -r "$src"/. "$dest/"
  cp "$ROOT/src/utils/ssm.py" "$dest/"
  "$PIP" install \
    --quiet \
    --target "$dest" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.12 \
    --only-binary=:all: \
    -r "$ROOT/requirements-lambda.txt"
  echo "  -> $dest"
}

build "ingestion" "$ROOT/src/ingestion"
build "query-api" "$ROOT/src/query"

echo "Done. Run terraform apply."
