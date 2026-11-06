# abx-release-tools

Shared release tooling for ABX (AI Builder Experience) integrations:
`mongodb/strands-mongodb`, `mongodb-developer/ms-agent-framework-mongodb`,
`mongodb-developer/claude-agent-sdk-mongodb-session-store`, and new
integrations that join that list.

POC. Covers the four steps of the ABX release how-to guides; the
[documentation](docs/index.rst) has the details:

- [Dependency scanning with SilkBomb](docs/scanning.rst)
- [Artifact signing with Garasign](docs/signing.rst)
- [Artifact tracing: Papertrail or the authorized-publication
  report](docs/tracing.rst)
- [Trusted publishing to PyPI](docs/publishing.rst)

## Documentation

Sphinx docs with the Furo theme, under `docs/`:

```
python -m pip install -r docs/requirements.txt
sphinx-build -b html docs docs/_build/html
```

Read the Docs builds the docs from `.readthedocs.yaml`. Update that
file when the repo moves or renames.

## Layout

- `actions/` — GitHub Actions composite actions, consumed with `uses:`.
- `evergreen/` — Evergreen function and task templates. Evergreen cannot
  include YAML from another repo. Copy them into the project config.

## Usage

```
uses: <owner>/abx-release-tools/actions/setup@main
uses: <owner>/abx-release-tools/actions/sbom@main
uses: <owner>/abx-release-tools/actions/gpg-sign@main
uses: <owner>/abx-release-tools/actions/git-sign@main
uses: <owner>/abx-release-tools/actions/authorized-pub@main
uses: <owner>/abx-release-tools/actions/upload-s3-assets@main
uses: <owner>/abx-release-tools/actions/python/publish@main
```

Pin to a commit SHA in real workflows.

The `python/publish` action needs `permissions: id-token: write` on the
publish job. PyPI trusted publishing exchanges the GitHub OIDC token for the
upload; without the permission the publish step fails.

The `sbom`, `gpg-sign`, `git-sign`, `authorized-pub`, and `upload-s3-assets`
actions expect the environment set up by the `setup` action (`RELEASE_ASSETS`,
`S3_ASSETS`, `GARASIGN_ENVFILE`, `KONDUKTO_ENVFILE`, `AWS_BUCKET`). Run
`setup` first.

Guide 3's GitHub Actions tracing alternative uses `authorized-pub` to write
`authorized-publication.txt`, then `upload-s3-assets` to put it in the release
S3 bucket. Run the two actions in that order: there is no `python/post-publish`
release chain here (see Out of scope). Agree the bucket with DevProd Release
Infrastructure.

## Per-repo onboarding

Four steps sit outside this repo, done once per repo. The ABX release how-to
guides have the details:
<https://docs.google.com/document/d/1rhYkWgbasperhG_9m5enMLamVkM0Nm5E7XuZ9lixxLI/edit>.

1. File the Kondukto RNDSEC onboarding ticket.
2. Request the Kondukto CI API token and store it as a CI secret.
3. Agree the Papertrail product name with DevProd Release Infrastructure.
4. Register the PyPI pending publisher for each new package.

## Provenance

The GitHub Actions are extracted unchanged from
[mongodb-labs/drivers-github-tools](https://github.com/mongodb-labs/drivers-github-tools)
at commit `99b1cbd729bc83bf7fc74e1b2a97fffad3d65d7b`. Each file carries a
provenance comment. Do not change semantics silently: keep names and inputs
aligned with upstream so fixes are easy to cherry-pick.

Every extracted action runs in production in pymongo's release workflow
([release-python.yml](https://github.com/mongodb/mongo-python-driver/blob/main/.github/workflows/release-python.yml)),
which pins the same commit: `setup` and `gpg-sign` in the post-publish chain,
`authorized-pub` and `sbom` through `full-report`, `upload-s3-assets` in
post-publish, and `git-sign` through pre-publish's `tag-version`.

The Evergreen templates follow public, working Evergreen release pipelines.
Each file cites its source:

- `evergreen/sign_artifacts.yml` — mongodb/mongo-rust-driver
  (`.evergreen/releases.yml`, `.evergreen/release-sign.sh`).
- `evergreen/silkbomb.yml` — mongodb/mongo-csharp-driver
  (`evergreen/evergreen.yml`, `evergreen/upload-sbom.sh`). `upload` only; the
  augmented SBOM that ships with a release comes from the GitHub Actions
  `sbom` action.
- `evergreen/papertrail.yml` — mongodb/mongo-java-driver (`.evergreen/.evg.yml`)
  and mongodb/mongo-rust-driver (`.evergreen/releases.yml`).

## Out of scope (deliberately)

The drivers-github-tools release pipeline around `python/post-publish`
(`full-report`, `bump-version`, `tag-version`, `compliance-report`) is not
extracted. ABX repos do not use the Evergreen +
S3 release pipeline those actions assume. ABX repos never use
drivers-github-tools directly: when a repo needs one of those actions, extract
it from drivers-github-tools into this repo first, then use it from here.

## Maintenance rules

- This repo is ABX-owned. ABX re-pins action SHAs, fixes lint findings, and
  adapts when DevProd changes SilkBomb, Garasign, or Papertrail interfaces.
- Generic fixes go upstream to drivers-github-tools too, so drift stays
  visible instead of silent.
- Run `pre-commit run --all-files` before committing.

## TODO before this leaves POC

- [ ] Move the repo to mongodb-labs. Composite actions in a private personal
      repo cannot be used by org repositories; mongodb-labs makes the repo
      public and consumable. Update the README owner placeholders when the
      move lands.
