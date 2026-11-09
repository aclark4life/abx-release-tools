#!/usr/bin/env bash
# Generate the input SBOM for SilkBomb from the pinned release requirements.
#
# Dev dependencies do not ship, so they do not belong in the SBOM.
#
# Optional environment:
#   SBOM_OUT  File to write. Default sbom.json.
#   PYTHON    Interpreter to use. Default python3.
set -euo pipefail

SBOM_OUT="${SBOM_OUT:-sbom.json}"
PYTHON="${PYTHON:-python3}"

"$PYTHON" -m pip install cyclonedx-py
cyclonedx-py requirements --of json -o "$SBOM_OUT"
