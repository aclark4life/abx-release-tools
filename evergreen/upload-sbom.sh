#!/usr/bin/env bash
# Upload an SBOM to Kondukto with SilkBomb.
#
# upload needs no Kondukto token: the silkbomb IAM role's session credentials
# are enough. Assume that role with ec2.assume_role in the project config and
# pass the session credentials in through the environment. Run ecr-login.sh
# first.
#
# The augmented SBOM that ships with a release is a different thing, produced
# on GitHub Actions by the sbom action, which does need the token.
#
# Required environment:
#   KONDUKTO_REPO    Kondukto repository, as org/repo.
#   KONDUKTO_BRANCH  Branch being scanned.
#   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN
#
# Optional environment:
#   SBOM_IN         Input SBOM. Default sbom.json.
#   SILKBOMB_IMAGE  Container image. Defaults to the DevProd registry.
#   CONTAINER_CMD   docker or podman. Default docker.
set -euo pipefail

: "${KONDUKTO_REPO:?is required}"
: "${KONDUKTO_BRANCH:?is required}"

SBOM_IN="${SBOM_IN:-sbom.json}"
SILKBOMB_IMAGE="${SILKBOMB_IMAGE:-901841024863.dkr.ecr.us-east-1.amazonaws.com/release-infrastructure/silkbomb:2.0}"
CONTAINER_CMD="${CONTAINER_CMD:-docker}"

if [ ! -f "$SBOM_IN" ]; then
    echo "upload-sbom: no such file: $SBOM_IN" >&2
    exit 1
fi

# The mount path is fixed, so the SBOM is passed by basename under it. An
# unquoted path here asked silkbomb for two files when the path held a space.
sbom_dir="$(cd "$(dirname "$SBOM_IN")" && pwd)"
sbom_name="$(basename "$SBOM_IN")"

"$CONTAINER_CMD" run --rm \
    -v "$sbom_dir:/pwd" \
    --user "$(id -u):$(id -g)" \
    --env AWS_ACCESS_KEY_ID \
    --env AWS_SECRET_ACCESS_KEY \
    --env AWS_SESSION_TOKEN \
    "$SILKBOMB_IMAGE" \
    upload \
    --repo "$KONDUKTO_REPO" \
    --branch "$KONDUKTO_BRANCH" \
    --sbom-in "/pwd/$sbom_name"
