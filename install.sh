#!/bin/sh
# Think Better - one-line installer for macOS / Linux
#
#   curl -fsSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh | sh
#
# Options (environment variables):
#   THINK_BETTER_VERSION    Release to install, e.g. v1.3.0 or 1.3.0 (default: latest)
#   INSTALL_DIR             Where to put the binary (default: $HOME/.local/bin)
#   THINK_BETTER_UNINSTALL  Set to 1 to remove the binary from INSTALL_DIR instead
#
# Uninstall:
#   curl -fsSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh | THINK_BETTER_UNINSTALL=1 sh
#   (or simply: rm "$HOME/.local/bin/think-better")
# Skills already installed in a project are removed with
# `think-better uninstall --skill <name>` (run it before removing the binary).
set -eu

REPO="HoangTheQuyen/think-better"
BINARY="think-better"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"
VERSION="${THINK_BETTER_VERSION:-latest}"

say() { printf '%s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

# --- Uninstall ---
if [ "${THINK_BETTER_UNINSTALL:-}" = "1" ]; then
  if [ -e "${INSTALL_DIR}/${BINARY}" ]; then
    rm -f "${INSTALL_DIR}/${BINARY}"
    say "Removed ${INSTALL_DIR}/${BINARY}"
  else
    say "Nothing to remove: ${INSTALL_DIR}/${BINARY} does not exist"
  fi
  say "If you added ${INSTALL_DIR} to PATH only for think-better, remove that line from your shell profile."
  exit 0
fi

# Accept "1.3.0" as well as "v1.3.0": release tags always start with "v".
case "$VERSION" in
  latest|v*) ;;
  [0-9]*) VERSION="v${VERSION}" ;;
  *) die "Invalid THINK_BETTER_VERSION '${VERSION}' (expected e.g. v1.3.0, 1.3.0 or latest)" ;;
esac

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

say "Think Better Installer"
say "   Platform: ${OS}/${ARCH}"
say "   Version:  ${VERSION}"

# --- Download helpers (HTTPS only, also across redirects) ---
if command -v curl >/dev/null 2>&1; then
  fetch() { curl --proto '=https' --tlsv1.2 -fsSL "$1" -o "$2"; }
elif command -v wget >/dev/null 2>&1; then
  # BusyBox wget has no --https-only; it does not follow redirects to other
  # schemes silently either, and every URL used here is https://.
  if wget --help 2>&1 | grep -q -- '--https-only'; then
    fetch() { wget --https-only -qO "$2" "$1"; }
  else
    fetch() { wget -qO "$2" "$1"; }
  fi
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
    say "Warning: sha256sum/shasum not found - skipping checksum verification"
  elif [ "$expected" != "$actual" ]; then
    die "Checksum mismatch for ${ASSET} (expected ${expected}, got ${actual})"
  else
    say "   Checksum verified: OK"
  fi
else
  say "Warning: checksums.txt not found for this release - skipping verification"
fi

# --- Install ---
mkdir -p "$INSTALL_DIR"
chmod +x "${TMP_DIR}/${BINARY}"
mv "${TMP_DIR}/${BINARY}" "${INSTALL_DIR}/${BINARY}"
say "Installed to ${INSTALL_DIR}/${BINARY}"

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
    say "Note: ${INSTALL_DIR} is not in your PATH. Add it:"
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
say "Ready! In your project directory, run:"
say "   think-better init --ai claude      # or: copilot, antigravity, opencode"
say ""
say "To uninstall: think-better uninstall --skill <name> (per project), then rm ${INSTALL_DIR}/${BINARY}"
