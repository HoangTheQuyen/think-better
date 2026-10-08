#!/bin/sh
# Think Better - Build Script (Linux / macOS)
# Equivalent of `make build` for users without make: same version, commit and
# build date in the binary (override with VERSION, COMMIT, BUILD_DATE).
set -e

VERSION="${VERSION:-$(git describe --tags --always --dirty 2>/dev/null || echo dev)}"
COMMIT="${COMMIT:-$(git rev-parse --short HEAD 2>/dev/null || echo unknown)}"
# Commit date rather than the current time, so rebuilding a commit gives the same binary.
BUILD_DATE="${BUILD_DATE:-$(git log -1 --format=%cs 2>/dev/null || echo unknown)}"

echo "=== Think Better Build ($VERSION) ==="
go generate ./internal/skills
mkdir -p bin
CGO_ENABLED=0 go build \
  -ldflags "-s -w -X main.version=$VERSION -X main.commit=$COMMIT -X main.buildDate=$BUILD_DATE" \
  -o bin/think-better ./cmd/think-better
echo "Built: bin/think-better"
