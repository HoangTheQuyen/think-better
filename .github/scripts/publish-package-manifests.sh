#!/bin/sh
# Commits the Homebrew formula and the Scoop manifest that GoReleaser wrote to
# dist/ (`brews` / `scoops` with skip_upload: true in .goreleaser.yaml) to the
# main branch, which doubles as the Homebrew tap (Formula/) and the Scoop
# bucket (bucket/). Run by the Release workflow after the release assets are
# uploaded and attested, just before the release is published.
#
# Commits go through the GitHub contents API, as GoReleaser's own upload did,
# so main having moved on since the tagged commit does not matter. A file
# that is already up to date is left alone, so re-running is safe.
#
# Usage: .github/scripts/publish-package-manifests.sh <tag>
# Needs GH_TOKEN (contents: write) and GITHUB_REPOSITORY; BRANCH defaults to main.
set -eu

tag="$1"
repo="${GITHUB_REPOSITORY:?GITHUB_REPOSITORY is not set}"
branch="${BRANCH:-main}"

# publish <file in dist/> <path in the repository> <commit message>
publish() {
  src="$1" dest="$2" message="$3"
  if [ ! -s "$src" ]; then
    echo "::error::$src is missing; GoReleaser should have written it"
    exit 1
  fi

  # Blob SHA of the file on the branch ("" when it does not exist yet).
  if ! sha="$(gh api "repos/$repo/contents/$dest?ref=$branch" --jq .sha 2>/dev/null)"; then
    sha=""
  fi
  if [ -n "$sha" ] && [ "$sha" = "$(git hash-object "$src")" ]; then
    echo "$dest is already up to date on $branch"
    return 0
  fi

  set -- --method PUT "repos/$repo/contents/$dest" \
    -f message="$message" \
    -f branch="$branch" \
    -f content="$(base64 < "$src" | tr -d '\n')" \
    -f "committer[name]=github-actions[bot]" \
    -f "committer[email]=41898282+github-actions[bot]@users.noreply.github.com"
  if [ -n "$sha" ]; then
    set -- "$@" -f sha="$sha"
  fi
  gh api "$@" --jq '"Committed \(.content.path) to '"$branch"' in \(.commit.sha)"'
}

# Same commit messages as GoReleaser used; the changelog filters them out.
publish dist/homebrew/Formula/think-better.rb Formula/think-better.rb "chore(brew): update formula to $tag"
publish dist/scoop/bucket/think-better.json bucket/think-better.json "chore(scoop): update manifest to $tag"
