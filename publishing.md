

Publishing notes
=================


To publish:

1. Edit `setup.py` to bump version
2. Check changes into git
3. Publish to PyPI
```
python3 setup.py sdist upload -r pypitodbotdotcom  # or whatever your repo is called
```
4. Verify new version on PyPi: https://pypi.org/project/blink1/


Note `setup.py` uses `setuptools-markdown` which requires having installed:
```
brew install pandoc
pip3 install setuptools-markdown
```

Make sure your `~/.pypirc` points to correct credentials. E.g.
```
index-servers =
  pypitodbotdotcom

[pypitodbotdotcom]
username=todbotdotcom
password=....
