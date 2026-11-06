Artifact tracing
================

Evergreen: ``evergreen/papertrail.yml``
---------------------------------------

Evergreen cannot include YAML from another repo. Copy the file into
the project config.

Hidden project variables needed:

- ``papertrail_key_id`` — Papertrail Key ID
- ``papertrail_secret_key`` — Papertrail Secret Key

The template's ``trace artifacts`` function reads the version from the
git tag and calls the built-in ``papertrail.trace`` command for every
customer-downloadable file. Pass the product name as a function var:

.. code-block:: yaml

   tasks:
     - name: release
       commands:
         - func: publish
         - func: trace artifacts
           vars:
             product: strands-mongodb

Use a dev product name, for example ``strands-mongodb-dev``, on
non-release builds.

Rules:

- One trace per customer-downloadable file: wheels, sdists, checksums,
  and signature files.
- The command rejects two files with the same name in one call.
- Filenames must include the version and be unique across releases.

Source: `mongo-java-driver
<https://github.com/mongodb/mongo-java-driver/blob/main/.evergreen/.evg.yml>`_
and `mongo-rust-driver
<https://github.com/mongodb/mongo-rust-driver/blob/main/.evergreen/releases.yml>`_.

GitHub Actions: ``authorized-pub`` and ``upload-s3-assets``
-----------------------------------------------------------

When the release runs on GitHub Actions, use the
authorized-publication report instead of ``papertrail.trace``. Run the
two actions in that order; there is no release chain that runs them
for you. Run ``setup`` first.

.. code-block:: yaml

   - uses: <owner>/abx-release-tools/actions/authorized-pub@<sha>
     with:
       product_name: strands-mongodb
       release_version: ${{ env.VERSION }}
       filenames: dist/*

   - uses: <owner>/abx-release-tools/actions/upload-s3-assets@<sha>
     with:
       product_name: strands-mongodb
       version: ${{ env.VERSION }}

``authorized-pub`` inputs:

.. list-table::
   :header-rows: 1

   * - Input
     - Required
     - Description
   * - ``product_name``
     - yes
     - Product name in the report.
   * - ``release_version``
     - yes
     - Released version.
   * - ``filenames``
     - no
     - Artifact files in the report. Can be a glob.
   * - ``token``
     - no
     - GitHub token used to read the releaser's name.

``upload-s3-assets`` inputs:

.. list-table::
   :header-rows: 1

   * - Input
     - Required
     - Description
   * - ``version``
     - yes
     - Published version. Forms the S3 key.
   * - ``product_name``
     - yes
     - Product name. Forms the S3 key.
   * - ``filenames``
     - no
     - Files to upload. Default ``*``.
   * - ``dry_run``
     - no
     - Print the files instead of uploading. Default ``false``.

The report lists Product, Version, Releaser, Build Source, Build
Number, and one Filename and Shasum pair per dist file. Agree the S3
bucket with DevProd Release Infrastructure, and agree that the S3
report meets the LRA requirement before you depend on it.
