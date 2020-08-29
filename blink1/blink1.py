# -*- coding: utf-8 -*-
"""
blink1.py -- blink(1) Python library using python hidapi

All platforms:
 % pip3 install blink1

"""
import logging
import time
from contextlib import contextmanager
import webcolors
import hid
import os
# from builtins import str as text

from .kelvin import kelvin_to_rgb, COLOR_TEMPERATURES


class Blink1ConnectionFailed(RuntimeError):
    """Raised when we cannot connect to a Blink(1)
    """


class InvalidColor(ValueError):
    """Raised when the user requests an implausible colour
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


class ColorCorrect(object):
    """Apply a gamma correction to any selected RGB color, see:
    http://en.wikipedia.org/wiki/Gamma_correction
    """
    def __init__(self, gamma, white_point):
        """
        :param gamma: Tuple of r,g,b gamma values
        :param white_point: White point expressed as (r,g,b), integer color
            temperature (in Kelvin) or a string value.

        All gamma values should be 0 > x >= 1
        """

        self.gamma = gamma

        if isinstance(white_point, str):
            kelvin = COLOR_TEMPERATURES[white_point]
            self.white_point = kelvin_to_rgb(kelvin)
        elif isinstance(white_point, (int, float)):
            self.white_point = kelvin_to_rgb(white_point)
        else:
            self.white_point = white_point

    @staticmethod
    def gamma_correct(gamma, white, luminance):
        return round(white * (luminance / 255.0) ** gamma)

    def __call__(self, r, g, b):
        color = [r, g, b]
        return tuple(
            self.gamma_correct(g, w, l)
            for (g, w, l) in zip(self.gamma, self.white_point, color)
        )


class Blink1(object):
    """Light controller class, sends messages to the blink(1) via USB HID.
    """
    def __init__(self, serial_number=None, gamma=None, white_point=None):
        """
        :param serial_number: serial number of blink(1) to open, otherwise first found
        :param gamma: Triple of gammas for each channel e.g. (2, 2, 2)
        """
        self.cc = ColorCorrect(
            gamma=gamma or DEFAULT_GAMMA,
            white_point=(white_point or DEFAULT_WHITE_POINT)
        )
        self.dev = self.find(serial_number)
        if self.dev is None:
            print("wtf")

    def close(self):
        self.dev.close()
        self.dev = None

    @staticmethod
    def find(serial_number=None):
        """ Find a praticular blink(1) device, or the first one
        :param serial_number: serial number of blink(1) device (from Blink1.list())
        :raises: Blink1ConnectionFailed: if blink(1) is not present
        """
        try:
            hidraw = hid.device(VENDOR_ID, PRODUCT_ID, serial_number)
            hidraw.open(VENDOR_ID, PRODUCT_ID, serial_number)
            # hidraw = hid.device(VENDOR_ID,PRODUCT_ID,unicode(serial_number))
            # hidraw.open(VENDOR_ID,PRODUCT_ID,unicode(serial_number))
        except IOError as e:  # python2
            raise Blink1ConnectionFailed(e)
            # hidraw = None
        except OSError as e:  # python3
            raise Blink1ConnectionFailed(e)
            # hidraw = None

        return hidraw

    @staticmethod
    def list():
        """ List blink(1) devices connected, by serial number
        :return: List of blink(1) device serial numbers
        """
        try:
            devs = hid.enumerate(VENDOR_ID, PRODUCT_ID)
            serials = list(map(lambda d: d.get('serial_number'), devs))
            return serials
        except IOError:
            return []

    @staticmethod
    def notfound():
        return None  # fixme what to do here

    def write(self, buf):
        """ Write command to blink(1), low-level internal use
        Send USB Feature Report 0x01 to blink(1) with 8-byte payload
        Note: arg 'buf' must be 8 bytes or bad things happen
        :raises: Blink1ConnectionFailed if blink(1) is disconnected
        """
        log.debug("blink1write:" + ",".join('0x%02x' % v for v in buf))
        rc = self.dev.send_feature_report(buf)
        # return self.dev.send_feature_report(buf)
        if rc != REPORT_SIZE:
            raise Blink1ConnectionFailed(
                "write returned %d instead of %d" % (rc, REPORT_SIZE)
            )

    def read(self):
        """ Read command result from blink(1), low-level internal use
        Receive USB Feature Report 0x01 from blink(1) with 8-byte payload
        Note: buf must be 8 bytes or bad things happen
        """
        buf = self.dev.get_feature_report(REPORT_ID, 9)
        log.debug("blink1read: " + ",".join('0x%02x' % v for v in buf))
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
        buf = [REPORT_ID, action, int(red), int(green), int(blue), th, tl, ledn, 0]
        self.write(buf)

    def fade_to_rgb(self, fade_milliseconds, red, green, blue, ledn=0):
        """ Command blink(1) to fade to RGB color
        :param fade_milliseconds: millisecs duration of fade
        :param red: 0-255
        :param green: 0-255
        :param blue: 0-255
        :param ledn: which LED to control (0=all, 1=LED A, 2=LED B)
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        r, g, b = self.cc(red, green, blue)
        return self.fade_to_rgb_uncorrected(fade_milliseconds, r, g, b, ledn)

    @staticmethod
    def color_to_rgb(color):
        """ Convert color name or hexcode to (r,g,b) tuple
        :param color: a color string, e.g. "#FF00FF" or "red"
        :raises: InvalidColor: if color string is bad
        """
        if isinstance(color, tuple):
            return color
        if color.startswith('#'):
            try:
                return webcolors.hex_to_rgb(color)
            except ValueError:
                raise InvalidColor(color)

        try:
            return webcolors.name_to_rgb(color)
        except ValueError:
            raise InvalidColor(color)

    def fade_to_color(self, fade_milliseconds, color, ledn=0):
        """ Fade the light to a known colour
        :param fade_milliseconds: Duration of the fade in milliseconds
        :param color: Named color to fade to (e.g. "#FF00FF", "red")
        :param ledn: which led to control
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        red, green, blue = self.color_to_rgb(color)

        return self.fade_to_rgb(fade_milliseconds, red, green, blue, ledn)

    def off(self):
        """ Switch the blink(1) off instantly
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        self.fade_to_color(0, 'black')

    def get_version(self):
        """ Get blink(1) firmware version
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        buf = [REPORT_ID, ord('v'), 0, 0, 0, 0, 0, 0, 0]
        self.write(buf)
        time.sleep(.05)
        version_raw = self.read()
        version = (version_raw[3] - ord('0')) * 100 + (version_raw[4] - ord('0'))
        return str(version)

    def get_serial_number(self):
        """ Get blink(1) serial number
        :return blink(1) serial number as string
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        return self.dev.get_serial_number_string()

    def play(self, start_pos=0, end_pos=0, count=0):
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
            int(count),
            0,
            0,
            0
        ]
        self.write(buf)

    def stop(self):
        """ Stop internal color pattern playing
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        if self.dev is None:
            return False

        buf = [REPORT_ID, ord('p'), 0, 0, 0, 0, 0, 0, 0]
        self.write(buf)

    def save_pattern(self):
        """ Save internal RAM pattern to flash
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        buf = [REPORT_ID, ord('W'), 0xBE, 0xEF, 0xCA, 0xFE, 0, 0, 0]
        self.write(buf)

    def set_ledn(self, ledn=0):
        """ Set the 'current LED' value for writePatternLine
        :param ledn: LED to adjust, 0=all, 1=LEDA, 2=LEDB
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        buf = [REPORT_ID, ord('l'), ledn, 0, 0, 0, 0, 0, 0]
        self.write(buf)

    def write_pattern_line(self, step_milliseconds, color, pos, ledn=0):
        """ Write a color & step time color pattern line to RAM
        :param step_milliseconds: how long for this pattern line to take
        :param color: LED color
        :param pos: color pattern line number (0-15)
        :param ledn: LED number to adjust, 0=all, 1=LEDA, 2=LEDB
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        self.set_ledn(ledn)
        red, green, blue = self.color_to_rgb(color)
        r, g, b = self.cc(red, green, blue)
        step_time = int(step_milliseconds / 10)
        th = (step_time & 0xff00) >> 8
        tl = step_time & 0x00ff
        buf = [REPORT_ID, ord('P'), int(r), int(g), int(b), th, tl, pos, 0]
        self.write(buf)

    def read_pattern_line(self, pos):
        """ Read a color pattern line at position
        :param pos: pattern line to read
        :return pattern line data as tuple (r,g,b, step_millis) or False on err
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        buf = [REPORT_ID, ord('R'), 0, 0, 0, 0, 0, int(pos), 0]
        self.write(buf)
        buf = self.read()

        r, g, b = buf[2:4]

        step_millis = ((buf[5] << 8) | buf[6]) * 10
        return r, g, b, step_millis

    def read_pattern(self):
        """ Read the entire color pattern
        :return List of pattern line tuples
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        pattern = []
        for i in range(0, 16):  # FIXME: adjustable for diff blink(1) models
            pattern.append(self.read_pattern_line(i))
        return pattern

    def clear_pattern(self):
        """ Clear entire color pattern in blink(1)
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        for i in range(0, 16):  # FIXME: pattern length
            self.write_pattern_line(0, 'black', i)

    def play_pattern(self, pattern_str, onDevice=True):
        """ Play a Blink1Control-style pattern string
        :param pattern_str: The Blink1Control-style pattern string to play
        :param onDevice: True (default) to run pattern on blink(1),
                         otherwise plays in Python process
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
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

        colorlist += [empty_color] * (32 - len(colorlist))

        for i, c in enumerate(colorlist):
            self.write_pattern_line(c['millis'], c['rgb'], i, c['ledn'])

        return self.play(count=num_repeats)

    def play_pattern_local(self, pattern_str):
        """ Play a Blink1Control pattern string in Python process
            (plays in blink1-python, so blocks)
        :param pattern_str: The Blink1Control-style pattern string to play
        :raises: Blink1ConnectionFailed: if blink(1) is disconnected
        """
        num_repeats, colorlist = self.parse_pattern(pattern_str)
        if num_repeats == 0:
            num_repeats = -1

        while num_repeats:
            num_repeats -= 1

            for c in colorlist:
                self.fade_to_color(c['millis'], c['rgb'], c['ledn'])
                time.sleep(c['time'])

    @staticmethod
    def parse_pattern(pattern_str):
        """ Parse a Blink1Control pattern string to a list of pattern lines
            e.g. of the form '10,#ff00ff,0.1,0,#00ff00,0.1,0'
        :param pattern_str: The Blink1Control-style pattern string to parse
        :returns: an list of dicts of the parsed out pieces
        """
        pattparts = pattern_str.replace(' ', '').split(',')
        num_repeats = int(pattparts[0])  # FIXME
        pattparts = pattparts[1:]

        colorlist = []
        dpattparts = dict(enumerate(pattparts))  # lets us use .get(i,'default')
        for i in range(0, len(pattparts), 3):
            rgb = dpattparts.get(i + 0, '#000000')
            time_ = float(dpattparts.get(i + 1, 0.0))
            ledn = int(dpattparts.get(i + 2, 0))
            # set default if empty string
            rgb = rgb if rgb else '#000000'  # sigh
            time_ = time_ if time_ else 0.0  # sigh
            ledn = ledn if ledn else 0  # sigh
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
def blink1(switch_off=True, gamma=None, white_point=None):
    """Context manager which automatically shuts down the Blink(1)
    after use.
    :param switch_off: turn blink(1) off when existing context
    :param gamma: set gamma curve (as tuple)
    :param white_point: set white point (as tuple)
    """
    b1 = Blink1(gamma=gamma, white_point=white_point)
    yield b1
    if switch_off:
        b1.off()
    b1.close()
