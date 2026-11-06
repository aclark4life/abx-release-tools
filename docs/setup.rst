Setup
=====

The ``setup`` action prepares the release environment. Run it first:
every other action except ``python/publish`` reads the environment it
writes.

Usage
-----

.. code-block:: yaml

   - uses: <owner>/abx-release-tools/actions/setup@<sha>
     with:
       aws_role_arn: ${{ secrets.AWS_ROLE_ARN }}
       aws_region_name: ${{ vars.AWS_REGION_NAME }}
       aws_secret_id: ${{ secrets.AWS_SECRET_ID }}

Inputs
------

.. list-table::
   :header-rows: 1

   * - Input
     - Required
     - Description
   * - ``aws_role_arn``
     - yes
     - AWS role that can read the release secret.
   * - ``aws_region_name``
     - yes
     - AWS region of the secret.
   * - ``aws_secret_id``
     - yes
     - AWS Secrets Manager secret holding the release credentials.
   * - ``ecr_registry_id``
     - no
     - ECR registry id. Default ``901841024863``.
   * - ``ecr_role_arn``
     - no
     - ECR pull role. Default ``ecr-role-gha-ro``.
   * - ``ecr_region``
     - no
     - ECR region. Default ``us-east-1``.

What it writes
--------------

The action logs in to ECR, reads the AWS secret, and exports:

- ``RELEASE_ASSETS`` — directory for artifacts that ship with the
  release.
- ``S3_ASSETS`` — directory for files uploaded to the release S3
  bucket.
- ``GARASIGN_ENVFILE`` — environment file for the Garasign container.
  Holds ``GARASIGN_USERNAME`` and ``GARASIGN_PASSWORD`` from the secret.
- ``KONDUKTO_ENVFILE`` — environment file with ``KONDUKTO_TOKEN``.
  Written only if the secret contains the token.
- ``AWS_BUCKET`` — release S3 bucket (``RELEASE_ASSETS_BUCKET`` key in
  the secret).
- ``GPG_KEY_ID``, ``GPG_PUBLIC_URL``, ``SECURITY_REPORT_URL`` — passed
  through from the secret when present.

It also sets the git identity to ``mongodb-dbx-release-bot[bot]`` for
release commits and tags.

Per-repo onboarding
-------------------

Four steps sit outside this repo. Do them once per repo:

1. File the Kondukto RNDSEC onboarding ticket.
2. Request the Kondukto CI API token and store it as a CI secret.
3. Agree the Papertrail product name with DevProd Release
   Infrastructure.
4. Register the PyPI pending publisher for each new package.

The ABX release how-to guides have the details.
