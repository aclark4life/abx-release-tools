#!/usr/bin/env bash
# Sign one artifact with Garasign, writing a detached, armored signature.
#
# Run ecr-login.sh first.
#
# Evergreen prints script text in task logs, so the credentials arrive in the
# environment and are never named on a command line.
#
# Required environment:
#   GARASIGN_USERNAME   Garasign username.
#   GARASIGN_PASSWORD   Garasign password.
#   GPG_KEY_ID          Key to sign with.
#   UNSIGNED_ARTIFACT   File to sign.
#   DETACHED_SIGNATURE  Signature file to write.
#
# Optional environment:
#   GARASIGN_IMAGE  Container image. Defaults to the DevProd registry.
#   CONTAINER_CMD   docker or podman. Default docker.
set -euo pipefail

: "${GARASIGN_USERNAME:?is required}"
: "${GARASIGN_PASSWORD:?is required}"
: "${GPG_KEY_ID:?is required}"
: "${UNSIGNED_ARTIFACT:?is required}"
: "${DETACHED_SIGNATURE:?is required}"

GARASIGN_IMAGE="${GARASIGN_IMAGE:-901841024863.dkr.ecr.us-east-1.amazonaws.com/release-infrastructure/garasign-gpg}"
CONTAINER_CMD="${CONTAINER_CMD:-docker}"

if [ ! -f "$UNSIGNED_ARTIFACT" ]; then
    echo "sign-artifact: no such file: $UNSIGNED_ARTIFACT" >&2
    exit 1
fi

# A container env file is line-oriented, so a newline in a value truncates it
# silently and the run then fails as a Garasign auth error, which is a
# misleading place to look. Reject it here instead.
for var in GARASIGN_USERNAME GARASIGN_PASSWORD; do
    case "${!var}" in
        *$'\n'*)
            echo "sign-artifact: $var contains a newline" >&2
            exit 1
            ;;
    esac
done

umask 077
envfile="$(mktemp "${TMPDIR:-/tmp}/garasign-envfile.XXXXXX")"
trap 'rm -f "$envfile"' EXIT

{
    printf 'GRS_CONFIG_USER1_USERNAME=%s\n' "$GARASIGN_USERNAME"
    printf 'GRS_CONFIG_USER1_PASSWORD=%s\n' "$GARASIGN_PASSWORD"
} >"$envfile"

# --local-user pins the key. A Garasign account holding more than one key
# otherwise signs with whichever gpg picks, and the signature then verifies
# against a key the release notes do not name.
#
# The file names reach the container as positional arguments, not as script
# text, so a name containing a space or a quote stays one name.
workdir="$(pwd)"
# shellcheck disable=SC2016  # $0, $1 and $2 are for the container's shell to
# expand from the positional arguments below, not for this one. Expanding them
# here is the defect this avoids.
"$CONTAINER_CMD" run \
    --env-file="$envfile" \
    --rm \
    -v "$workdir:$workdir" \
    -w "$workdir" \
    "$GARASIGN_IMAGE" \
    /bin/bash -c \
    'gpgloader && gpg --yes -v --armor --local-user "$0" -o "$1" --detach-sign "$2"' \
    "$GPG_KEY_ID" "$DETACHED_SIGNATURE" "$UNSIGNED_ARTIFACT"

if [ ! -f "$DETACHED_SIGNATURE" ]; then
    echo "sign-artifact: the container produced no signature at $DETACHED_SIGNATURE" >&2
    exit 1
fi
