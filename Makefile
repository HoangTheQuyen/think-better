# Think Better - Build Automation
# Framework + AI for clear thinking and better decisions

BINARY_NAME := think-better
CMD_PATH := ./cmd/make-decision
BIN_DIR := bin
SKILLS_DIR := internal/skills/skills

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

.PHONY: all build build-all test clean embed-prep lint fmt tidy

all: embed-prep build

## embed-prep: Copy skill and workflow files into internal/ for embedding
embed-prep:
	@echo "Preparing embedded skills..."
	@rm -rf $(SKILLS_DIR)
	@mkdir -p $(SKILLS_DIR)
	@cp -r .agents/skills/make-decision $(SKILLS_DIR)/make-decision
	@cp -r .agents/skills/problem-solving-pro $(SKILLS_DIR)/problem-solving-pro
	@find $(SKILLS_DIR) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "Preparing embedded workflows..."
	@rm -rf internal/skills/workflows
	@mkdir -p internal/skills/workflows
	@cp .agents/workflows/*.md internal/skills/workflows/
	@echo "Done: skills + workflows ready for embedding"

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

## test-cover: Run tests with coverage
test-cover:
	go test -cover ./...

## clean: Remove build artifacts
clean:
	rm -rf $(BIN_DIR) $(SKILLS_DIR)

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

## help: Show available targets
help:
	@grep -E '^## ' Makefile | sed 's/^## /  /' | sed 's/: /\t/'

