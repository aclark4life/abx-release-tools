#!/usr/bin/env bash
# Write the release version to an Evergreen expansions file, for
# papertrail.trace to read after an expansions.update command.
#
# Optional environment:
#   TAG_PREFIX       Prefix stripped from the git tag. Default v. Set it
#                    empty for a project that tags without one.
#   EXPANSIONS_FILE  File to write. Default trace-expansions.yml.
#   EXPANSION_KEY    Key to write. Default release_version.
set -euo pipefail

# No colon: an empty TAG_PREFIX is a valid choice, not a missing value.
TAG_PREFIX="${TAG_PREFIX-v}"
EXPANSIONS_FILE="${EXPANSIONS_FILE:-trace-expansions.yml}"
EXPANSION_KEY="${EXPANSION_KEY:-release_version}"

tag="$(git describe --tags)"

# Strip the prefix only if it is there. cut -c 2- would eat the first
# character of a tag that carries no prefix.
version="${tag#"$TAG_PREFIX"}"

if [ -z "$version" ]; then
    echo "release-version: git describe --tags gave no version" >&2
    exit 1
fi

printf '%s: "%s"\n' "$EXPANSION_KEY" "$version" >"$EXPANSIONS_FILE"
echo "release-version: $EXPANSION_KEY=$version"
