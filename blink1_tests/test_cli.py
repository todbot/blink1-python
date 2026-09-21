"""The installed blink1-flash and blink1-shine scripts, against the fake."""

import pytest
from click.testing import CliRunner

from blink1.flash import flash
from blink1.shine import shine

from .fakehid import FakeHidModule


@pytest.fixture
def runner():
    return CliRunner()


def test_shine_sets_a_color(runner, fake_hid):
    result = runner.invoke(shine, ['--color', 'red'])
    assert result.exit_code == 0, result.output
    assert fake_hid.last_device.closed


def test_shine_leaves_the_light_on_by_default(runner, fake_hid):
    runner.invoke(shine, ['--color', 'red'])
    fades = [w for w in fake_hid.last_device.writes if w[1] == ord('c')]
    assert len(fades) == 1


def test_shine_can_switch_off(runner, fake_hid):
    """There was no way to do this from the CLI before."""
    result = runner.invoke(shine, ['--color', 'red', '--switch-off'])
    assert result.exit_code == 0, result.output
    fades = [w for w in fake_hid.last_device.writes if w[1] == ord('c')]
    assert fades[-1][2:5] == [0, 0, 0]


def test_shine_reports_a_bad_color_cleanly(runner, fake_hid):
    result = runner.invoke(shine, ['--color', 'moomintrol'])
    assert result.exit_code != 0
    assert 'bad color' in result.output
    assert not isinstance(result.exception, AttributeError)


def test_shine_closes_the_device_on_a_bad_color(runner, fake_hid):
    """The context manager used to leak the handle on this path."""
    runner.invoke(shine, ['--color', 'moomintrol'])
    assert fake_hid.last_device.closed


def test_shine_reports_no_device(runner, monkeypatch):
    import blink1.blink1 as blink1_mod
    monkeypatch.setattr(blink1_mod, "hid", FakeHidModule(serials=[]))
    result = runner.invoke(shine, ['--color', 'red'])
    assert result.exit_code != 0
    assert 'no blink(1) found' in result.output


def test_flash_accepts_a_fractional_duration(runner, fake_hid):
    """--duration 1.5 was rejected when the default was the int 1."""
    result = runner.invoke(flash, ['--duration', '0.01', '--repeat', '1'])
    assert result.exit_code == 0, result.output


def test_flash_closes_the_device(runner, fake_hid):
    """flash never closed its device at all."""
    runner.invoke(flash, ['--duration', '0.01', '--repeat', '1'])
    assert fake_hid.last_device.closed


def test_flash_reports_a_bad_color_cleanly(runner, fake_hid):
    result = runner.invoke(flash, ['--on', 'moomintrol', '--duration', '0.01'])
    assert result.exit_code != 0
    assert 'bad color' in result.output
    assert fake_hid.last_device.closed


def test_flash_reports_no_device(runner, monkeypatch):
    import blink1.blink1 as blink1_mod
    monkeypatch.setattr(blink1_mod, "hid", FakeHidModule(serials=[]))
    result = runner.invoke(flash, ['--duration', '0.01'])
    assert result.exit_code != 0
    assert 'no blink(1) found' in result.output
