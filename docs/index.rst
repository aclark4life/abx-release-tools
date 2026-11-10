abx-release-tools
=================

Shared release tooling for ABX (AI Builder Experience) integrations:
``mongodb/strands-mongodb``,
``mongodb-developer/ms-agent-framework-mongodb``,
``mongodb-developer/claude-agent-sdk-mongodb-session-store``, and new
integrations that join that list.

The tooling covers the four secure-release steps every ABX release
needs, plus the setup action that precedes them:

.. toctree::
   :maxdepth: 2

   Setup <setup>
   Dependency scanning with SilkBomb <scanning>
   Artifact signing with Garasign <signing>
   Artifact tracing: Papertrail or the authorized-publication report <tracing>
   Trusted publishing to PyPI <publishing>

Which CI system can run which step
----------------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 16 16 34

   * - Step
     - Evergreen
     - GitHub Actions
     - Notes
   * - Dependency scanning
     - X
     - X
     - Evergreen uploads the SBOM to Kondukto. The augmented SBOM that
       ships with a release comes from GitHub Actions.
   * - Artifact signing
     - X
     - X
     - Same Garasign container, same GPG key, either way.
   * - Artifact tracing
     - X
     - X
     - Different mechanisms: ``papertrail.trace`` on Evergreen, the
       authorized-publication report on GitHub Actions.
   * - Publishing to PyPI
     -
     - X
     - Trusted publishing needs a GitHub OIDC token, which only a
       GitHub Actions job can present.

A mixed pipeline is normal. A repo that runs its release on Evergreen
still publishes from GitHub Actions, because the last row leaves it no
choice. Releasing on Evergreen means running the other three steps
there, not all four.

Provenance and the verification trail live in the repo README. Pin
every action to a commit SHA in real workflows.
