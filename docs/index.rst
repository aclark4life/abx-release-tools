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

Provenance and the verification trail live in the repo README. Pin
every action to a commit SHA in real workflows.
