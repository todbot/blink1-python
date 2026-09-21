"""Pattern parsing, pattern memory sizing, and the on_device alias."""

import pytest

from blink1.blink1 import (
    PATTERN_LINES_MK2,
    PATTERN_LINES_MK3,
    Blink1,
)

from .fakehid import FakeHidModule

# Every pattern string shipped in blink1_demo/demo_pattern3.py, including
# the one with an empty field that used to raise.
DEMO_PATTERNS = [
    '3, #ff00ff,0.3,1, #00ff00,0.1,2,#ff00ff,0.3,2,#00ff00,0.1,1,#000000,0.5,0',
    '5, #FF0000,0.2,0,#000000,0.2,0',
    ' 10, #ff00ff,0.3,1, #00ff00,0.1,2,  #ff00ff,0.3,2, #00ff00,0.1,1',
    '  10, #ff00ff,0.3,1, #00ff00,0.1,2 ',
    '  7, #ff00ff,0.3,1, #00ff00,0.1,2, #ff3333  ',
    '  1, ',
    '  2, #ff99cc,,0.3',
    '  0, #ff00ff,0.3',
]


@pytest.mark.parametrize("patt", DEMO_PATTERNS)
def test_demo_patterns_parse(patt):
    num_repeats, colorlist = Blink1.parse_pattern(patt)
    assert isinstance(num_repeats, int)
    for c in colorlist:
        assert set(c) == {'rgb', 'time', 'ledn', 'millis'}


def test_empty_fields_take_defaults():
    _, colorlist = Blink1.parse_pattern('10,#ff00ff,,0')
    assert colorlist[0] == {'rgb': '#ff00ff', 'time': 0.0, 'ledn': 0, 'millis': 0}


def test_missing_trailing_fields_take_defaults():
    _, colorlist = Blink1.parse_pattern('10,#ff00ff,0.1,')
    assert colorlist[0]['ledn'] == 0
    assert colorlist[0]['millis'] == 100


def test_empty_color_field_defaults_to_black():
    _, colorlist = Blink1.parse_pattern('1,,0.1,0')
    assert colorlist[0]['rgb'] == '#000000'


def test_bad_repeat_count_is_a_clear_error():
    with pytest.raises(ValueError, match="repeat count"):
        Blink1.parse_pattern('notanumber,#ff00ff,0.1,0')


def test_parse_returns_a_two_tuple():
    result = Blink1.parse_pattern('2,#ff00ff,0.1,0')
    assert len(result) == 2
    assert isinstance(result[1], list)


def _writes_of(fake, cmd):
    return [w for w in fake.last_device.writes if w[1] == ord(cmd)]


def test_play_pattern_fills_mk3_memory(fake_hid):
    b1 = Blink1(pattern_lines=PATTERN_LINES_MK3)
    b1.play_pattern('2,#ff00ff,0.1,0')
    assert len(_writes_of(fake_hid, 'P')) == PATTERN_LINES_MK3
    assert len(_writes_of(fake_hid, 'p')) == 1
    b1.close()


def test_play_pattern_fills_mk2_memory(fake_hid):
    b1 = Blink1(pattern_lines=PATTERN_LINES_MK2)
    b1.play_pattern('2,#ff00ff,0.1,0')
    assert len(_writes_of(fake_hid, 'P')) == PATTERN_LINES_MK2
    b1.close()


def test_pattern_longer_than_memory_is_truncated(fake_hid):
    b1 = Blink1(pattern_lines=PATTERN_LINES_MK2)
    long_patt = '1,' + ','.join(['#ff0000,0.1,0'] * 20)
    b1.play_pattern(long_patt)
    assert len(_writes_of(fake_hid, 'P')) == PATTERN_LINES_MK2
    b1.close()


def test_write_pattern_line_rejects_out_of_range_pos(fake_hid):
    b1 = Blink1(pattern_lines=PATTERN_LINES_MK2)
    with pytest.raises(ValueError):
        b1.write_pattern_line(100, 'red', PATTERN_LINES_MK2)
    b1.close()


def test_pattern_round_trips(fake_hid):
    b1 = Blink1(pattern_lines=PATTERN_LINES_MK3)
    b1.write_pattern_line(500, '#ff0000', 3)
    r, g, b, millis = b1.read_pattern_line(3)
    assert millis == 500
    assert (r, g, b) == b1.cc(255, 0, 0)
    b1.close()


def test_read_pattern_line_can_undo_gamma(fake_hid):
    b1 = Blink1(pattern_lines=PATTERN_LINES_MK3)
    b1.write_pattern_line(100, (200, 100, 50), 0)
    raw = b1.read_pattern_line(0)[:3]
    undone = b1.read_pattern_line(0, uncorrect=True)[:3]
    assert undone != raw
    assert undone == pytest.approx((200, 100, 50), abs=2)
    b1.close()


def test_read_pattern_length_follows_device(fake_hid):
    b1 = Blink1(pattern_lines=PATTERN_LINES_MK2)
    assert len(b1.read_pattern()) == PATTERN_LINES_MK2
    b1.close()


@pytest.mark.parametrize("firmware,expected", [
    ("306", PATTERN_LINES_MK3),
    ("300", PATTERN_LINES_MK3),
    ("206", PATTERN_LINES_MK2),
    ("104", PATTERN_LINES_MK2),
])
def test_pattern_lines_detected_from_firmware(monkeypatch, firmware, expected):
    import blink1.blink1 as blink1_mod
    fake = FakeHidModule(firmware=firmware)
    monkeypatch.setattr(blink1_mod, "hid", fake)
    b1 = Blink1()
    assert b1.pattern_lines == expected
    b1.close()


def test_detection_falls_back_to_mk3_when_version_is_unreadable(monkeypatch):
    import blink1.blink1 as blink1_mod
    fake = FakeHidModule()
    monkeypatch.setattr(blink1_mod, "hid", fake)
    monkeypatch.setattr(Blink1, "get_version", lambda self: "bogus")
    b1 = Blink1()
    assert b1.pattern_lines == PATTERN_LINES_MK3
    b1.close()


def test_explicit_pattern_lines_skips_detection(fake_hid):
    b1 = Blink1(pattern_lines=PATTERN_LINES_MK2)
    assert b1.pattern_lines == PATTERN_LINES_MK2
    assert _writes_of(fake_hid, 'v') == []
    b1.close()


def test_on_device_alias_matches_camelcase(fake_hid, monkeypatch):
    b1 = Blink1(pattern_lines=PATTERN_LINES_MK3)
    called = []
    monkeypatch.setattr(Blink1, "play_pattern_local",
                        lambda self, s: called.append(s))
    b1.play_pattern('1,#ff0000,0.1,0', on_device=False)
    b1.play_pattern('1,#00ff00,0.1,0', onDevice=False)
    b1.play_pattern('1,#0000ff,0.1,0', False)
    assert len(called) == 3
    b1.close()


def test_play_pattern_local_rejects_negative_repeats(fake_hid):
    b1 = Blink1(pattern_lines=PATTERN_LINES_MK3)
    with pytest.raises(ValueError):
        b1.play_pattern('-3,#ff0000,0.1,0', on_device=False)
    b1.close()
