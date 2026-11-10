"""``scripts/generate-sbom.sh`` builds the SBOM that SilkBomb then uploads.

The script it replaced ran ``cyclonedx-py requirements`` with no argument, which reads
``requirements.txt`` from the working directory. A project that declares its dependencies in
``pyproject.toml`` has no such file, so the step could not work for it at all. These tests pin the
project type down as a parameter, and pin the two ways the step can look like it worked: a
positional argument that word-splits, and a zero-byte output file.

``cyclonedx-py`` is stubbed. Whether it reads a Poetry project correctly is a question about
cyclonedx-py.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from conftest import REPO, STUBS, run_step

SCRIPT = REPO / "scripts" / "generate-sbom.sh"


def generate(cwd: Path, argv_log: Path, **env: str) -> subprocess.CompletedProcess[str]:
    """Run the script with cyclonedx-py stubbed, so no install and no network happen."""
    return subprocess.run(
        ["bash", str(SCRIPT)],
        check=False,
        cwd=cwd,
        env={
            "PATH": f"{STUBS}{os.pathsep}/usr/bin:/bin:/usr/local/bin",
            "STUB_CYCLONEDX_ARGV": str(argv_log),
            **env,
        },
        capture_output=True,
        text=True,
    )


@pytest.fixture
def argv_log(tmp_path: Path) -> Path:
    return tmp_path / "argv"


def test_it_asks_for_a_requirements_sbom_by_default(tmp_path: Path, argv_log) -> None:
    """The default is the old behaviour, so a project with requirements.txt needs no change."""
    result = generate(tmp_path, argv_log)

    assert result.returncode == 0, result.stderr
    assert argv_log.read_text().splitlines() == [
        "requirements",
        "--of",
        "json",
        "-o",
        "sbom.json",
    ]
    assert (tmp_path / "sbom.json").exists()


def test_it_names_the_project_type(tmp_path: Path, argv_log) -> None:
    """A Poetry or pyproject.toml project is the case the old script could not express."""
    result = generate(
        tmp_path,
        argv_log,
        SBOM_SOURCE="poetry",
        SBOM_SOURCE_ARG=str(tmp_path),
        SBOM_OUT="out.json",
    )

    assert result.returncode == 0, result.stderr
    assert argv_log.read_text().splitlines() == [
        "poetry",
        "--of",
        "json",
        "-o",
        "out.json",
        str(tmp_path),
    ]


def test_a_source_path_containing_a_space_stays_one_argument(
    tmp_path: Path, argv_log
) -> None:
    """The defect this repository shipped with, in the one place this script can repeat it."""
    project = tmp_path / "my project"
    project.mkdir()

    result = generate(
        tmp_path, argv_log, SBOM_SOURCE="pipenv", SBOM_SOURCE_ARG=str(project)
    )

    assert result.returncode == 0, result.stderr
    assert argv_log.read_text().splitlines()[-1] == str(project)


def test_an_empty_positional_is_left_out(tmp_path: Path, argv_log) -> None:
    """Passing "" would be read as a path of that name, not as the subcommand's own default."""
    result = generate(tmp_path, argv_log, SBOM_SOURCE_ARG="")

    assert result.returncode == 0, result.stderr
    assert "" not in argv_log.read_text().splitlines()


def test_an_unknown_project_type_is_rejected(tmp_path: Path, argv_log) -> None:
    """Named here, where the message can list the four that work."""
    result = generate(tmp_path, argv_log, SBOM_SOURCE="pdm")

    assert result.returncode == 1
    assert "requirements, poetry, pipenv, or environment" in result.stderr
    assert not argv_log.exists(), "cyclonedx-py ran with a subcommand it does not have"


def test_an_empty_sbom_file_fails_the_step(tmp_path: Path, argv_log) -> None:
    """cyclonedx-py creates the output before it reads the project, so a failed run leaves a
    zero-byte file. A later step must not find that and take it for an SBOM."""
    result = generate(tmp_path, argv_log, STUB_CYCLONEDX_EMPTY="1")

    assert result.returncode == 1
    assert "no SBOM written" in result.stderr


def test_the_action_runs_the_same_script(tmp_path: Path, argv_log) -> None:
    """One copy of the shell, two CI systems. The action reaches it by walking up from
    ``github.action_path``, so this fails if the action moves directory."""
    result = run_step(
        "python/generate-sbom",
        inputs={"sbom_out": "sbom.json"},
        env={"STUB_CYCLONEDX_ARGV": str(argv_log)},
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "sbom.json").exists()
    assert argv_log.read_text().splitlines()[0] == "requirements"
