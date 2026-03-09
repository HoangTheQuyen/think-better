#!/bin/bash
# Think Better — One-liner installer for macOS / Linux
# Usage: curl -sSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh | bash
set -e

REPO="HoangTheQuyen/think-better"
BINARY="think-better"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"

# --- Detect platform ---
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$OS" in
  linux)  OS="linux" ;;
  darwin) OS="darwin" ;;
  *)      echo "❌ Unsupported OS: $OS"; exit 1 ;;
esac

case "$ARCH" in
  x86_64|amd64)  ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *)             echo "❌ Unsupported architecture: $ARCH"; exit 1 ;;
esac

ASSET="${BINARY}-${OS}-${ARCH}"
echo "🧠 Think Better Installer"
echo "   Platform: ${OS}/${ARCH}"

# --- Get latest release URL ---
LATEST_URL="https://github.com/${REPO}/releases/latest/download/${ASSET}"
echo "   Downloading: ${LATEST_URL}"

# --- Download ---
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

if command -v curl &>/dev/null; then
  curl -fsSL "$LATEST_URL" -o "${TMP_DIR}/${BINARY}"
elif command -v wget &>/dev/null; then
  wget -qO "${TMP_DIR}/${BINARY}" "$LATEST_URL"
else
  echo "❌ Neither curl nor wget found. Please install one."
  exit 1
fi

# --- Install ---
mkdir -p "$INSTALL_DIR"
mv "${TMP_DIR}/${BINARY}" "${INSTALL_DIR}/${BINARY}"
chmod +x "${INSTALL_DIR}/${BINARY}"

echo "✅ Installed to ${INSTALL_DIR}/${BINARY}"

# --- Check PATH ---
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$INSTALL_DIR"; then
  echo ""
  echo "⚠️  ${INSTALL_DIR} is not in your PATH. Add it:"
  echo ""
  echo "   echo 'export PATH=\"${INSTALL_DIR}:\$PATH\"' >> ~/.bashrc"
  echo "   source ~/.bashrc"
  echo ""
fi

# --- Verify ---
if command -v "$BINARY" &>/dev/null; then
  echo ""
  "$BINARY" version
  echo ""
  echo "🚀 Ready! Run: think-better init --ai claude"
fi
