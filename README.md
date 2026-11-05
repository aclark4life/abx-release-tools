# abx-release-tools

Shared release tooling for ABX (AI Builder Experience) integrations:
`mongodb/strands-mongodb`, `mongodb-developer/ms-agent-framework-mongodb`,
`mongodb-developer/claude-agent-sdk-mongodb-session-store`, and new
integrations that join that list.

POC. Covers the four steps of the ABX release how-to guides:

1. Dependency scanning (SilkBomb / Kondukto).
2. Artifact signing (Garasign).
3. Artifact tracing (Papertrail).
4. PyPI trusted publishing.

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
uses: <owner>/abx-release-tools/actions/python/publish@main
```

Pin to a commit SHA in real workflows.

The `sbom`, `gpg-sign`, `git-sign`, and `authorized-pub` actions expect the
environment set up by the `setup` action (`RELEASE_ASSETS`, `S3_ASSETS`,
`GARASIGN_ENVFILE`, `KONDUKTO_ENVFILE`). Run `setup` first.

## Provenance

The GitHub Actions are extracted unchanged from
[mongodb-labs/drivers-github-tools](https://github.com/mongodb-labs/drivers-github-tools)
at commit `99b1cbd729bc83bf7fc74e1b2a97fffad3d65d7b`. Each file carries a
provenance comment. Do not change semantics silently: keep names and inputs
aligned with upstream so fixes are easy to cherry-pick.

The Evergreen templates are written from the ABX release how-to guides and the
public drivers-github-tools container patterns. The mms `sign_artifacts.yml`
source is private, so `evergreen/sign_artifacts.yml` is a reconstruction.
Verify it against the internal Garasign signing guide before first use.

## Out of scope (deliberately)

The drivers-github-tools release pipeline around `python/post-publish`
(`full-report`, `upload-s3-assets`, `bump-version`, `tag-version`,
`compliance-report`) is not extracted. ABX repos do not use the Evergreen +
S3 release pipeline those actions assume. Add actions from upstream when an
ABX repo needs one.

## Maintenance rules

- This repo is ABX-owned. ABX re-pins action SHAs, fixes lint findings, and
  adapts when DevProd changes SilkBomb, Garasign, or Papertrail interfaces.
- Generic fixes go upstream to drivers-github-tools too, so drift stays
  visible instead of silent.
- Run `pre-commit run --all-files` before committing.

## TODO before this leaves POC

- [ ] Verify `evergreen/sign_artifacts.yml` against the Garasign signing guide.
- [ ] Verify `evergreen/silkbomb.yml` against the SilkBomb onboarding doc.
- [ ] Confirm how `KONDUKTO_TOKEN` is supplied on Evergreen (hidden project
      variable or Secrets Manager via the silkbomb role).
- [ ] Move to an ABX-owned org repo. Composite actions in a private personal
      repo cannot be used by org repositories; the repo must be public or
      internal before ABX repos consume it.
- [ ] Add a license (upstream has none).
