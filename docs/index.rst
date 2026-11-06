abx-release-tools
=================

Shared release tooling for ABX (AI Builder Experience) integrations:
``mongodb/strands-mongodb``,
``mongodb-developer/ms-agent-framework-mongodb``, and
``mongodb-developer/claude-agent-sdk-mongodb-session-store``.

The tooling covers the four secure-release steps every ABX release
needs, plus the setup action that precedes them:

.. toctree::
   :maxdepth: 2

   Setup <setup>
   Dependency scanning with SilkBomb <scanning>
   Artifact signing with Garasign <signing>
   Artifact tracing: Papertrail or the authorized-publication report <tracing>
   Trusted publishing to PyPI <publishing>

Verification
------------

Every GitHub Action in this repo is extracted unchanged from
`drivers-github-tools <https://github.com/mongodb-labs/drivers-github-tools>`_
at commit ``99b1cbd``, the same commit `pymongo's release
<https://github.com/mongodb/mongo-python-driver/blob/main/.github/workflows/release-python.yml>`_
pins and runs in production.

The Evergreen templates follow public, working Evergreen release
pipelines. Each template cites its source.

Pin every action to a commit SHA in real workflows.
