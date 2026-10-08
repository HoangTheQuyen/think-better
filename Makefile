# Think Better - Build Automation
# Framework + AI for clear thinking and better decisions

BINARY_NAME := think-better
CMD_PATH := ./cmd/think-better
BIN_DIR := bin

# Version injection via ldflags
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
COMMIT ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_DATE ?= $(shell date -u +%Y-%m-%d 2>/dev/null || echo "unknown")
LDFLAGS := -s -w \
	-X main.version=$(VERSION) \
	-X main.commit=$(COMMIT) \
	-X main.buildDate=$(BUILD_DATE)

# Cross-compilation targets
PLATFORMS := linux/amd64 linux/arm64 darwin/amd64 darwin/arm64 windows/amd64 windows/arm64

.PHONY: all build build-all test test-cover test-py check clean embed-prep lint fmt tidy help release-snapshot

all: embed-prep build

## embed-prep: Mirror .agents/ skills and workflows into internal/skills for embedding
embed-prep:
	go generate ./internal/skills

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

## test-py: Smoke-test the Python skill scripts
test-py:
	python3 scripts/smoke_test_skills.py

## check: Everything CI runs — use before opening a PR
check:
	go vet ./...
	go test ./...
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

## fmt: Format Go source files
fmt:
	gofmt -s -w .
	goimports -w -local github.com/HoangTheQuyen/think-better .

## tidy: Tidy and verify Go module dependencies
tidy:
	go mod tidy
	go mod verify

## release-snapshot: Dry-run the GoReleaser release locally (output in dist/)
release-snapshot:
	goreleaser release --snapshot --clean

## help: Show available targets
help:
	@grep -E '^## ' Makefile | sed 's/^## /  /' | sed 's/: /\t/'

