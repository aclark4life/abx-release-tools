"""The defect this repository shipped with, and the two I introduced while fixing it.

Upstream iterated the file list as ``for filename in ${{ inputs.filenames }}``. That splits on
whitespace, so ``my package.tar.gz`` became ``my`` and ``package.tar.gz``, neither of which
exists. Nothing was signed for it, and the step exited 0 -- a release that looks signed.

Fixing it took three attempts. The first still split each line on spaces. The second globbed with
an unquoted ``$pattern``, which word-splits before it expands. Both passed review by eye. Neither
survived a file with a space in its name, which is why that file is the fixture here.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import run_step

SPACED = "my package.tar.gz"


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    work = tmp_path / "work"
    work.mkdir()
    (work / "pkg-1.0-py3-none-any.whl").write_bytes(b"wheel")
    (work / SPACED).write_bytes(b"sdist")
    return work


@pytest.fixture
def release_env(tmp_path: Path) -> dict[str, str]:
    """What the setup action exports, which every other action expects to find."""
    (tmp_path / "release-assets").mkdir()
    (tmp_path / "s3-assets").mkdir()
    envfile = tmp_path / "garasign-envfile"
    envfile.write_text(
        "GRS_CONFIG_USER1_USERNAME=user\nGRS_CONFIG_USER1_PASSWORD=pass\n"
    )
    return {
        "GARASIGN_ENVFILE": str(envfile),
        "GPG_KEY_ID": "DEADBEEFCAFE",
        "RELEASE_ASSETS": str(tmp_path / "release-assets"),
        "S3_ASSETS": str(tmp_path / "s3-assets"),
        "AWS_BUCKET": "release-assets-bucket",
        "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.txt"),
    }


class TestSigning:
    def test_a_name_containing_a_space_is_signed_under_that_name(
        self, workspace: Path, release_env: dict[str, str], tmp_path: Path
    ) -> None:
        """One pattern per line, which is the only form that can express such a name."""
        result = run_step(
            "gpg-sign",
            inputs={"filenames": f"*.whl\n{SPACED}"},
            env=release_env,
            cwd=workspace,
        )

        assert result.returncode == 0, result.stderr
        signatures = sorted(p.name for p in (tmp_path / "release-assets").iterdir())
        assert signatures == [f"{SPACED}.sig", "pkg-1.0-py3-none-any.whl.sig"]

    def test_the_key_id_reaches_the_container(
        self, workspace: Path, release_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Half of the --local-user fix. The other half is gpg's, and needs a real container."""
        run_step(
            "gpg-sign",
            inputs={"filenames": f"{SPACED}\n"},
            env=release_env,
            cwd=workspace,
        )

        signature = (tmp_path / "release-assets" / f"{SPACED}.sig").read_text()
        assert "key=DEADBEEFCAFE" in signature

    def test_a_pattern_matching_nothing_fails(
        self, workspace: Path, release_env: dict[str, str]
    ) -> None:
        """Signing fewer files than asked for, quietly, is how an unsigned artifact ships."""
        result = run_step(
            "gpg-sign",
            inputs={"filenames": "dist/*.whl"},
            env=release_env,
            cwd=workspace,
        )

        assert result.returncode != 0
        assert "no file matches" in result.stdout + result.stderr

    def test_a_space_separated_list_still_works(
        self, workspace: Path, release_env: dict[str, str], tmp_path: Path
    ) -> None:
        """The upstream calling convention, which callers already written depend on."""
        result = run_step(
            "gpg-sign",
            inputs={"filenames": "pkg-1.0-py3-none-any.whl *.whl"},
            env=release_env,
            cwd=workspace,
        )

        assert result.returncode == 0, result.stderr
        assert (tmp_path / "release-assets" / "pkg-1.0-py3-none-any.whl.sig").exists()

    def test_a_signature_that_was_not_produced_is_caught(
        self, workspace: Path, release_env: dict[str, str]
    ) -> None:
        """A container that exits 0 having written nothing must not pass for a signed release."""
        result = run_step(
            "gpg-sign",
            inputs={"filenames": f"{SPACED}\n"},
            env={**release_env, "STUB_DOCKER_FAIL": "0"},
            cwd=workspace,
        )

        assert result.returncode != 0
        assert "no signature was produced" in result.stdout + result.stderr


class TestTheAuthorizedPublicationReport:
    def test_it_lists_a_name_containing_a_space(
        self, workspace: Path, release_env: dict[str, str], tmp_path: Path
    ) -> None:
        result = run_step(
            "authorized-pub",
            inputs={
                "product_name": "strands-mongodb",
                "release_version": "0.1.0rc1",
                "filenames": f"*.whl\n{SPACED}",
            },
            env=release_env,
            cwd=workspace,
        )

        assert result.returncode == 0, result.stderr
        report = (tmp_path / "s3-assets" / "authorized-publication.txt").read_text()
        assert f"Filename: {SPACED}" in report
        # sha256 of b"sdist", so the digest is the file's and not something's default.
        assert "Shasum: " in report
        assert report.index("Filename: my package.tar.gz") < report.index(
            "Filename: pkg-1.0-py3-none-any.whl"
        ), "the file list is sorted, so two runs over the same artifacts agree"

    def test_it_falls_back_to_the_login_when_the_name_lookup_fails(
        self, workspace: Path, release_env: dict[str, str], tmp_path: Path
    ) -> None:
        """The login is the identity that matters; a courtesy lookup must not take the report down."""
        result = run_step(
            "authorized-pub",
            inputs={
                "product_name": "strands-mongodb",
                "release_version": "0.1.0rc1",
                "filenames": f"{SPACED}\n",
            },
            env={**release_env, "STUB_GH_FAIL": "1"},
            cwd=workspace,
        )

        assert result.returncode == 0, result.stderr
        assert (
            "Releaser: test-actor"
            in (tmp_path / "s3-assets" / "authorized-publication.txt").read_text()
        )

    def test_no_artifacts_is_said_rather_than_left_blank(
        self, workspace: Path, release_env: dict[str, str], tmp_path: Path
    ) -> None:
        result = run_step(
            "authorized-pub",
            inputs={"product_name": "p", "release_version": "1", "filenames": ""},
            env=release_env,
            cwd=workspace,
        )

        assert result.returncode == 0, result.stderr
        assert (
            "No published artifacts."
            in (tmp_path / "s3-assets" / "authorized-publication.txt").read_text()
        )


class TestTheS3Upload:
    def test_it_uploads_a_name_containing_a_space(
        self, release_env: dict[str, str], tmp_path: Path
    ) -> None:
        (tmp_path / "s3-assets" / SPACED).write_bytes(b"asset")
        log = tmp_path / "aws.log"

        result = run_step(
            "upload-s3-assets",
            inputs={
                "version": "0.1.0rc1",
                "product_name": "strands-mongodb",
                "filenames": "*",
            },
            env={**release_env, "STUB_AWS_LOG": str(log)},
            cwd=tmp_path,
        )

        assert result.returncode == 0, result.stderr
        assert log.read_text().strip() == (
            f"s3 cp ./{SPACED} s3://release-assets-bucket/strands-mongodb/0.1.0rc1/{SPACED}"
        )

    def test_a_pattern_matching_nothing_fails(
        self, release_env: dict[str, str], tmp_path: Path
    ) -> None:
        """An upload step that uploads nothing and exits 0 is the failure it exists to catch."""
        result = run_step(
            "upload-s3-assets",
            inputs={"version": "1", "product_name": "p", "filenames": "*.sbom.json"},
            env=release_env,
            cwd=tmp_path,
        )

        assert result.returncode != 0
        assert "no file matches" in result.stdout + result.stderr

    def test_an_unset_bucket_is_named_rather_than_expanded(
        self, release_env: dict[str, str], tmp_path: Path
    ) -> None:
        """Upstream expanded an unset bucket into s3:///product/version/file, once per file."""
        (tmp_path / "s3-assets" / "report.txt").write_bytes(b"x")

        result = run_step(
            "upload-s3-assets",
            inputs={"version": "1", "product_name": "p"},
            env={**release_env, "AWS_BUCKET": ""},
            cwd=tmp_path,
        )

        assert result.returncode != 0
        assert "AWS_BUCKET" in result.stdout + result.stderr

    def test_a_dry_run_uploads_nothing(
        self, release_env: dict[str, str], tmp_path: Path
    ) -> None:
        (tmp_path / "s3-assets" / "report.txt").write_bytes(b"x")
        log = tmp_path / "aws.log"

        result = run_step(
            "upload-s3-assets",
            inputs={"version": "1", "product_name": "p", "dry_run": "true"},
            env={**release_env, "STUB_AWS_LOG": str(log)},
            cwd=tmp_path,
        )

        assert result.returncode == 0, result.stderr
        assert not log.exists(), "a dry run called aws"
        assert "Would upload report.txt" in result.stdout
