#!/usr/bin/env bash
# Install Lambda dependencies into build directories before terraform apply.
# Run from the project root: ./scripts/build-lambdas.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

build() {
  local name="$1"
  local src="$2"
  local dest="$ROOT/terraform/modules/${name}/builds/package"
  echo "Building $name..."
  rm -rf "$dest"
  mkdir -p "$dest"
  cp -r "$src"/. "$dest/"
  pip install \
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
