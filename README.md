

Python Blink(1) library
========================

Official Python library for blink(1) USB RGB LED notification devices
https://blink1.thingm.com/

* [About this library](#about-this-library)
* [Installation](#installation)
* [Example Code and Installed scripts](#example-code-and-installed-scripts)
* [OS-specific notes](#os-specific-notes)
   * [Linux:](#linux)
   * [Mac OS X:](#mac-os-x)
   * [Windows:](#windows)
* [Use](#use)
   * [Colors](#colors)
   * [Pattern playing](#pattern-playing)
   * [Servertickle watchdog](#servertickle-watchdog)
   * [Gamma correction](#gamma-correction)
   * [White point correction](#white-point-correction)
* [API reference](#api-reference)
* [Developer installation](#developer-installation)

## About this library

Features of this library:

* Test coverage on all library components
* Python 3.x and Python 2.7.x compatible
* Automatic installation via Python Package Index
* High level control over the blink(1)
* Single implementation with `cython-hidapi` USB HID API (PyUSB cannot access HID devices on all OSes)

This library lives at https://github.com/todbot/blink1-python

Originally written by @salimfadhley, at https://github.com/salimfadhley/blink1/tree/master/python/pypi.
Moved to this repository and rewritten for `cython-hidapi` by @todbot.

## Installation

Use the `pip` utility to fetch the latest release of this package and any
additional components required in a single step:
```
  pip install blink1
```

## Example Code and Installed scripts
Two command-line scripts `blink1-shine` and `blink1-flash` are installed when this library is installed.
* `blink1-shine` – Tell the blink(1) to be specifc steady color
* `blink1-flash` – Flash the blink(1) two different colors at a specific rate

For examples, see the [`blink1_demo`](./blink1_demo/) directory for several examples on how to use this library.

## OS-specific notes
The `blink1-python` library relies on [cython-hidapi](https://github.com/trezor/cython-hidapi) for USB HID access.  This package may require a C compiler and attendant utilities to be installed before installing this library.

### Linux:
The following extra packages must be installed:
```
  sudo apt-get install python-dev libusb-1.0-0-dev libudev-dev
```
And udev rules for non-root user access to blink(1) devices:
```
  echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="27b8", ATTRS{idProduct}=="01ed", MODE:="666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/51-blink1.rules
  sudo udevadm control --reload
  sudo udevadm trigger
```

### Mac OS X:
Install [Xcode](https://developer.apple.com/xcode/_) with command-line tools.

### Windows:
You will need [Microsoft Visual C++ Compiler for Python 2.7](http://aka.ms/vcpython27)

## Use

The simplest way to use this library is via a context manager.
```
  import time
  from blink1.blink1 import blink1

  with blink1() as b1:
    b1.fade_to_color(100, 'navy')
    time.sleep(10)
```

When the blink1() block exits the light is automatically switched off.
It is also possible to access the exact same set of functions without the context manager:
```
  import time
  from blink1.blink1 import Blink1

  b1 = Blink1()
  b1.fade_to_rgb(1000, 64, 64, 64)
  time.sleep(3)
  b1.fade_to_rgb(1000, 255, 255, 255)
```

Unlike the context manager, this demo will leave the blink(1) open at the end of execution.
To close it, use the `b1.close()` method.

To list all connected blink(1) devices:
```
  from blink1.blink1 import Blink1
  blink1_serials = Blink1.list()
  print("blink(1) devices found: " + ','.join(blink1_serials))
```

To open a particular blink(1) device by serial number, pass in its serial number as a Unicode string:
```
  from blink1.blink1 import blink1
  blink1 = Blink1(serial_number=u'20002345')
  blink1.fade_to_rgb(1000, 255,0,255)
  blink1.close()
```

### Colors

There are a number of ways to specify colors in this library:
```
  blink1.fade_to_color(1000, '#ffffff') # Hexdecimal RGB as a string
  blink1.fade_to_color(1000, 'green') # Named color - any color name understood by css3
  blink1.fade_to_color(1000, (22,33,44) # RGB as a tuple. Luminance values are 0 <= lum <= 255
```
Attempting to select a color outside the plausible range will generate an InvalidColor exception.


### Pattern playing

The blink(1) device has a 16-line non-volatile color pattern memory.
This color pattern plays automatically if power is applied but not connected to a computer.
You can also trigger this pattern (or sub-patterns) over USB,
leaving your application free to do other things besides blink lights.

Each line in the color pattern consists of an R,G,B triplet and a fade time to reach that color.

To play the pattern in blink(1) or sub-patterns:
```
blink1.play()  # play entire color pattern, infinitely looped
blink1.stop()  # stop a color pattern playing (if playing)

blink1.play(2,3, count=7)  # play color pattern lines 2,3 in a loop 7 times
```

To alter the lines of the pattern memory:
```
# write 100msec fades to green then yellow then black at lines 3,4,5
blink1.write_pattern_line( 100, 'green',  3)
blink1.write_pattern_line( 100, 'yellow', 4)
blink1.write_pattern_line( 100, 'black',  5)

blink1.play( 3,5, 4)  # play that sub-loop 4 times
```

To save the pattern to non-volatile memory (overwriting the factory pattern):
```
blink1.savePattern()
```

To quickly play a pattern in Blink1Control-style string format:
```
# play purple on LED1 in 300ms, green on LED2 in 100ms, then swap, for 10 times
pattern_str = '10, #ff00ff,0.3,1, #00ff00,0.1,2,  #ff00ff,0.3,2, #00ff00,0.1,1'
blink1.play_pattern(pattern_str)
# wait 5 seconds while the pattern plays on the blink1
# (or go do something more useful)
time.sleep(5.0)
# flash red-off 5 times fast on all LEDs
blink1.play_pattern('5, #FF0000,0.2,0,#000000,0.2,0')
```

### Servertickle watchdog
blink(1) also has a "watchdog" of sorts called "servertickle".
When enabled, you must periodically send it to the blink(1) or it will
trigger, playing the stored color pattern.  This is useful to announce
a computer that has crashed.  The blink(1) will flash on its own until
told otherwise.

To use, enable severtickle with a timeout value (max timeout 62 seconds):
```
blink1.server_tickle(enable=True, timeout_millis=2000)
```


### Gamma correction

The context manager supports a ''gamma'' argument which allows you to supply a per-channel gamma correction value.
```
  from blink1.blink1 import blink1

  with blink1(gamma=(2, 2, 2)) as b1:
    b1.fade_to_color(100, 'pink')
    time.sleep(10)
```
This example provides a gamma correction of 2 to each of the three colour channels.

Higher values of gamma make the blink(1) appear more colorful but decrease the brightness of colours.

### White point correction

The human eye's perception of color can be influenced by ambient lighting. In some circumstances it may be desirable
to apply a small color correction in order to make colors appear more accurate. For example, if we were operating
the blink(1) in a room lit predominantly by candle-light:
```
  with blink1(white_point='candle', switch_off) as b1:
    b1.fade_to_color(100, 'white')
```
Viewed in daylight this would make the Blink(1) appear yellowish, however in a candle-lit room this would be perceived
as a more natural white. If we did not apply this kind of color correction the Blink(1) would appear blueish.

The following values are acceptable white-points:

* Any triple of (r,g,b). Each 0 <= luminance <= 255
* Any color_temperature expressed as an integer or float in Kelvin
* A color temperature name.

The library supports the following temperature names:

* candle
* sunrise
* incandescent
* tungsten
* halogen
* sunlight
* overcast
* shade
* blue-sky

## API reference
```
Help on class Blink1 in blink1.blink1:

blink1.blink1.Blink1 = class Blink1
 |  Light controller class, sends messages to the blink(1) via USB HID.
 |  
 |  Methods defined here:
 |  
 |  __init__(self, serial_number=None, gamma=None, white_point=None)
 |      :param serial_number: serial number of blink(1) to open, otherwise first found
 |      :param gamma: Triple of gammas for each channel e.g. (2, 2, 2)
 |  
 |  clear_pattern(self)
 |      Clear entire color pattern in blink(1)
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  close(self)
 |  
 |  fade_to_color(self, fade_milliseconds, color, ledn=0)
 |      Fade the light to a known colour
 |      :param fade_milliseconds: Duration of the fade in milliseconds
 |      :param color: Named color to fade to (e.g. "#FF00FF", "red")
 |      :param ledn: which led to control
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  fade_to_rgb(self, fade_milliseconds, red, green, blue, ledn=0)
 |      Command blink(1) to fade to RGB color
 |      :param fade_milliseconds: millisecs duration of fade
 |      :param red: 0-255
 |      :param green: 0-255
 |      :param blue: 0-255
 |      :param ledn: which LED to control (0=all, 1=LED A, 2=LED B)
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  fade_to_rgb_uncorrected(self, fade_milliseconds, red, green, blue, ledn=0)
 |      Command blink(1) to fade to RGB color, no color correction applied.
 |      :throws: Blink1ConnectionFailed if blink(1) is disconnected
 |  
 |  get_serial_number(self)
 |      Get blink(1) serial number
 |      :return blink(1) serial number as string
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  get_version(self)
 |      Get blink(1) firmware version
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  notfound(self)
 |  
 |  off(self)
 |      Switch the blink(1) off instantly
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  play(self, start_pos=0, end_pos=0, count=0)
 |      Play internal color pattern
 |      :param start_pos: pattern line to start from
 |      :param end_pos: pattern line to end at
 |      :param count: number of times to play, 0=play forever
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  play_pattern(self, pattern_str, onDevice=True)
 |      Play a Blink1Control-style pattern string
 |      :param pattern_str: The Blink1Control-style pattern string to play
 |      :param onDevice: True (default) to run pattern on blink(1),
 |                       otherwise plays in Python process
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  play_pattern_local(self, pattern_str)
 |      Play a Blink1Control pattern string in Python process
 |          (plays in blink1-python, so blocks)
 |      :param pattern_str: The Blink1Control-style pattern string to play
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  read(self)
 |      Read command result from blink(1), low-level internal use
 |      Receive USB Feature Report 0x01 from blink(1) with 8-byte payload
 |      Note: buf must be 8 bytes or bad things happen
 |  
 |  read_pattern(self)
 |      Read the entire color pattern
 |      :return List of pattern line tuples
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  read_pattern_line(self, pos)
 |      Read a color pattern line at position
 |      :param pos: pattern line to read
 |      :return pattern line data as tuple (r,g,b, step_millis) or False on err
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  save_pattern(self)
 |      Save internal RAM pattern to flash
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  server_tickle(self, enable, timeout_millis=0, stay_lit=False, start_pos=0, end_pos=16)
 |      Enable/disable servertickle / serverdown watchdog
 |      :param: enable: Set True to enable serverTickle
 |      :param: timeout_millis: millisecs until servertickle is triggered
 |      :param: stay_lit: Set True to keep current color of blink(1), False to turn off
 |      :param: start_pos: Sub-pattern start position in whole color pattern
 |      :param: end_pos: Sub-pattern end position in whole color pattern
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  set_ledn(self, ledn=0)
 |      Set the 'current LED' value for writePatternLine
 |      :param ledn: LED to adjust, 0=all, 1=LEDA, 2=LEDB
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  stop(self)
 |      Stop internal color pattern playing
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  write(self, buf)
 |      Write command to blink(1), low-level internal use
 |      Send USB Feature Report 0x01 to blink(1) with 8-byte payload
 |      Note: arg 'buf' must be 8 bytes or bad things happen
 |      :return: number of bytes written or -1 if failure
 |  
 |  write_pattern_line(self, step_milliseconds, color, pos, ledn=0)
 |      Write a color & step time color pattern line to RAM
 |      :param step_milliseconds: how long for this pattern line to take
 |      :param color: LED color
 |      :param pos: color pattern line number (0-15)
 |      :param ledn: LED number to adjust, 0=all, 1=LEDA, 2=LEDB
 |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
 |  
 |  ----------------------------------------------------------------------
 |  Static methods defined here:
 |  
 |  color_to_rgb(color)
 |      Convert color name or hexcode to (r,g,b) tuple
 |      :param color: a color string, e.g. "#FF00FF" or "red"
 |      :raises: InvalidColor: if color string is bad
 |  
 |  find(serial_number=None)
 |      Find a praticular blink(1) device, or the first one
 |      :param serial_number: serial number of blink(1) device (from Blink1.list())
 |      :raises: Blink1ConnectionFailed: if blink(1) is not present
 |  
 |  list()
 |      List blink(1) devices connected, by serial number
 |      :return: List of blink(1) device serial numbers
 |  
 |  parse_pattern(pattern_str)
 |      Parse a Blink1Control pattern string to a list of pattern lines
 |          e.g. of the form '10,#ff00ff,0.1,0,#00ff00,0.1,0'
 |      :param pattern_str: The Blink1Control-style pattern string to parse
 |      :returns: an list of dicts of the parsed out pieces
```


## Developer installation

Having checked out the `blink1-python` library, cd to its directory and run the setup script:
```
  git clone https://github.com/todbot/blink1-python
  cd blink1-python
  python3 setup.py develop
  python3 ./blink1_demo/demo1.py
```
or
```
  pip3 install --editable .
```
You can now use the `blink1` package on your system and edit it.

To get internal blink1 library debug, messages set the environment variable `DEBUGBLINK1`:
```
DEBUGBLINK1=1 python3 ./blink1_demo/demo1.py
```

To uninstall the development version:
```
  python3 setup.py develop --uninstall
```
