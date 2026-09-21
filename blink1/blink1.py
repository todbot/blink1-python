# -*- coding: utf-8 -*-
"""
blink1.py -- blink(1) Python library using python hidapi

All platforms:
 % pip3 install blink1

"""
from __future__ import annotations

import logging
import os
import time
import warnings
from contextlib import contextmanager
from typing import Any, Iterator, List, Sequence, Tuple, Union

import hid
import webcolors

from .kelvin import COLOR_TEMPERATURES, kelvin_to_rgb


class Blink1ConnectionFailed(RuntimeError):
    """Raised when we cannot connect to a Blink(1)
    """


class InvalidColor(ValueError):
    """Raised when the user requests an implausible colour
    """


class UnknownWhitePoint(InvalidColor, KeyError):
    """Raised when a white point is named that has no color temperature.

    Also a KeyError, so callers written against the old bare KeyError
    keep working.
    """


log = logging.getLogger(__name__)
if os.getenv('DEBUGBLINK1'):
    log.setLevel(logging.DEBUG)


DEFAULT_GAMMA = (2, 2, 2)
DEFAULT_WHITE_POINT = (255, 255, 255)

REPORT_ID = 0x01
VENDOR_ID = 0x27B8
PRODUCT_ID = 0x01ED

REPORT_SIZE = 9  # 8 bytes + 1 byte reportId

MAX_LEDN = 2

RGB = Tuple[int, ...]
Color = Union[str, Sequence[float]]
WhitePoint = Union[str, float, Sequence[float]]

# mk2 has 16 color pattern lines, mk3 has 32. Firmware 3xx is mk3.
PATTERN_LINES_MK2 = 16
PATTERN_LINES_MK3 = 32
PATTERN_LINES_DEFAULT = PATTERN_LINES_MK3
MK3_MIN_VERSION = 300


def _clamp_byte(value: float) -> int:
    """Clamp a library-computed channel value into the 0-255 wire range.

    Gamma below 1 or a bright white point can legitimately push a
    corrected value past 255, so these are clamped rather than rejected.
    """
    return min(255, max(0, int(value)))


def _validate_channel(value: Any, name: str) -> Any:
    try:
        num = float(value)
    except (TypeError, ValueError) as e:
        raise InvalidColor("%s must be a number, got %r" % (name, value)) from e
    if not 0 <= num <= 255:
        raise InvalidColor("%s must be 0-255, got %r" % (name, value))
    return value


def _validate_ledn(ledn: Any) -> int:
    try:
        n = int(ledn)
    except (TypeError, ValueError) as e:
        raise ValueError("ledn must be an integer, got %r" % (ledn,)) from e
    if not 0 <= n <= MAX_LEDN:
        raise ValueError("ledn must be 0-%d, got %r" % (MAX_LEDN, ledn))
    return n


class ColorCorrect(object):
    """Apply a gamma correction to any selected RGB color, see:
    http://en.wikipedia.org/wiki/Gamma_correction
    """
    def __init__(self, gamma: Sequence[float], white_point: WhitePoint) -> None:
        """
        :param gamma: Tuple of r,g,b gamma values
        :param white_point: White point expressed as (r,g,b), integer color
            temperature (in Kelvin) or a string value.
        :raises: UnknownWhitePoint: if white_point names no known temperature

        Gamma values above 1 darken mid-tones; the library default is
        (2, 2, 2). Values below 1 brighten them.
        """

        self.gamma: Sequence[float] = gamma
        self.white_point: Sequence[float]

        if isinstance(white_point, str):
            try:
                kelvin = COLOR_TEMPERATURES[white_point]
            except KeyError as e:
                raise UnknownWhitePoint(
                    "unknown white point %r, expected one of: %s"
                    % (white_point, ", ".join(sorted(COLOR_TEMPERATURES)))
                ) from e
            self.white_point = kelvin_to_rgb(kelvin)
        elif isinstance(white_point, (int, float)):
            self.white_point = kelvin_to_rgb(white_point)
        else:
            self.white_point = white_point

    @staticmethod
    def gamma_correct(gamma: float, white: float, luminance: float) -> int:
        return round(white * (luminance / 255.0) ** gamma)

    @staticmethod
    def gamma_uncorrect(gamma: float, white: float, value: float) -> int:
        if not white:
            return 0
        return round(255 * (min(value, white) / white) ** (1.0 / gamma))

    def __call__(self, r: float, g: float, b: float) -> RGB:
        return tuple(
            self.gamma_correct(gam, white, lum)
            for (gam, white, lum) in zip(self.gamma, self.white_point, [r, g, b])
        )

    def uncorrect(self, r: float, g: float, b: float) -> RGB:
        """Undo __call__, mapping device values back towards the input range."""
        return tuple(
            self.gamma_uncorrect(gam, white, value)
            for (gam, white, value) in zip(self.gamma, self.white_point, [r, g, b])
        )


class Blink1(object):
    """Light controller class, sends messages to the blink(1) via USB HID.
    """
    def __init__(self, serial_number: str | None = None,
                 gamma: Sequence[float] | None = None,
                 white_point: WhitePoint | None = None,
                 pattern_lines: int | None = None) -> None:
        """
        :param serial_number: serial number of blink(1) to open, otherwise first found
        :param gamma: Triple of gammas for each channel e.g. (2, 2, 2)
        :param white_point: White point as (r,g,b), Kelvin, or a name
        :param pattern_lines: size of the device's color pattern memory.
            Detected from the firmware version when left as None.
        :raises: Blink1ConnectionFailed: if blink(1) is not present
        """
        self.cc = ColorCorrect(
            gamma=gamma or DEFAULT_GAMMA,
            white_point=(white_point or DEFAULT_WHITE_POINT)
        )
        self.dev = self.find(serial_number)
        self.pattern_lines = (
            self.detect_pattern_lines() if pattern_lines is None else int(pattern_lines)
        )

    def detect_pattern_lines(self) -> int:
        """Ask the firmware how big the color pattern memory is.

        Falls back to the mk3 size on any failure, which is what the
        library assumed unconditionally before this existed.
        """
        try:
            version = int(self.get_version())
        except Exception as e:
            log.debug("pattern line detection failed (%s), assuming mk3", e)
            return PATTERN_LINES_DEFAULT
        return PATTERN_LINES_MK3 if version >= MK3_MIN_VERSION else PATTERN_LINES_MK2

    def close(self) -> None:
        """Close the connection to the blink(1). Safe to call twice."""
        if self.dev is not None:
            self.dev.close()
            self.dev = None

    def __enter__(self) -> "Blink1":
        return self

    def __exit__(self, exc_type: object, exc_value: object,
                 traceback: object) -> None:
        self.close()

    def _require_dev(self) -> None:
        if self.dev is None:
            raise Blink1ConnectionFailed("blink(1) is closed")

    @staticmethod
    def find(serial_number: str | None = None):
        """ Find a particular blink(1) device, or the first one
        :param serial_number: serial number of blink(1) device (from Blink1.list())
        :raises: Blink1ConnectionFailed: if blink(1) is not present
        """
        try:
            hidraw = hid.device(VENDOR_ID, PRODUCT_ID, serial_number)
            hidraw.open(VENDOR_ID, PRODUCT_ID, serial_number)
        except OSError as e:
            raise Blink1ConnectionFailed(e) from e

        return hidraw

    @staticmethod
    def list() -> List[str]:
        """ List blink(1) devices connected, by serial number
        :return: List of blink(1) device serial numbers
        """
        try:
            devs = hid.enumerate(VENDOR_ID, PRODUCT_ID)
            return [d.get('serial_number') for d in devs]
        except OSError:
            return []

    @staticmethod
    def notfound() -> None:
        """Deprecated, always returns None. Use Blink1ConnectionFailed instead."""
        warnings.warn(
            "Blink1.notfound() is deprecated and does nothing; catch "
            "Blink1ConnectionFailed instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return None

    def write(self, buf: Sequence[int]) -> None:
        """ Write command to blink(1), low-level internal use
        Send USB Feature Report 0x01 to blink(1) with 8-byte payload
        Note: arg 'buf' must be 8 bytes or bad things happen
        :raises: Blink1ConnectionFailed if blink(1) is disconnected or closed
        """
        self._require_dev()
        log.debug("blink1write:" + ",".join('0x%02x' % v for v in buf))
        rc = self.dev.send_feature_report(buf)
        if rc != REPORT_SIZE:
            raise Blink1ConnectionFailed(
                "write returned %d instead of %d" % (rc, REPORT_SIZE)
            )

    def read(self) -> List[int]:
        """ Read command result from blink(1), low-level internal use
        Receive USB Feature Report 0x01 from blink(1) with 8-byte payload
        Note: buf must be 8 bytes or bad things happen
        :raises: Blink1ConnectionFailed if blink(1) is disconnected or closed
        """
        self._require_dev()
        buf = self.dev.get_feature_report(REPORT_ID, REPORT_SIZE)
        log.debug("blink1read: " + ",".join('0x%02x' % v for v in buf))
        if len(buf) != REPORT_SIZE:
            raise Blink1ConnectionFailed(
                "read returned %d bytes instead of %d" % (len(buf), REPORT_SIZE)
            )
        return buf

    def fade_to_rgb_uncorrected(
        self,
        fade_milliseconds,
        red,
        green,
        blue,
        ledn=0
    ):
        """ Command blink(1) to fade to RGB color, no color correction applied.
        :raises: Blink1ConnectionFailed if blink(1) is disconnected
        """
        action = ord('c')
        fade_time = int(fade_milliseconds / 10)
        th = (fade_time & 0xff00) >> 8
        tl = fade_time & 0x00ff
        buf = [
            REPORT_ID, action,
            _clamp_byte(red), _clamp_byte(green), _clamp_byte(blue),
            th, tl, _validate_ledn(ledn), 0,
        ]
        self.write(buf)

    def fade_to_rgb(self, fade_milliseconds: float, red: float, green: float,
                    blue: float, ledn: int = 0) -> None:
        """ Command blink(1) to fade to RGB color
        :param fade_milliseconds: millisecs duration of fade
        :param red: 0-255
        :param green: 0-255
        :param blue: 0-255
        :param ledn: which LED to control (0=all, 1=LED A, 2=LED B)
        :raises: InvalidColor: if a channel is not a number in 0-255
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        red = _validate_channel(red, 'red')
        green = _validate_channel(green, 'green')
        blue = _validate_channel(blue, 'blue')
        r, g, b = self.cc(red, green, blue)
        return self.fade_to_rgb_uncorrected(fade_milliseconds, r, g, b, ledn)

    @staticmethod
    def color_to_rgb(color: Color) -> RGB:
        """ Convert color name, hexcode or (r,g,b) sequence to an (r,g,b) tuple
        :param color: a color string, e.g. "#FF00FF" or "red", or an
            (r,g,b) tuple or list with each channel 0-255
        :raises: InvalidColor: if the color cannot be interpreted
        """
        if isinstance(color, (tuple, list)):
            if len(color) != 3:
                raise InvalidColor(
                    "expected 3 channels, got %d: %r" % (len(color), color)
                )
            return tuple(
                _validate_channel(c, name)
                for c, name in zip(color, ('red', 'green', 'blue'))
            )
        if not isinstance(color, str):
            raise InvalidColor(
                "expected a color name, hexcode or (r,g,b), got %r" % (color,)
            )
        if color.startswith('#'):
            try:
                return webcolors.hex_to_rgb(color)
            except ValueError as e:
                raise InvalidColor(color) from e

        try:
            return webcolors.name_to_rgb(color)
        except ValueError as e:
            raise InvalidColor(color) from e

    def fade_to_color(self, fade_milliseconds: float, color: Color, ledn: int = 0) -> None:
        """ Fade the light to a known colour
        :param fade_milliseconds: Duration of the fade in milliseconds
        :param color: Named color to fade to (e.g. "#FF00FF", "red")
        :param ledn: which led to control
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        red, green, blue = self.color_to_rgb(color)

        return self.fade_to_rgb(fade_milliseconds, red, green, blue, ledn)

    def off(self) -> None:
        """ Switch the blink(1) off instantly
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        self.fade_to_color(0, 'black')

    def get_version(self) -> str:
        """ Get blink(1) firmware version
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        buf = [REPORT_ID, ord('v'), 0, 0, 0, 0, 0, 0, 0]
        self.write(buf)
        time.sleep(.05)
        version_raw = self.read()
        version = (version_raw[3] - ord('0')) * 100 + (version_raw[4] - ord('0'))
        return str(version)

    def get_serial_number(self) -> str:
        """ Get blink(1) serial number
        :return blink(1) serial number as string
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        self._require_dev()
        return self.dev.get_serial_number_string()

    def play(self, start_pos: int = 0, end_pos: int = 0, count: int = 0) -> None:
        """ Play internal color pattern
        :param start_pos: pattern line to start from
        :param end_pos: pattern line to end at
        :param count: number of times to play, 0=play forever
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        if self.dev is None:
            raise Blink1ConnectionFailed("must open first")

        buf = [
            REPORT_ID,
            ord('p'),
            1,
            int(start_pos),
            int(end_pos),
            _clamp_byte(count),
            0,
            0,
            0
        ]
        self.write(buf)

    def stop(self):
        """ Stop internal color pattern playing
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        # Returns False rather than raising on a closed device, unlike the
        # rest of the class. Kept for callers that branch on it.
        if self.dev is None:
            return False

        buf = [REPORT_ID, ord('p'), 0, 0, 0, 0, 0, 0, 0]
        self.write(buf)

    def save_pattern(self) -> None:
        """ Save internal RAM pattern to flash
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        buf = [REPORT_ID, ord('W'), 0xBE, 0xEF, 0xCA, 0xFE, 0, 0, 0]
        self.write(buf)

    def set_ledn(self, ledn: int = 0) -> None:
        """ Set the 'current LED' value for writePatternLine
        :param ledn: LED to adjust, 0=all, 1=LEDA, 2=LEDB
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        buf = [REPORT_ID, ord('l'), _validate_ledn(ledn), 0, 0, 0, 0, 0, 0]
        self.write(buf)

    def write_pattern_line(self, step_milliseconds: float, color: Color,
                           pos: int, ledn: int = 0) -> None:
        """ Write a color & step time color pattern line to RAM
        :param step_milliseconds: how long for this pattern line to take
        :param color: LED color
        :param pos: color pattern line number, 0 to pattern_lines-1
        :param ledn: LED number to adjust, 0=all, 1=LEDA, 2=LEDB
        :raises: ValueError: if pos is outside the device's pattern memory
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected

        Note this applies gamma correction, while read_pattern_line()
        returns raw device values.
        """
        pos = int(pos)
        if not 0 <= pos < self.pattern_lines:
            raise ValueError(
                "pos must be 0-%d, got %d" % (self.pattern_lines - 1, pos)
            )
        self.set_ledn(ledn)
        red, green, blue = self.color_to_rgb(color)
        r, g, b = self.cc(red, green, blue)
        step_time = int(step_milliseconds / 10)
        th = (step_time & 0xff00) >> 8
        tl = step_time & 0x00ff
        buf = [
            REPORT_ID, ord('P'),
            _clamp_byte(r), _clamp_byte(g), _clamp_byte(b),
            th, tl, pos, 0,
        ]
        self.write(buf)

    def read_pattern_line(self, pos: int, uncorrect: bool = False) -> Tuple[Any, ...]:
        """ Read a color pattern line at position
        :param pos: pattern line to read
        :param uncorrect: undo the gamma correction write_pattern_line()
            applied, so a read-modify-write round trip does not compound it
        :return pattern line data as tuple (r,g,b, step_millis)
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        self.write([REPORT_ID, ord('R'), 0, 0, 0, 0, 0, int(pos), 0])
        buf = self.read()

        r, g, b = buf[2:5]
        if uncorrect:
            r, g, b = self.cc.uncorrect(r, g, b)

        step_millis = ((buf[5] << 8) | buf[6]) * 10
        return r, g, b, step_millis

    def read_pattern(self, uncorrect: bool = False) -> List[Tuple[Any, ...]]:
        """ Read the entire color pattern
        :param uncorrect: see read_pattern_line()
        :return List of pattern line tuples
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        return [
            self.read_pattern_line(i, uncorrect=uncorrect)
            for i in range(self.pattern_lines)
        ]

    def clear_pattern(self) -> None:
        """ Clear entire color pattern in blink(1)
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        for i in range(self.pattern_lines):
            self.write_pattern_line(0, 'black', i)

    def play_pattern(self, pattern_str: str, onDevice: bool = True, *,
                     on_device: bool | None = None) -> None:
        """ Play a Blink1Control-style pattern string
        :param pattern_str: The Blink1Control-style pattern string to play
        :param onDevice: True (default) to run pattern on blink(1),
                         otherwise plays in Python process
        :param on_device: snake_case spelling of onDevice; wins if given
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected

        Note this overwrites the whole pattern memory, which is what
        makes the played pattern deterministic.
        """
        if on_device is not None:
            onDevice = on_device
        if not onDevice:
            return self.play_pattern_local(pattern_str)

        # else, play it in the blink(1)
        num_repeats, colorlist = self.parse_pattern(pattern_str)

        empty_color = {
            'rgb': '#000000',
            'time': 0.0,
            'ledn': 0,
            'millis': 0
        }

        colorlist = colorlist[:self.pattern_lines]
        colorlist += [empty_color] * (self.pattern_lines - len(colorlist))

        for i, c in enumerate(colorlist):
            self.write_pattern_line(c['millis'], c['rgb'], i, c['ledn'])

        return self.play(count=num_repeats)

    def play_pattern_local(self, pattern_str: str) -> None:
        """ Play a Blink1Control pattern string in Python process
            (plays in blink1-python, so blocks)
        :param pattern_str: The Blink1Control-style pattern string to play
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        num_repeats, colorlist = self.parse_pattern(pattern_str)
        if num_repeats < 0:
            raise ValueError(
                "repeat count cannot be negative; 0 means play forever"
            )
        if num_repeats == 0:
            num_repeats = -1

        while num_repeats:
            num_repeats -= 1

            for c in colorlist:
                self.fade_to_color(c['millis'], c['rgb'], c['ledn'])
                time.sleep(c['time'])

    @staticmethod
    def parse_pattern(pattern_str: str) -> Tuple[int, List[dict]]:
        """ Parse a Blink1Control pattern string to a list of pattern lines
            e.g. of the form '10,#ff00ff,0.1,0,#00ff00,0.1,0'
        :param pattern_str: The Blink1Control-style pattern string to parse
        :returns: tuple of (num_repeats, list of pattern line dicts)
        :raises: ValueError: if the repeat count or a field is unparseable

        Omitted and empty fields take their defaults, so
        '2,#ff99cc,,0.3' parses rather than raising.
        """
        pattparts = pattern_str.replace(' ', '').split(',')
        repeats_raw = pattparts[0]
        try:
            num_repeats = int(repeats_raw) if repeats_raw else 0
        except ValueError as e:
            raise ValueError(
                "pattern must start with a repeat count, got %r" % (repeats_raw,)
            ) from e
        pattparts = pattparts[1:]

        colorlist = []
        for i in range(0, len(pattparts), 3):
            fields = pattparts[i:i + 3]
            fields += [''] * (3 - len(fields))
            rgb_raw, time_raw, ledn_raw = fields

            rgb = rgb_raw if rgb_raw else '#000000'
            try:
                time_ = float(time_raw) if time_raw else 0.0
            except ValueError as e:
                raise ValueError("bad fade time %r" % (time_raw,)) from e
            try:
                ledn = int(float(ledn_raw)) if ledn_raw else 0
            except ValueError as e:
                raise ValueError("bad led number %r" % (ledn_raw,)) from e
            millis = int(time_ * 1000)
            color = {
                'rgb': rgb,
                'time': time_,
                'ledn': ledn,
                'millis': millis
            }

            colorlist.append(color)

        return num_repeats, colorlist

    def server_tickle(
        self,
        enable,
        timeout_millis=0,
        stay_lit=False,
        start_pos=0,
        end_pos=16
    ):
        """Enable/disable servertickle / serverdown watchdog
        :param: enable: Set True to enable serverTickle
        :param: timeout_millis: millisecs until servertickle is triggered
        :param: stay_lit: Set True to keep current color of blink(1), False to turn off
        :param: start_pos: Sub-pattern start position in whole color pattern
        :param: end_pos: Sub-pattern end position in whole color pattern
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        # Returns '' rather than raising on a closed device, unlike the rest
        # of the class. Kept for callers that branch on it.
        if self.dev is None:
            return ''

        en = int(enable is True)
        timeout_time = int(timeout_millis / 10)
        th = (timeout_time & 0xff00) >> 8
        tl = timeout_time & 0x00ff
        st = int(stay_lit is True)
        buf = [REPORT_ID, ord('D'), en, th, tl, st, start_pos, end_pos, 0]
        self.write(buf)


@contextmanager
def blink1(switch_off: bool = True,
           gamma: Sequence[float] | None = None,
           white_point: WhitePoint | None = None,
           serial_number: str | None = None,
           pattern_lines: int | None = None) -> Iterator[Blink1]:
    """Context manager which automatically shuts down the Blink(1)
    after use.
    :param switch_off: turn blink(1) off when exiting context
    :param gamma: set gamma curve (as tuple)
    :param white_point: set white point (as tuple)
    :param serial_number: serial number of blink(1) to open, otherwise first found
    :param pattern_lines: size of color pattern memory, detected if None
    """
    b1 = Blink1(gamma=gamma, white_point=white_point, serial_number=serial_number,
                pattern_lines=pattern_lines)
    try:
        yield b1
    finally:
        # The body may have closed the device itself, so off() is conditional.
        if switch_off and b1.dev is not None:
            b1.off()
        b1.close()
