# Think Better - Build Automation
# Framework + AI for clear thinking and better decisions

BINARY_NAME := think-better
CMD_PATH := ./cmd/think-better
BIN_DIR := bin

# Version injection via ldflags
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
COMMIT ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
# Commit date rather than the current time, so rebuilding a commit gives the
# same binary (GoReleaser does the same for releases).
BUILD_DATE ?= $(shell git log -1 --format=%cs 2>/dev/null || echo "unknown")
LDFLAGS := -s -w \
	-X main.version=$(VERSION) \
	-X main.commit=$(COMMIT) \
	-X main.buildDate=$(BUILD_DATE)

# Same golangci-lint version as CI (.github/workflows/ci.yml, lint job)
GOLANGCI_LINT_VERSION := v2.5.0

# Cross-compilation targets
PLATFORMS := linux/amd64 linux/arm64 darwin/amd64 darwin/arm64 windows/amd64 windows/arm64

.PHONY: all build build-all test test-cover test-py check clean embed-prep known-hashes lint fmt tidy help release-check release-snapshot

all: embed-prep build

## embed-prep: Mirror .agents/ skills and workflows into internal/skills for embedding
embed-prep:
	go generate ./internal/skills

## known-hashes: Record what every release tag installed (internal/installer/known_hashes.json); run after tagging a release
known-hashes:
	go run ./internal/installer/gen

## build: Build for current platform
build: embed-prep
	@mkdir -p $(BIN_DIR)
	CGO_ENABLED=0 go build -ldflags "$(LDFLAGS)" -o $(BIN_DIR)/$(BINARY_NAME) $(CMD_PATH)
	@echo "Built: $(BIN_DIR)/$(BINARY_NAME)"

## build-all: Cross-compile for all platforms
build-all: embed-prep
	@mkdir -p $(BIN_DIR)
	@$(foreach platform,$(PLATFORMS), \
		$(eval OS := $(word 1,$(subst /, ,$(platform)))) \
		$(eval ARCH := $(word 2,$(subst /, ,$(platform)))) \
		$(eval EXT := $(if $(filter windows,$(OS)),.exe,)) \
		echo "Building $(OS)/$(ARCH)..." ; \
		CGO_ENABLED=0 GOOS=$(OS) GOARCH=$(ARCH) go build \
			-ldflags "$(LDFLAGS)" \
			-o $(BIN_DIR)/$(BINARY_NAME)-$(OS)-$(ARCH)$(EXT) $(CMD_PATH) ; \
	)
	@echo "Built all platforms:"
	@ls -la $(BIN_DIR)/

## test: Run all tests
test:
	go test ./...

## test-py: Smoke-test the Python skill scripts, run their regression tests and check the docs (counts, links, samples)
test-py:
	python3 scripts/smoke_test_skills.py
	python3 scripts/test_skill_engines.py
	python3 scripts/test_docs.py  # also re-runs the doc samples (scripts/test_doc_samples.py)

## check: What CI runs (vet, Go tests, lint if golangci-lint is installed, Python tests) - use before opening a PR
check:
	go vet ./...
	go test ./...
	@if command -v golangci-lint >/dev/null 2>&1; then \
		$(MAKE) lint; \
	else \
		echo "NOTE: golangci-lint not found, skipping lint. CI runs $(GOLANGCI_LINT_VERSION); install it with:"; \
		echo "  go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@$(GOLANGCI_LINT_VERSION)"; \
	fi
	$(MAKE) test-py

## test-cover: Run tests with coverage
test-cover:
	go test -cover ./...

## clean: Remove build artifacts
clean:
	rm -rf $(BIN_DIR)

## lint: Run golangci-lint
lint:
	golangci-lint run ./...

## fmt: Format Go source files (gofmt + goimports, as configured in .golangci.yml)
fmt:
	@if command -v golangci-lint >/dev/null 2>&1; then \
		golangci-lint fmt ./...; \
	else \
		echo "NOTE: golangci-lint not found, running gofmt only (import grouping is not fixed)"; \
		gofmt -s -w .; \
	fi

## tidy: Tidy and verify Go module dependencies
tidy:
	go mod tidy
	go mod verify

## release-check: Validate .goreleaser.yaml (allows only the known brews deprecation)
release-check:
	sh .github/scripts/goreleaser-check.sh

## release-snapshot: Dry-run the release locally, unsigned (output in dist/; SBOMs need syft)
release-snapshot:
	goreleaser release --snapshot --clean --skip=sign

## help: Show available targets
help:
	@grep -E '^## ' Makefile | sed 's/^## /  /' | sed 's/: /\t/'

