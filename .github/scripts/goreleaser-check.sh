#!/bin/sh
# Runs `goreleaser check` and fails on any problem except the one deprecation
# we keep on purpose: `brews` (see the comment at the top of .goreleaser.yaml).
# `goreleaser check` exits 1 for an invalid config and 2 for a valid config
# that uses deprecated properties.
#
# Usage: .github/scripts/goreleaser-check.sh   (GORELEASER=/path/to/goreleaser to override)
set -u

GORELEASER="${GORELEASER:-goreleaser}"

out="$(NO_COLOR=1 "$GORELEASER" check 2>&1)"
rc=$?
printf '%s\n' "$out"

if [ "$rc" -eq 2 ]; then
  # Strip ANSI colors (in case NO_COLOR is ignored), then list deprecations other than brews.
  esc="$(printf '\033')"
  others="$(printf '%s\n' "$out" | sed "s/${esc}\[[0-9;]*m//g" | grep 'DEPRECATED:' | grep -Ev 'DEPRECATED:[[:space:]]+brews([[:space:]]|$)')"
  if [ -z "$others" ]; then
    echo "goreleaser check: OK (only the known 'brews' deprecation, kept on purpose)"
    exit 0
  fi
  echo "goreleaser check: unexpected deprecations:" >&2
  printf '%s\n' "$others" >&2
  exit 1
fi

exit "$rc"
