Dependency scanning
===================

Two ways to run SilkBomb on GitHub Actions. Choose by what the repo
needs:

- Scan-only CI, no AWS release infrastructure: run the container
  inline, with ``KONDUKTO_TOKEN`` from a GitHub Actions secret. Source:
  `mongodb-mcp-server
  <https://github.com/mongodb-js/mongodb-mcp-server/pull/1356>`_.
- A repo that also releases: use :doc:`setup` and the ``sbom`` action.
  The repo needs ``setup`` anyway for signing and S3 upload; the
  Kondukto token then lives in the AWS secret.

GitHub Actions: ``sbom``
------------------------

The ``sbom`` action generates an SBOM with SilkBomb, then augments it.
It writes ``cyclonedx.sbom.json`` to both ``RELEASE_ASSETS`` and
``S3_ASSETS``. Run ``setup`` first.

Usage
-----

.. code-block:: yaml

   - uses: <owner>/abx-release-tools/actions/sbom@<sha>
     with:
       kondukto_sub_project: main

Inputs
------

.. list-table::
   :header-rows: 1

   * - Input
     - Required
     - Description
   * - ``sbom_in_path``
     - no
     - Input SBOM. Default ``sbom.json``.
   * - ``sbom_file_name``
     - no
     - Output SBOM name. Default ``cyclonedx.sbom.json``.
   * - ``kondukto_sub_project``
     - no
     - Kondukto sub-project, appended to the branch name.
   * - ``ecr_registry``, ``ecr_repository``
     - no
     - SilkBomb container location. Defaults to the DevProd registry.

Generate the input SBOM first with an ecosystem-native tool. For
Python, use ``cyclonedx-py`` against the pinned release requirements,
not dev dependencies:

.. code-block:: shell

   pip install cyclonedx-py
   cyclonedx-py requirements --of json -o sbom.json

The augment step needs the Kondukto token, so the AWS secret must
contain ``KONDUKTO_TOKEN``. See :doc:`setup`.

Evergreen: ``evergreen/silkbomb.yml``
-------------------------------------

Evergreen cannot include YAML from another repo. Copy the file into
the project config and adapt the ``<TODO>`` values.

Project variables needed:

- ``silkbomb_role_arn`` — ``arn:aws:iam::119629040606:role/silkbomb``
- ``devprod_platforms_ecr_readonly_role_arn`` —
  ``arn:aws:iam::901841024863:role/ecr-role-evergreen-ro``
- ``branch_name`` — the branch being scanned

The template defines one task, ``UPLOAD_SBOM_TO_KONDUKTO``, in an
``ssdlc`` buildvariant. It needs no Kondukto token: the silkbomb IAM
role credentials are enough for ``upload``. The augmented SBOM that
ships with a release is produced on GitHub Actions by the ``sbom``
action.

Source: `mongo-csharp-driver
<https://github.com/mongodb/mongo-csharp-driver/blob/main/evergreen/upload-sbom.sh>`_.
