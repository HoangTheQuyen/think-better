#!/bin/bash
# Think Better - Build Script (Linux / macOS)
# Equivalent of `make build` for users without make

set -e

echo "=== Think Better Build ==="

# Step 1: Prepare embedded skills
echo "Preparing embedded skills..."
SKILLS_DIR="internal/skills/skills"
rm -rf "$SKILLS_DIR"
mkdir -p "$SKILLS_DIR"
cp -r .github/prompts/make-decision "$SKILLS_DIR/make-decision"
cp -r .github/prompts/problem-solving-pro "$SKILLS_DIR/problem-solving-pro"
find "$SKILLS_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "Done: skills ready for embedding"

# Step 2: Build
echo "Building..."
mkdir -p bin
CGO_ENABLED=0 go build -o bin/think-better ./cmd/make-decision
echo "Built: bin/think-better"
