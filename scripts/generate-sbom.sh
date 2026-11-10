#!/usr/bin/env bash
# Generate the input SBOM for SilkBomb from a Python project.
#
# Shared by both CI systems, which is why it sits here and not under
# evergreen/: the Evergreen generate_sbom function calls it, and so does the
# python/generate-sbom action. SilkBomb consumes the file this writes; it does
# not produce it.
#
# cyclonedx-py reads one project type per subcommand, and the default,
# requirements, reads requirements.txt from the working directory. A project
# that declares its dependencies in pyproject.toml has no such file, and the
# run then fails with "Could not open requirements file". Name the project type
# rather than assume one.
#
# Dev dependencies do not ship, so they do not belong in the SBOM. With
# requirements, point SBOM_SOURCE_ARG at the pinned release requirements.
#
# Optional environment:
#   SBOM_SOURCE      cyclonedx-py subcommand: requirements, poetry, pipenv, or
#                    environment. Default requirements.
#   SBOM_SOURCE_ARG  Positional argument for that subcommand: a requirements
#                    file, a project directory for poetry and pipenv, an
#                    interpreter for environment. Each subcommand has its own
#                    default, so this may stay empty.
#   SBOM_OUT         File to write. Default sbom.json.
#   PYTHON           Interpreter that installs cyclonedx-py. Default python3.
#   CYCLONEDX_VERSION  Version of cyclonedx-py to install. Default: whatever
#                    pip resolves.
set -euo pipefail

SBOM_SOURCE="${SBOM_SOURCE:-requirements}"
SBOM_SOURCE_ARG="${SBOM_SOURCE_ARG:-}"
SBOM_OUT="${SBOM_OUT:-sbom.json}"
PYTHON="${PYTHON:-python3}"
CYCLONEDX_VERSION="${CYCLONEDX_VERSION:-}"

# An unknown subcommand is rejected here, where the message names the four that
# work. cyclonedx-py exits 2 with an argparse usage dump instead.
case "$SBOM_SOURCE" in
    requirements | poetry | pipenv | environment) ;;
    *)
        echo "generate-sbom: unknown SBOM_SOURCE: $SBOM_SOURCE" >&2
        echo "generate-sbom: expected requirements, poetry, pipenv, or environment" >&2
        exit 1
        ;;
esac

# An installed cyclonedx-py is left alone, so a project that pins the tool in
# its own environment keeps that version.
if ! command -v cyclonedx-py >/dev/null 2>&1; then
    if [ -n "$CYCLONEDX_VERSION" ]; then
        "$PYTHON" -m pip install "cyclonedx-py==$CYCLONEDX_VERSION"
    else
        "$PYTHON" -m pip install cyclonedx-py
    fi
fi

# The positional argument is omitted when it is empty. Passing "" would be read
# as a path of that name, rather than as the subcommand's own default.
if [ -n "$SBOM_SOURCE_ARG" ]; then
    cyclonedx-py "$SBOM_SOURCE" --of json -o "$SBOM_OUT" "$SBOM_SOURCE_ARG"
else
    cyclonedx-py "$SBOM_SOURCE" --of json -o "$SBOM_OUT"
fi

# cyclonedx-py creates the output file before it reads the project, so a failed
# run leaves a zero-byte file behind. A later step must not find that and take
# it for an SBOM. A library with no dependencies is a different case: its SBOM
# is near-empty but still a document, so it has a size.
if [ ! -s "$SBOM_OUT" ]; then
    echo "generate-sbom: no SBOM written to $SBOM_OUT" >&2
    exit 1
fi
