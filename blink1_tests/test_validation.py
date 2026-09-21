"""Validation of caller-supplied colors, and clamping of computed bytes."""

import pytest

from blink1.blink1 import (
    Blink1,
    ColorCorrect,
    InvalidColor,
    UnknownWhitePoint,
)


@pytest.mark.parametrize("bad", [
    (256, 0, 0),
    (-1, 0, 0),
    (0, 0, 300),
    (1, 2),
    (1, 2, 3, 4),
    None,
    42,
    b"#ff0000",
    "moomintrol",
    "#xxxxxx",
    ("a", "b", "c"),
    "255,0",
    "1,2,3,4",
    "300,0,0",
    "zz,0,0",
])
def test_bad_colors_raise_invalid_color(bad):
    with pytest.raises(InvalidColor):
        Blink1.color_to_rgb(bad)


@pytest.mark.parametrize("good,expected", [
    ("#ff00ff", (255, 0, 255)),
    ("green", (0, 128, 0)),
    ((22, 33, 44), (22, 33, 44)),
    ([22, 33, 44], (22, 33, 44)),
    # the forms blink1-tool's parsecolor() accepts
    ("FF00FF", (255, 0, 255)),
    ("ff00ff", (255, 0, 255)),
    ("255,0,255", (255, 0, 255)),
    ("0xff,0x00,0xff", (255, 0, 255)),
    (" 255 , 0 , 255 ", (255, 0, 255)),
])
def test_good_colors(good, expected):
    assert tuple(Blink1.color_to_rgb(good)) == expected


def test_fade_to_rgb_rejects_out_of_range(b1):
    with pytest.raises(InvalidColor):
        b1.fade_to_rgb(0, 300, 0, 0)


def test_fade_to_rgb_rejects_non_numeric(b1):
    with pytest.raises(InvalidColor):
        b1.fade_to_rgb(0, "red", 0, 0)


def test_ledn_out_of_range(b1):
    with pytest.raises(ValueError):
        b1.fade_to_rgb(0, 255, 0, 0, ledn=3)
    with pytest.raises(ValueError):
        b1.set_ledn(9)


def test_low_gamma_still_writes_bytes_in_range(fake_hid):
    """Gamma below 1 can compute past 255; those get clamped, not rejected."""
    b1 = Blink1(gamma=(0.1, 0.1, 0.1), white_point=(255, 255, 255),
               pattern_lines=32)
    b1.fade_to_color(0, 'white')
    for buf in fake_hid.last_device.writes:
        assert all(0 <= v <= 255 for v in buf), buf
    b1.close()


def test_unknown_white_point_name():
    with pytest.raises(UnknownWhitePoint):
        ColorCorrect(gamma=(2, 2, 2), white_point='candel')


def test_unknown_white_point_is_still_a_key_error():
    """Callers written against the old bare KeyError keep working."""
    with pytest.raises(KeyError):
        ColorCorrect(gamma=(2, 2, 2), white_point='candel')


def test_notfound_is_deprecated():
    with pytest.deprecated_call():
        assert Blink1.notfound() is None
