

Publishing notes
=================

Releases are published to PyPI by GitHub Actions
(`.github/workflows/release.yml`) when a release is published on GitHub.
Nothing is built or uploaded from a laptop, and there is no API token to
keep anywhere: PyPI trusted publishing authenticates the workflow itself.

To develop and test, see "Developer installation" in the README.


One-time setup
--------------

1. On pypi.org, go to the `blink1` project, then Manage project ->
   Settings -> Publishing (the project's own settings, not the account
   ones). Add a GitHub publisher:

   * Owner: `todbot`
   * Repository: `blink1-python`
   * Workflow name: `release.yml`
   * Environment: `pypi`

2. Repeat on test.pypi.org, with environment name `testpypi`.

3. On GitHub, Settings -> Environments, create environments named `pypi`
   and `testpypi`.

Adding a required reviewer to the `pypi` environment is worth doing: it
means no release can reach PyPI without someone approving it. Be aware of
how that looks, so it is not mistaken for a stuck job. Publishing the
GitHub release runs the checks and the build, then **waits** at the
publish step until the environment is approved. Nothing is uploaded
before that.


Publishing a release
--------------------

1. Bump `version` in `pyproject.toml`, and add the matching section to
   `CHANGELOG.md`.
2. Get that onto `main`, and let CI go green.
3. Optionally rehearse: run the Release workflow manually
   (Actions -> Release -> Run workflow). A manual run publishes to
   TestPyPI instead of PyPI, so the whole pipeline can be checked without
   using up a version number. Verify at
   https://test.pypi.org/project/blink1/
4. Draft a GitHub release tagged `vX.Y.Z`, using the CHANGELOG entry as
   the notes.
5. Publish the release. The workflow verifies the tag, runs the tests,
   lint and typecheck, builds, and uploads.
6. Verify the new version at https://pypi.org/project/blink1/

The tag must match the version in `pyproject.toml`, with or without a
leading `v`. If it does not, the workflow fails immediately at the
`verify-tag` job and publishes nothing, so a mistyped tag costs seconds
rather than a burnt version number.


Regenerating the API reference
------------------------------

The "API reference" section of README.md is generated, not hand-written.
Run `python3 -m pydoc blink1.blink1 > api.txt`, then paste in the
`Blink1` and `ColorCorrect` class blocks and the `FUNCTIONS` section,
trimmed of inherited boilerplate. The module-level form matters: the
older class-only `pydoc blink1.blink1.Blink1` cannot show the `blink1()`
context manager, `ColorCorrect`, or the exception classes.


Checking a release locally
--------------------------

The workflow does all of this, but the same commands run by hand if you
want to check before tagging:

```
pytest -q
ruff check .
mypy blink1/
python3 -m build
python3 -m twine check dist/*
```
