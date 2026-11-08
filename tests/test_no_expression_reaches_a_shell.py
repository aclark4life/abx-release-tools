"""Static checks over every action, needing neither docker nor a network.

These encode the defect class that the extracted actions shipped with: an input interpolated into
a ``run:`` body. ``${{ }}`` is substituted before bash parses the script, so an input containing a
quote does not arrive as a string -- it arrives as syntax. Reviewing for it by eye is exactly the
sort of thing that passes review and then does not.
"""

from __future__ import annotations

import re

import pytest

from conftest import (
    EXPRESSION,
    action_files,
    action_name,
    declared_inputs,
    run_steps,
)
import yaml

# The only expressions allowed to reach a shell. `github.action_path` is set by the runner and is
# not caller-controlled; it is how a composite action finds the script that ships beside it.
SAFE_IN_A_RUN_BODY = frozenset({"github.action_path"})

ACTIONS = [pytest.param(path, id=action_name(path)) for path in action_files()]


@pytest.fixture(params=ACTIONS)
def action(request):
    path = request.param
    return action_name(path), yaml.safe_load(path.read_text())


def test_no_expression_reaches_a_shell(action) -> None:
    """No step interpolates an expression into the script it runs.

    An input reaches a step through ``env:`` instead, where it is a value rather than syntax.
    """
    name, document = action
    for index, step in enumerate(run_steps(document)):
        script = step.get("run")
        if script is None:
            continue
        found = {match.strip() for match in EXPRESSION.findall(str(script))}
        offending = sorted(found - SAFE_IN_A_RUN_BODY)
        assert not offending, (
            f"{name} step {index} interpolates {offending} into its run: body; pass it through "
            f"env: instead, because ${{{{ }}}} is substituted before bash parses the script"
        )


def test_every_expression_names_a_declared_input(action) -> None:
    """A typo in ``${{ inputs.filename }}`` is not an error at any point: it expands to nothing.

    The step then runs with an empty value and, before the guards added alongside these tests,
    did so silently.
    """
    name, document = action
    inputs = declared_inputs(document)
    for index, step in enumerate(run_steps(document)):
        for match in EXPRESSION.findall(yaml.safe_dump(step)):
            context, _, key = match.strip().partition(".")
            if context != "inputs":
                continue
            assert key in inputs, (
                f"{name} step {index} reads inputs.{key}, which the action does not declare; "
                f"it would expand to the empty string"
            )


def test_every_script_stops_at_the_first_failure(action) -> None:
    """Without ``set -e`` a failing line is a line the step carries on past.

    For a signing or uploading step that means reporting success over a partial result, which is
    the failure mode every guard in these actions exists to prevent.
    """
    name, document = action
    for index, step in enumerate(run_steps(document)):
        script = step.get("run")
        if script is None or "\n" not in str(script).strip():
            continue  # A one-line run: fails on its own exit status.
        assert re.search(r"^\s*set -euo pipefail\s*$", str(script), re.MULTILINE), (
            f"{name} step {index} runs a multi-line script without `set -euo pipefail`"
        )


def test_every_script_declares_bash(action) -> None:
    """A composite action has no default shell; omitting it is an error at run time, not at lint."""
    name, document = action
    for index, step in enumerate(run_steps(document)):
        if step.get("run") is None:
            continue
        assert step.get("shell") == "bash", (
            f"{name} step {index} has a run: but no `shell: bash`"
        )
