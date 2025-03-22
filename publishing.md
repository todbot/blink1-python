

Publishing notes
=================

To develop and test, see the "Developer Installation" in the README.

To publish:

1. Edit `pyproject.toml` to bump version
2. Update README.md (use `pydoc blink1.blink1.Blink1 > api.txt` to generate new API ref)
3. Check can build with `python3 -m build`
3. Check changes into git
4. Publish to PyPI with:  (must have pypi API token handy)

```
python3 -m pip install --upgrade twine
python3 -m build
# to test
python3 -m twine upload --repository testpypi dist/*
# for reals
python3 -m twine upload dist/*
```
4. Verify new version on PyPi: https://pypi.org/project/blink1/
