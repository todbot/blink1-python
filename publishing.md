

Publishing notes
=================

To develop and test, see the "Developer Installation" in the README.

To publish:

1. Edit `pyproject.toml` to bump version, and add a section to
   `CHANGELOG.md`
2. Update README.md. Use `python3 -m pydoc blink1.blink1 > api.txt` to
   generate a new API ref; the module-level form also covers the
   `blink1()` context manager, `ColorCorrect` and the exception classes,
   which the old class-only form left out.
3. Check tests and lint pass: `pytest`, `ruff check .`, `mypy blink1/`
4. Check it builds: `python3 -m build` then `python3 -m twine check dist/*`
5. Check changes into git
6. Publish to PyPI with:  (must have pypi API token handy)

```
python3 -m pip install --upgrade twine
python3 -m build
# to test
python3 -m twine upload --repository testpypi dist/*
# for reals
python3 -m twine upload dist/*
```
7. Verify new version on PyPi: https://pypi.org/project/blink1/
