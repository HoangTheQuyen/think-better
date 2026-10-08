#!/bin/sh
# Upgrade path test: installs every skill with an older think-better release,
# for each target (in a project, and with --global where supported), then
# updates with the new binary and checks that
#   - update leaves no <file>.new / <file>.bak behind (nothing the user did
#     not edit is treated as modified),
#   - check --strict passes (nothing missing, modified or outdated),
#   - uninstall removes every file.
#
# Usage: .github/scripts/upgrade-test.sh <old-binary> <new-binary>
# The real home directory is never touched: HOME points at a temp directory.
set -eu

old="$1"
new="$2"
work="$(mktemp -d)"
HOME="$work/home"
USERPROFILE="$HOME"
export HOME USERPROFILE
mkdir -p "$HOME"

fail() {
  echo "::error::$*"
  exit 1
}

echo "Upgrading from $("$old" version) to $("$new" version)"
skills="$("$new" list --json | jq -r '.skills[].name')"
[ -n "$skills" ] || fail "no skills listed"

# check_upgrade <label> <dir to inspect> <scope flag or "">
check_upgrade() {
  label="$1" dir="$2" scope="$3"
  # shellcheck disable=SC2086 # $scope is empty or a single flag
  "$new" update $scope
  leftovers="$(find "$dir" -name '*.new' -o -name '*.bak' -o -name '*.bak.*')"
  [ -z "$leftovers" ] || fail "$label: update kept files as modified: $leftovers"
  "$new" check --strict || fail "$label: check --strict failed after update"
  for skill in $skills; do
    # shellcheck disable=SC2086
    "$new" uninstall --ai "$ai" --skill "$skill" --force $scope
  done
  remaining="$(find "$dir" -type f)"
  [ -z "$remaining" ] || fail "$label: uninstall left files behind: $remaining"
}

for ai in claude copilot antigravity opencode; do
  echo "::group::$ai (project)"
  project="$work/project-$ai"
  mkdir -p "$project"
  cd "$project"
  "$old" init --ai "$ai" >/dev/null
  check_upgrade "$ai" "$project" ""
  echo "::endgroup::"

  [ "$ai" = copilot ] && continue # no --global for copilot
  echo "::group::$ai (--global)"
  mkdir -p "$work/elsewhere"
  cd "$work/elsewhere"
  "$old" init --ai "$ai" --global >/dev/null
  check_upgrade "$ai --global" "$HOME" "--global"
  echo "::endgroup::"
done
echo "Upgrade from $("$old" version) OK"
