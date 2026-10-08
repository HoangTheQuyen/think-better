#!/bin/sh
# Think Better - Build Script (Linux / macOS)
# Equivalent of `make build` for users without make
set -e

echo "=== Think Better Build ==="
go generate ./internal/skills
mkdir -p bin
CGO_ENABLED=0 go build -o bin/think-better ./cmd/think-better
echo "Built: bin/think-better"
