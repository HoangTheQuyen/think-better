#!/bin/sh
# Think Better — one-line installer for macOS / Linux
#
#   curl -fsSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh | sh
#
# Options (environment variables):
#   THINK_BETTER_VERSION  Release tag to install, e.g. v1.0.3 (default: latest)
#   INSTALL_DIR           Where to put the binary (default: $HOME/.local/bin)
set -eu

REPO="HoangTheQuyen/think-better"
BINARY="think-better"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"
VERSION="${THINK_BETTER_VERSION:-latest}"

say() { printf '%s\n' "$*"; }
die() { printf '❌ %s\n' "$*" >&2; exit 1; }

# --- Detect platform ---
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$OS" in
  linux|darwin) ;;
  mingw*|msys*|cygwin*) die "On Windows, use PowerShell: irm https://raw.githubusercontent.com/${REPO}/main/install.ps1 | iex" ;;
  *) die "Unsupported OS: $OS (build from source: https://github.com/${REPO}#install)" ;;
esac

case "$ARCH" in
  x86_64|amd64)  ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *) die "Unsupported architecture: $ARCH" ;;
esac

ASSET="${BINARY}-${OS}-${ARCH}"
if [ "$VERSION" = "latest" ]; then
  BASE_URL="https://github.com/${REPO}/releases/latest/download"
else
  BASE_URL="https://github.com/${REPO}/releases/download/${VERSION}"
fi

say "🧠 Think Better Installer"
say "   Platform: ${OS}/${ARCH}"
say "   Version:  ${VERSION}"

# --- Download helpers ---
if command -v curl >/dev/null 2>&1; then
  fetch() { curl -fsSL "$1" -o "$2"; }
elif command -v wget >/dev/null 2>&1; then
  fetch() { wget -qO "$2" "$1"; }
else
  die "Neither curl nor wget found. Please install one."
fi

sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

say "   Downloading: ${BASE_URL}/${ASSET}"
fetch "${BASE_URL}/${ASSET}" "${TMP_DIR}/${BINARY}" || die "Download failed. Check that release ${VERSION} exists for ${OS}/${ARCH}."

# --- Verify checksum ---
if fetch "${BASE_URL}/checksums.txt" "${TMP_DIR}/checksums.txt" 2>/dev/null; then
  expected="$(awk -v f="$ASSET" '$2 == f || $2 == "*"f {print $1}' "${TMP_DIR}/checksums.txt")"
  actual="$(sha256 "${TMP_DIR}/${BINARY}")"
  if [ -z "$expected" ]; then
    die "No checksum for ${ASSET} in checksums.txt"
  elif [ -z "$actual" ]; then
    say "⚠️  sha256sum/shasum not found — skipping checksum verification"
  elif [ "$expected" != "$actual" ]; then
    die "Checksum mismatch for ${ASSET} (expected ${expected}, got ${actual})"
  else
    say "   Checksum verified ✓"
  fi
else
  say "⚠️  checksums.txt not found for this release — skipping verification"
fi

# --- Install ---
mkdir -p "$INSTALL_DIR"
chmod +x "${TMP_DIR}/${BINARY}"
mv "${TMP_DIR}/${BINARY}" "${INSTALL_DIR}/${BINARY}"
say "✅ Installed to ${INSTALL_DIR}/${BINARY}"

# --- Check PATH ---
case ":${PATH}:" in
  *":${INSTALL_DIR}:"*) ;;
  *)
    case "$(basename "${SHELL:-sh}")" in
      zsh)  rc="$HOME/.zshrc" ;;
      bash) rc="$HOME/.bashrc" ;;
      fish) rc="" ;;
      *)    rc="$HOME/.profile" ;;
    esac
    say ""
    say "⚠️  ${INSTALL_DIR} is not in your PATH. Add it:"
    say ""
    if [ -z "$rc" ]; then
      say "   fish_add_path ${INSTALL_DIR}"
    else
      say "   echo 'export PATH=\"${INSTALL_DIR}:\$PATH\"' >> ${rc} && . ${rc}"
    fi
    say ""
    ;;
esac

say ""
"${INSTALL_DIR}/${BINARY}" version
say ""
say "🚀 Ready! In your project directory, run:"
say "   think-better init --ai claude      # or: copilot, antigravity, opencode"
