Artifact signing
================

GitHub Actions: ``gpg-sign``
----------------------------

Signs release artifacts with the Garasign GPG container and moves the
detached ``.sig`` files to ``RELEASE_ASSETS``. Run ``setup`` first.

The ``filenames`` input contract, shared by every action that takes a
file list: entries may be **space- or newline-separated**, and each may
be a glob. A pattern that matches nothing fails the step; a file
matched by two patterns is handled once.

Usage
-----

.. code-block:: yaml

   - uses: <owner>/abx-release-tools/actions/gpg-sign@<sha>
     with:
       filenames: dist/*

Inputs
------

.. list-table::
   :header-rows: 1

   * - Input
     - Required
     - Description
   * - ``filenames``
     - yes
     - File names to sign. Can be a glob.
   * - ``ecr_registry``, ``ecr_repository``
     - no
     - Garasign container location. Defaults to the DevProd registry.

Pass a glob, never a package's file names. A rename or version bump
then never means editing the workflow.

GitHub Actions: ``git-sign``
----------------------------

Runs arbitrary git commands in a container with the Garasign GPG keys
loaded. Use it to sign release tags.

Usage
-----

.. code-block:: yaml

   - uses: <owner>/abx-release-tools/actions/git-sign@<sha>
     with:
       command: git tag -s -m "Release 1.0.0" v1.0.0

Inputs
------

.. list-table::
   :header-rows: 1

   * - Input
     - Required
     - Description
   * - ``command``
     - yes
     - Git command run inside the container.
   * - ``ecr_registry``, ``ecr_repository``
     - no
     - Garasign container location. Defaults to the DevProd registry.

Evergreen: ``evergreen/sign_artifacts.yml``
-------------------------------------------

Evergreen cannot include YAML from another repo. Copy the file into
the project config.

Hidden project variables needed:

- ``GARASIGN_USERNAME`` — Garasign username (``ai-builder-experience``)
- ``GARASIGN_PASSWORD`` — Garasign password

Task usage:

.. code-block:: yaml

   tasks:
     - name: sign_artifacts
       commands:
         - func: build  # produces dist/
         - func: sign_artifact
           vars:
             unsigned_artifact: dist/abx-1.0.0-py3-none-any.whl
             detached_signature: dist/abx-1.0.0-py3-none-any.whl.sig

Credentials ride the environment, never the script text: Evergreen
prints script text in task logs.

Source: `mongo-rust-driver
<https://github.com/mongodb/mongo-rust-driver/blob/main/.evergreen/release-sign.sh>`_.

Verification
------------

Users check a signature against MongoDB's public key:

.. code-block:: shell

   gpg --verify artifact.whl.sig artifact.whl

The public key lives at
https://pgp.mongodb.com/ai-builder-experience.asc. Publish the location
in the project README. Attach each ``.sig`` file to the GitHub Release
next to the artifact, as pymongo does.
