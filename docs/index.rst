abx-release-tools
=================

Shared release tooling for ABX (AI Builder Experience) integrations:
``mongodb/strands-mongodb``,
``mongodb-developer/ms-agent-framework-mongodb``, and
``mongodb-developer/claude-agent-sdk-mongodb-session-store``.

The tooling covers the four secure-release steps every ABX release
needs:

1. Dependency scanning (SilkBomb / Kondukto).
2. Artifact signing (Garasign).
3. Artifact tracing (Papertrail).
4. PyPI trusted publishing.

.. toctree::
   :maxdepth: 2

   setup
   scanning
   signing
   tracing
   publishing

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
