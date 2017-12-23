"""
blink1.py -- blink(1) Python library using python hidapi

All platforms:
 % pip install blink1

"""
import logging
import time
import sys
from contextlib import contextmanager
import webcolors
import hid
#from builtins import str as text

# from .kelvin import kelvin_to_rgb, COLOR_TEMPERATURES


class Blink1ConnectionFailed(RuntimeError):
    """Raised when we cannot connect to a Blink(1)
    """

class InvalidColor(ValueError):
    """Raised when the user requests an implausible colour
    """


log = logging.getLogger(__name__)
#logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
#getattr(log, loglevel.upper())

DEFAULT_GAMMA = (2, 2, 2)
DEFAULT_WHITE_POINT = (255, 255, 255)

REPORT_ID = 0x01
VENDOR_ID = 0x27b8
PRODUCT_ID = 0x01ed

class ColorCorrect(object):
    """Apply a gamma correction to any selected RGB color, see:
    http://en.wikipedia.org/wiki/Gamma_correction
    """
    def __init__(self, gamma, white_point):
        """
        :param gamma: Tuple of r,g,b gamma values
        :param white_point: White point expressed as (r,g,b), integer color temperature (in Kelvin) or a string value.

        All gamma values should be 0 > x >= 1
        """
        self.gamma = gamma

        if isinstance(white_point, str):
            kelvin = COLOR_TEMPERATURES[white_point]
            self.white_point = kelvin_to_rgb(kelvin)
        elif isinstance(white_point,(int,float)):
            self.white_point = kelvin_to_rgb(white_point)
        else:
            self.white_point = white_point

    @staticmethod
    def gamma_correct(gamma, white, luminance):
        return round(white * (luminance / 255) ** gamma)

    def __call__(self, r, g, b):
        color = [r,g,b]
        return tuple(self.gamma_correct(g, w, l) for (g, w, l) in zip(self.gamma, self.white_point, color) )


class Blink1:
    """Light controller class, sends messages to the blink(1) and blink(1) mk2 via USB HID.
    """
    def __init__(self, serial_number=None, gamma=None, white_point=None):
        """
        :param serial_number: serial number of blink(1) to open, otherwise first found
        :param gamma: Triple of gammas for each channel e.g. (2, 2, 2)
        """
        self.cc = ColorCorrect(
            gamma=(gamma or DEFAULT_GAMMA),
            white_point=(white_point or DEFAULT_WHITE_POINT)
        )
        self.dev = self.find(serial_number)

    def close(self):
        self.dev = None

    @staticmethod
    def find(serial_number=None):
        """
        Find a praticular blink(1) device, or the first one
        :param serial_number: serial number of blink(1) device (from Blink1.list())
        """
        try:
            hidraw = hid.device(VENDOR_ID,PRODUCT_ID,serial_number)
            hidraw.open(VENDOR_ID,PRODUCT_ID,serial_number)
            # hidraw = hid.device(VENDOR_ID,PRODUCT_ID,unicode(serial_number))
            # hidraw.open(VENDOR_ID,PRODUCT_ID,unicode(serial_number))
#        except IOError as e:
#            raise Blink1ConnectionFailed(e)
        except OSError as e:
            hidraw = None

        return hidraw

    @staticmethod
    def list():
        """
        List blink(1) devices connected, by serial number
        :return: List of blink(1) device serial numbers
        """
        try:
            devs = hid.enumerate(VENDOR_ID,PRODUCT_ID)
            serials = map(lambda d:d.get('serial_number'), devs)
            return serials
        except IOError as e:
            return []

    def notfound(self):
        return None  # fixme what to do here

    def write(self,buf):
        """
        Write command to blink(1)
        Send USB Feature Report 0x01 to blink(1) with 8-byte payload
        Note: arg 'buf' must be 8 bytes or bad things happen
        """
        log.debug("blink1write:" + ",".join('0x%02x' % v for v in buf))
        self.dev.send_feature_report(buf)

    def read(self):
        """
        Read command result from blink(1)
        Receive USB Feature Report 0x01 from blink(1) with 8-byte payload
        Note: buf must be 8 bytes or bad things happen
        """
        buf = self.dev.get_feature_report(REPORT_ID,9)
        log.debug("blink1read: " + ",".join('0x%02x' % v for v in buf))
        return buf

    def fade_to_rgb_uncorrected(self, fade_milliseconds, red, green, blue, led_number=0):
        """
        Command blink(1) to fade to RGB color, no color correction applied.
        """
        action = ord('c')
        fade_time = int(fade_milliseconds / 10)
        th = (fade_time & 0xff00) >> 8
        tl = fade_time & 0x00ff
        buf = [REPORT_ID, action, int(red), int(green), int(blue), th, tl, led_number, 0]
        self.write( buf )

    def fade_to_rgb(self,fade_milliseconds, red, green, blue, led_number=0):
        r, g, b = self.cc(red, green, blue)
        return self.fade_to_rgb_uncorrected(fade_milliseconds, r, g, b, led_number)

    @staticmethod
    def color_to_rgb(color):
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


    def fade_to_color(self, fade_milliseconds, color):
        """
        Fade the light to a known colour in a
        :param fade_milliseconds: Duration of the fade in milliseconds
        :param color: Named color to fade to
        :return: None
        """
        red, green, blue = self.color_to_rgb(color)

        return self.fade_to_rgb(fade_milliseconds, red, green, blue)

    def off(self):
        """Switch the blink(1) off instantly
        """
        self.fade_to_color(0, 'black')

    def get_version(self):
        """Get blink(1) firmware version
        """
        if ( self.dev == None ): return ''
        buf = [REPORT_ID, ord('v'), 0, 0, 0, 0, 0, 0, 0]
        self.write(buf)
        time.sleep(.05)
        version_raw = self.read()
        version = (version_raw[3] - ord('0')) * 100 + (version_raw[4] - ord('0'))
        return str(version)

    def get_serial_number(self):
        """Get blink(1) serial number
        """
        return self.dev.get_serial_number_string()
        # return usb.util.get_string(self.dev, 256, 3)


@contextmanager
def blink1(switch_off=True, gamma=None, white_point=None):
    """Context manager which automatically shuts down the Blink(1)
    after use.
    """
    # b1 = Blink1(gamma=gamma, white_point=white_point)
    b1 = Blink1()
    yield b1
    if switch_off:
        b1.off()
    b1.close()
