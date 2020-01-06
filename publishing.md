

Publishing notes
=================

To develop and test, see the "Developer Installation" in the README.

Notes:
-  `setup.py` uses `setuptools-markdown` which requires having installed:
    ```
    brew install pandoc
    pip3 install setuptools-markdown
    ```

- Make sure your `~/.pypirc` points to correct credentials. E.g.
    ```
    index-servers =
      pypitodbotdotcom

    [pypitodbotdotcom]
    username=todbotdotcom
    password=....
    ```

To publish:

1. Edit `setup.py` to bump version
2. Update README.md (use `pydoc blink1.blink1.Blink1 > api.txt` to generate new API ref)
3. Check changes into git
4. Publish to PyPI with:
```
python3 setup.py sdist upload -r pypitodbotdotcom
```
4. Verify new version on PyPi: https://pypi.org/project/blink1/
