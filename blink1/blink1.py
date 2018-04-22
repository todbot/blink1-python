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
import os
#from builtins import str as text

from .kelvin import kelvin_to_rgb, COLOR_TEMPERATURES


class Blink1ConnectionFailed(RuntimeError):
    """Raised when we cannot connect to a Blink(1)
    """

class InvalidColor(ValueError):
    """Raised when the user requests an implausible colour
    """


log = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s:%(message)s',
                    level=logging.DEBUG if os.getenv('DEBUGBLINK1') else logging.INFO )


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
        self.dev.close()
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
            serials = list(map(lambda d:d.get('serial_number'), devs))
            return serials
        except IOError as e:
            return []

    def notfound(self):
        return None  # fixme what to do here

    def write(self,buf):
        """
        Write command to blink(1), low-level internal use
        Send USB Feature Report 0x01 to blink(1) with 8-byte payload
        Note: arg 'buf' must be 8 bytes or bad things happen
        """
        log.debug("blink1write:" + ",".join('0x%02x' % v for v in buf))
        self.dev.send_feature_report(buf)

    def read(self):
        """
        Read command result from blink(1), low-level internal use
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
        """
        Convert color name or hexcode to (r,g,b) tuple
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
        :return blink(1) serial number as string
        """
        return self.dev.get_serial_number_string()
        # return usb.util.get_string(self.dev, 256, 3)

    def play(self, start_pos=0, end_pos=0, count=0):
        """Play internal color pattern
        :param start_pos: pattern line to start from
        :param end_pos: pattern line to end at (but not play)
        :param count: number of times to play, 0=play forever
        """
        if ( self.dev == None ): return ''
        buf = [REPORT_ID, ord('p'), 1, start_pos, end_pos, count, 0, 0, 0]
        return self.write(buf);

    def stop(self):
        """Stop internal color pattern playing
        """
        if ( self.dev == None ): return ''
        buf = [REPORT_ID, ord('p'), 0, 0, 0, 0, 0, 0, 0]
        return self.write(buf);

    def savePattern(self):
        """Save internal RAM pattern to flash 
        """
        if ( self.dev == None ): return ''
        buf = [REPORT_ID, ord('W'), 0xBE, 0xEF, 0xCA, 0xFE, 0, 0, 0]
        return self.write(buf);

    def setLedN(self, led_number=0):
        """Set the 'current LED' value for writePatternLine
        :param led_number: LED to adjust, 0=all, 1=LEDA, 2=LEDB
        """
        if ( self.dev == None ): return ''
        buf = [REPORT_ID, ord('l'), led_number, 0,0,0,0,0,0]
        self.write(buf)        
        
    def writePatternLine(self, fade_milliseconds, color, pos, led_number=0):
        """Write a color & fadetime color pattern line to RAM 
        :param led_number: LED to adjust, 0=all, 1=LEDA, 2=LEDB
        """
        if ( self.dev == None ): return ''
        self.setLedN(led_number)
        red, green, blue = self.color_to_rgb(color)
        r, g, b = self.cc(red, green, blue)
        fade_time = int(fade_milliseconds / 10)
        th = (fade_time & 0xff00) >> 8
        tl = fade_time & 0x00ff
        buf = [REPORT_ID, ord('P'), r,g,b, th,tl, pos, 0]
        return self.write(buf);

    def readPatternLine(self, pos):
        """Read a color pattern line at position
        :param pos: pattern line to read
        :return pattern line data as tuple (r,g,b, fade_millis)
        """
        if ( self.dev == None ): return ''
        buf = [REPORT_ID, ord('R'), 0, 0, 0, 0, 0, pos, 0]
        self.write(buf)
        buf = self.read()
        (r,g,b) = (buf[2],buf[3],buf[4])
        fade_millis = ((buf[5] << 8) | buf[6]) * 10
        return (r,g,b,fade_millis)
    
    def readPattern(self):
        """Read the entire color pattern
        :return List of pattern line tuples
        """
        if ( self.dev == None ): return ''
        pattern=[]
        for i in range(0,16):    # FIXME: adjustable for diff blink(1) models
            pattern.append( self.readPatternLine(i) )
        return pattern

    def serverTickle(self, enable, timeout_millis, stay_lit=False):
        """Enable/disable servertickle / serverdown watchdog
        :param: enable: Set True to enable serverTickle
        :param: timeout_millis: millisecs until servertickle is triggered
        :param: stay_lit: Set True to keep current color of blink(1), False to turn off
        """
        if ( self.dev == None ): return ''
        en = int(enable == True)
        timeout_time = tmieout_millis/10
        th = (timeout_time & 0xff00) >>8
        tl = timeout_time & 0x00ff
        st = int(stay_lit == True)
        buf = [REPORT_ID, ord('D'), en, th, tl, st, 0, 0, 0]
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
