"""Run a composite action's step the way GitHub Actions would.

The step's script is read out of its ``action.yml`` rather than copied into the test, because a
copy drifts and then the test passes while the action that ships is broken. Everything here exists
to make that extraction faithful:

* ``${{ }}`` expressions are substituted *before* bash sees the script, which is what Actions does
  and what makes an interpolated input a shell injection. The tests rely on that ordering.
* A step's ``env:`` block is rendered from the action's declared input defaults, so a test that
  passes no inputs exercises the same defaults a caller would get.
* ``working-directory`` is honoured, because ``upload-s3-assets`` depends on it.

Stub executables on PATH stand in for docker, gh and aws. They are deliberately crude: their job
is to record what the step handed them, not to behave like the real thing.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
ACTIONS = REPO / "actions"
STUBS = Path(__file__).resolve().parent / "stubs"

EXPRESSION = re.compile(r"\$\{\{\s*(.+?)\s*\}\}")
ACTION_PATH_EXPRESSION = re.compile(r"\$\{\{\s*github\.action_path\s*\}\}")

# github context values a step may read. Fixed so output is reproducible. `action_path` is filled
# in per action by run_step: the runner sets it to the directory of the action being run, and an
# action that reaches a file beside it, or walks up to the repository root, depends on that.
GITHUB_CONTEXT = {
    "actor": "test-actor",
    "run_id": "424242",
    "repository": "mongodb/strands-mongodb",
    "action_path": str(ACTIONS),
}


def action_files() -> list[Path]:
    return sorted(ACTIONS.rglob("action.yml"))


def action_name(path: Path) -> str:
    return path.parent.relative_to(ACTIONS).as_posix()


def load_action(name: str) -> dict:
    return yaml.safe_load((ACTIONS / name / "action.yml").read_text())


def declared_inputs(action: dict) -> dict[str, str]:
    """Input names mapped to their defaults, as a caller supplying nothing would see them."""
    return {
        key: str(spec.get("default", ""))
        for key, spec in (action.get("inputs") or {}).items()
    }


def run_steps(action: dict) -> list[dict]:
    return action["runs"]["steps"]


def resolve(
    text: str,
    inputs: dict[str, str],
    env: dict[str, str],
    github: dict[str, str] | None = None,
) -> str:
    """Substitute ``${{ }}`` the way Actions does: textually, before bash parses anything."""
    github = github or GITHUB_CONTEXT

    def one(match: re.Match[str]) -> str:
        ref = match.group(1)
        context, _, key = ref.partition(".")
        if context == "inputs":
            assert key in inputs, f"{ref!r} is not a declared input"
            return inputs[key]
        if context == "github":
            assert key in github, f"the test harness has no github.{key}"
            return github[key]
        if context == "env":
            return env.get(key, "")
        raise AssertionError(f"the test harness cannot resolve {ref!r}")

    return EXPRESSION.sub(one, text)


def run_step(
    name: str,
    index: int = 0,
    *,
    inputs: dict[str, str] | None = None,
    env: dict[str, str] | None = None,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    """Execute one step of one action, with the stubs on PATH."""
    action = load_action(name)
    step = run_steps(action)[index]

    merged_inputs = declared_inputs(action) | (inputs or {})
    github = {**GITHUB_CONTEXT, "action_path": str(ACTIONS / name)}
    environment = {
        **os.environ,
        **(env or {}),
        "PATH": f"{STUBS}{os.pathsep}{os.environ['PATH']}",
    }
    # The step's own env: block is rendered last, so it can read the inputs.
    for key, value in (step.get("env") or {}).items():
        environment[key] = resolve(str(value), merged_inputs, environment, github)

    # `github.action_path` is the one expression a run: body may hold, because the runner sets it
    # and a caller cannot. It is substituted here so an action can reach the script that ships
    # beside it. Every other expression still makes the harness refuse the body: that an input
    # arrives as syntax rather than as a value is the defect these tests exist for.
    script = ACTION_PATH_EXPRESSION.sub(github["action_path"], str(step["run"]))
    assert "${{" not in script, (
        f"{name} step {index} interpolates an expression into its run: body; "
        f"the harness refuses to run it, see test_no_expression_reaches_a_shell"
    )

    working_directory = step.get("working-directory")
    if working_directory:
        cwd = Path(resolve(str(working_directory), merged_inputs, environment, github))

    return subprocess.run(
        ["bash", "-c", script],
        check=False,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
    )


def shellcheck_path() -> str:
    """The shellcheck binary.

    `shellcheck-py` in tests/requirements.txt installs it next to the running interpreter, so it
    is found there first and only then on PATH. It is a hard requirement rather than a skip: a
    check that quietly skips itself on a machine without shellcheck is not a check.
    """
    here = str(Path(sys.executable).parent)
    found = shutil.which(
        "shellcheck", path=os.pathsep.join([here, os.environ.get("PATH", "")])
    )
    assert found, "shellcheck not found; pip install -r tests/requirements.txt"
    return found
