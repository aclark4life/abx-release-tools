PyPI publishing
===============

GitHub Actions: ``python/publish``
----------------------------------

Publishes dists to PyPI with trusted publishing. No stored token: the
job presents a GitHub OIDC token and PyPI checks the claims against
the registered publisher.

The publish job needs ``id-token: write``. Without the permission the
OIDC token is not issued and the publish step fails:

.. code-block:: yaml

   publish:
     runs-on: ubuntu-latest
     permissions:
       id-token: write
     steps:
       - uses: actions/download-artifact@v4
         with:
           name: dist
           path: dist/
       - uses: <owner>/abx-release-tools/actions/python/publish@<sha>

Inputs
------

.. list-table::
   :header-rows: 1

   * - Input
     - Required
     - Description
   * - ``dist_path``
     - no
     - Directory holding the dists. Default ``dist/``.
   * - ``repository-url``
     - no
     - PyPI upload URL. Default ``https://upload.pypi.org/legacy/``.
   * - ``skip-existing``
     - no
     - Skip files already on the index. Default ``false``.

The action disables PyPI attestations. The Garasign signature from
:doc:`signing` is the only signature on an ABX release.

Pending publisher
-----------------

A publisher can only attach to a PyPI project that already exists. A
new package does not exist yet, so register a pending publisher by
hand on pypi.org before the first release: account settings, then
Publishing, then Add a new pending publisher. Without it, the release
run fails at the publish step, after a green build.

The Workflow field names the workflow file that contains the publish
job, not the workflow that dispatches it. Leave the Environment field
empty unless the publish job declares an ``environment:``.

Sign the release tag
--------------------

The DBX policy requires signed release tags. Sign them with the
``git-sign`` action; see :doc:`signing`.
