import pytest

import blink1.blink1 as blink1_mod

from .fakehid import FakeHidModule


def pytest_addoption(parser):
    parser.addoption(
        "--run-hardware",
        action="store_true",
        default=False,
        help="run tests that need a physical blink(1) attached",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-hardware"):
        return
    skip = pytest.mark.skip(reason="needs a blink(1); pass --run-hardware")
    for item in items:
        if "hardware" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def fake_hid(monkeypatch):
    """Swap the module-level `hid` that blink1.blink1 imported."""
    fake = FakeHidModule()
    monkeypatch.setattr(blink1_mod, "hid", fake)
    return fake


@pytest.fixture
def b1(fake_hid):
    # pattern_lines given explicitly so construction issues no version
    # query, keeping the write log free of setup noise
    dev = blink1_mod.Blink1(pattern_lines=32)
    yield dev
    if dev.dev is not None:
        dev.close()
