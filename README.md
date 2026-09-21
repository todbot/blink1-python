Python Blink(1) library
========================

Official Python library for blink(1) USB RGB LED notification devices
https://blink1.thingm.com/

[![CI](https://github.com/todbot/blink1-python/actions/workflows/ci.yml/badge.svg)](https://github.com/todbot/blink1-python/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/blink1.svg)](https://pypi.org/project/blink1/)

* [About this library](#about-this-library)
* [Installation](#installation)
* [Example Code and Installed scripts](#example-code-and-installed-scripts)
* [OS-specific notes](#os-specific-notes)
   * [Linux:](#linux)
   * [Mac OS X:](#mac-os-x)
   * [Windows:](#windows)
* [Use](#use)
   * [Import styles](#import-styles)
   * [Colors](#colors)
   * [Pattern playing](#pattern-playing)
   * [Servertickle watchdog](#servertickle-watchdog)
   * [Gamma correction](#gamma-correction)
   * [White point correction](#white-point-correction)
* [API reference](#api-reference)
* [Developer installation](#developer-installation)

## About this library

Features of this library:

* Test suite that runs without a blink(1) attached, plus hardware tests
* Python 3.9+
* Automatic installation via Python Package Index
* High level control over the blink(1)
* Type hints throughout, with a `py.typed` marker so they reach your
  type checker
* Single implementation with `cython-hidapi` USB HID API (PyUSB cannot access HID devices on all OSes)

This library lives at https://github.com/todbot/blink1-python

Changes are recorded in
[CHANGELOG.md](https://github.com/todbot/blink1-python/blob/main/CHANGELOG.md). If you are
upgrading from 0.4.0, read its "Changed" section first: 1.0.0 has five
behavior changes, including colors outside 0-255 now raising
`InvalidColor`, and a corrected value for the `fluorescent` white point.

Originally written by @salimfadhley, at https://github.com/salimfadhley/blink1/tree/master/python/pypi.
Moved to this repository and rewritten for `cython-hidapi` by @todbot.

## Installation

Use the `pip` utility to fetch the latest release of this package and any
additional components required in a single step:
```
  pip install blink1
```

## Example Code and Installed scripts
Two command-line scripts `blink1-shine` and `blink1-flash` are installed
when this library is installed.

`blink1-shine` sets the blink(1) to a specific steady color:
```
  blink1-shine --color red
  blink1-shine --color '#ff00ff' --fade 1.5
  blink1-shine --switch-off          # set the color, then turn it off on exit
  blink1-shine --serial 20002345     # pick one of several blink(1)s
  blink1-shine --list                # serial numbers of connected blink(1)s
  blink1-shine --version             # library version, and firmware if connected
```
Note `--switch-off` is off by default, so the light stays lit after the
command exits. This is the opposite of the `blink1()` context manager,
which switches off unless told otherwise.

`--list` and `--version` work with nothing plugged in. `--version` still
reports the library version, and says no device is connected.

`blink1-flash` flashes between two colors at a given rate:
```
  blink1-flash --on white --off black --repeat 5
  blink1-flash --duration 1.5 --fade 0.1
  blink1-flash --serial 20002345
```

Both report a missing blink(1) or an unrecognized color as a one-line
error rather than a traceback. Run either with `--help` for the full
list of options.

For examples, see the [`blink1_demo`](https://github.com/todbot/blink1-python/tree/main/blink1_demo) directory for several examples on how to use this library.

## OS-specific notes
The `blink1-python` library relies on [cython-hidapi](https://github.com/trezor/cython-hidapi) for USB HID access.  This package may require a C compiler and attendant utilities to be installed before installing this library.

### Linux:
The following extra packages must be installed:
```
  sudo apt-get install python3-dev libusb-1.0-0-dev libudev-dev
```
And udev rules for non-root user access to blink(1) devices:
```
  echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="27b8", ATTRS{idProduct}=="01ed", MODE:="666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/51-blink1.rules
  sudo udevadm control --reload
  sudo udevadm trigger
```

### Mac OS X:
Install [Xcode](https://developer.apple.com/xcode/) with command-line tools.

### Windows:
You may need the [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

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
Pass `switch_off=False` to leave it lit.

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

To open a particular blink(1) device by serial number, pass its serial
number as a string:
```
  from blink1.blink1 import Blink1
  b1 = Blink1(serial_number='20002345')
  b1.fade_to_rgb(1000, 255,0,255)
  b1.close()
```
The context manager takes the same argument:
```
  with blink1(serial_number='20002345') as b1:
    b1.fade_to_color(1000, 'purple')
```

### Import styles

The short form works from the package itself:
```
  from blink1 import Blink1
```
The original, fully-qualified form keeps working, and is the only way to
get the context manager under its original name:
```
  from blink1.blink1 import Blink1, blink1
```
The context manager is also re-exported from the package as `blink1_ctx`.
It is not exported as `blink1`, because the package and its main module
share that name and rebinding it would break `import blink1.blink1`.

The package also exports the exception classes, `ColorCorrect`,
`kelvin_to_rgb`, `COLOR_TEMPERATURES`, `VENDOR_ID`, `PRODUCT_ID` and
`__version__`:
```
  from blink1 import Blink1, Blink1ConnectionFailed, InvalidColor
  from blink1 import COLOR_TEMPERATURES, __version__
```

`Blink1` is itself a context manager, so this works too:
```
  with Blink1() as b1:
    b1.fade_to_color(100, 'navy')
```
Note the difference from `blink1()`: leaving a `with Blink1()` block
closes the device but leaves the light on. Only `blink1()` switches it
off for you.

### Colors

There are a number of ways to specify colors in this library:
```
  b1.fade_to_color(1000, '#ffffff') # Hexadecimal RGB as a string
  b1.fade_to_color(1000, 'green') # Named color - any color name understood by css3
  b1.fade_to_color(1000, (22,33,44)) # RGB as a tuple, each 0 <= lum <= 255
  b1.fade_to_color(1000, [22,33,44]) # a list works too
```
An unknown color name, a malformed hexcode, a sequence that is not three
channels, or a channel outside 0-255 all raise `InvalidColor`.


### Pattern playing

The blink(1) device has a non-volatile color pattern memory.
This color pattern plays automatically if power is applied but not connected to a computer.
You can also trigger this pattern (or sub-patterns) over USB,
leaving your application free to do other things besides blink lights.

The memory holds 16 lines on a mk2 and 32 on an mk3. The library works
out which from the firmware version when it opens the device, and
exposes the result as `b1.pattern_lines`. Pass
`Blink1(pattern_lines=...)` to set it yourself and skip the detection.

Each line in the color pattern consists of an R,G,B triplet and a fade time to reach that color.

To play the pattern in blink(1) or sub-patterns:
```
b1.play()  # play entire color pattern, infinitely looped
b1.stop()  # stop a color pattern playing (if playing)

b1.play(2,3, count=7)  # play color pattern lines 2,3 in a loop 7 times
```

To alter the lines of the pattern memory:
```
# write 100msec fades to green then yellow then black at lines 3,4,5
b1.write_pattern_line( 100, 'green',  3)
b1.write_pattern_line( 100, 'yellow', 4)
b1.write_pattern_line( 100, 'black',  5)

b1.play( 3,5, 4)  # play that sub-loop 4 times
```
A `pos` outside the device's pattern memory raises `ValueError`, as does
an `ledn` outside 0-2. On a mk2 that means lines 0-15 only.

`write_pattern_line` applies gamma correction, while `read_pattern_line`
returns the raw device values, so reading a line and writing it back
would compound the correction. Pass `read_pattern_line(pos,
uncorrect=True)` to undo it and get back roughly what you wrote.

To save the pattern to non-volatile memory (overwriting the factory pattern):
```
b1.save_pattern()
```

To quickly play a pattern in Blink1Control-style string format:
```
# play purple on LED1 in 300ms, green on LED2 in 100ms, then swap, for 10 times
pattern_str = '10, #ff00ff,0.3,1, #00ff00,0.1,2,  #ff00ff,0.3,2, #00ff00,0.1,1'
b1.play_pattern(pattern_str)
# wait 5 seconds while the pattern plays on the blink1
# (or go do something more useful)
time.sleep(5.0)
# flash red-off 5 times fast on all LEDs
b1.play_pattern('5, #FF0000,0.2,0,#000000,0.2,0')
```
Be aware that `play_pattern` overwrites the whole pattern memory, filling
any lines the string does not cover with black. That is what makes the
pattern it plays deterministic, but it discards anything written with
`write_pattern_line` beforehand.

Pass `on_device=False` to play the pattern in the Python process instead
of on the blink(1), which blocks until it finishes. The original
`onDevice` spelling still works.

### Servertickle watchdog
blink(1) also has a "watchdog" of sorts called "servertickle".
When enabled, you must periodically send it to the blink(1) or it will
trigger, playing the stored color pattern.  This is useful to announce
a computer that has crashed.  The blink(1) will flash on its own until
told otherwise.

To use, enable servertickle with a timeout value (max timeout 62 seconds):
```
b1.server_tickle(enable=True, timeout_millis=2000)
```


### Gamma correction

Both `Blink1` and the context manager take a *gamma* argument, letting
you supply a per-channel gamma correction value.
```
  import time
  from blink1.blink1 import blink1

  with blink1(gamma=(3, 3, 3)) as b1:
    b1.fade_to_color(100, 'pink')
    time.sleep(10)
```
This example provides a gamma correction of 3 to each of the three colour
channels. The library default is `(2, 2, 2)`.

Higher values of gamma make the blink(1) appear more colorful but decrease the brightness of colours.

### White point correction

The human eye's perception of color can be influenced by ambient lighting. In some circumstances it may be desirable
to apply a small color correction in order to make colors appear more accurate. For example, if we were operating
the blink(1) in a room lit predominantly by candle-light:
```
  from blink1.blink1 import blink1

  with blink1(white_point='candle', switch_off=False) as b1:
    b1.fade_to_color(100, 'white')
```
Viewed in daylight this would make the Blink(1) appear yellowish, however in a candle-lit room this would be perceived
as a more natural white. If we did not apply this kind of color correction the Blink(1) would appear blueish.

The following values are acceptable white-points:

* Any triple of (r,g,b). Each 0 <= luminance <= 255
* Any color_temperature expressed as an integer or float in Kelvin.
  The conversion is only meaningful between 1000 K and 40000 K, and
  values outside that are clamped to it with a logged warning.
* A color temperature name. An unrecognized name raises
  `UnknownWhitePoint`, which is both an `InvalidColor` and a `KeyError`.

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
* warm-fluorescent
* fluorescent
* cool-fluorescent

## API reference

Generated with `python3 -m pydoc blink1.blink1`, trimmed of inherited
boilerplate. Exceptions: `Blink1ConnectionFailed` (a RuntimeError),
`InvalidColor` (a ValueError) and `UnknownWhitePoint` (both an
InvalidColor and a KeyError).

```
    class Blink1(builtins.object)
     |  Blink1(
     |      serial_number: 'str | None' = None,
     |      gamma: 'Sequence[float] | None' = None,
     |      white_point: 'WhitePoint | None' = None,
     |      pattern_lines: 'int | None' = None
     |  ) -> 'None'
     |
     |  Light controller class, sends messages to the blink(1) via USB HID.
     |
     |  Methods defined here:
     |
     |  __enter__(self) -> "'Blink1'"
     |
     |  __exit__(self, exc_type: 'object', exc_value: 'object', traceback: 'object') -> 'None'
     |
     |  __init__(
     |      self,
     |      serial_number: 'str | None' = None,
     |      gamma: 'Sequence[float] | None' = None,
     |      white_point: 'WhitePoint | None' = None,
     |      pattern_lines: 'int | None' = None
     |  ) -> 'None'
     |      :param serial_number: serial number of blink(1) to open, otherwise first found
     |      :param gamma: Triple of gammas for each channel e.g. (2, 2, 2)
     |      :param white_point: White point as (r,g,b), Kelvin, or a name
     |      :param pattern_lines: size of the device's color pattern memory.
     |          Detected from the firmware version when left as None.
     |      :raises: Blink1ConnectionFailed: if blink(1) is not present
     |
     |  clear_pattern(self) -> 'None'
     |      Clear entire color pattern in blink(1)
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |  close(self) -> 'None'
     |      Close the connection to the blink(1). Safe to call twice.
     |
     |  detect_pattern_lines(self) -> 'int'
     |      Ask the firmware how big the color pattern memory is.
     |
     |      Falls back to the mk3 size on any failure, which is what the
     |      library assumed unconditionally before this existed.
     |
     |  fade_to_color(self, fade_milliseconds: 'float', color: 'Color', ledn: 'int' = 0) -> 'None'
     |      Fade the light to a known colour
     |      :param fade_milliseconds: Duration of the fade in milliseconds
     |      :param color: Named color to fade to (e.g. "#FF00FF", "red")
     |      :param ledn: which led to control
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |  fade_to_rgb(
     |      self,
     |      fade_milliseconds: 'float',
     |      red: 'float',
     |      green: 'float',
     |      blue: 'float',
     |      ledn: 'int' = 0
     |  ) -> 'None'
     |      Command blink(1) to fade to RGB color
     |      :param fade_milliseconds: millisecs duration of fade
     |      :param red: 0-255
     |      :param green: 0-255
     |      :param blue: 0-255
     |      :param ledn: which LED to control (0=all, 1=LED A, 2=LED B)
     |      :raises: InvalidColor: if a channel is not a number in 0-255
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |  fade_to_rgb_uncorrected(self, fade_milliseconds, red, green, blue, ledn=0)
     |      Command blink(1) to fade to RGB color, no color correction applied.
     |      :raises: Blink1ConnectionFailed if blink(1) is disconnected
     |
     |  get_serial_number(self) -> 'str'
     |      Get blink(1) serial number
     |      :return blink(1) serial number as string
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |  get_version(self) -> 'str'
     |      Get blink(1) firmware version
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |  off(self) -> 'None'
     |      Switch the blink(1) off instantly
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |  play(self, start_pos: 'int' = 0, end_pos: 'int' = 0, count: 'int' = 0) -> 'None'
     |      Play internal color pattern
     |      :param start_pos: pattern line to start from
     |      :param end_pos: pattern line to end at
     |      :param count: number of times to play, 0=play forever
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |  play_pattern(
     |      self,
     |      pattern_str: 'str',
     |      onDevice: 'bool' = True,
     |      *,
     |      on_device: 'bool | None' = None
     |  ) -> 'None'
     |      Play a Blink1Control-style pattern string
     |      :param pattern_str: The Blink1Control-style pattern string to play
     |      :param onDevice: True (default) to run pattern on blink(1),
     |                       otherwise plays in Python process
     |      :param on_device: snake_case spelling of onDevice; wins if given
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |      Note this overwrites the whole pattern memory, which is what
     |      makes the played pattern deterministic.
     |
     |  play_pattern_local(self, pattern_str: 'str') -> 'None'
     |      Play a Blink1Control pattern string in Python process
     |          (plays in blink1-python, so blocks)
     |      :param pattern_str: The Blink1Control-style pattern string to play
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |  read(self) -> 'List[int]'
     |      Read command result from blink(1), low-level internal use
     |      Receive USB Feature Report 0x01 from blink(1) with 8-byte payload
     |      Note: buf must be 8 bytes or bad things happen
     |      :raises: Blink1ConnectionFailed if blink(1) is disconnected or closed
     |
     |  read_pattern(self, uncorrect: 'bool' = False) -> 'List[Tuple[Any, ...]]'
     |      Read the entire color pattern
     |      :param uncorrect: see read_pattern_line()
     |      :return List of pattern line tuples
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |  read_pattern_line(self, pos: 'int', uncorrect: 'bool' = False) -> 'Tuple[Any, ...]'
     |      Read a color pattern line at position
     |      :param pos: pattern line to read
     |      :param uncorrect: undo the gamma correction write_pattern_line()
     |          applied, so a read-modify-write round trip does not compound it
     |      :return pattern line data as tuple (r,g,b, step_millis)
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |  save_pattern(self) -> 'None'
     |      Save internal RAM pattern to flash
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |  server_tickle(
     |      self,
     |      enable,
     |      timeout_millis=0,
     |      stay_lit=False,
     |      start_pos=0,
     |      end_pos=16
     |  )
     |      Enable/disable servertickle / serverdown watchdog
     |      :param: enable: Set True to enable serverTickle
     |      :param: timeout_millis: millisecs until servertickle is triggered
     |      :param: stay_lit: Set True to keep current color of blink(1), False to turn off
     |      :param: start_pos: Sub-pattern start position in whole color pattern
     |      :param: end_pos: Sub-pattern end position in whole color pattern
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |  set_ledn(self, ledn: 'int' = 0) -> 'None'
     |      Set the 'current LED' value for writePatternLine
     |      :param ledn: LED to adjust, 0=all, 1=LEDA, 2=LEDB
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |  stop(self)
     |      Stop internal color pattern playing
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |  write(self, buf: 'Sequence[int]') -> 'None'
     |      Write command to blink(1), low-level internal use
     |      Send USB Feature Report 0x01 to blink(1) with 8-byte payload
     |      Note: arg 'buf' must be 8 bytes or bad things happen
     |      :raises: Blink1ConnectionFailed if blink(1) is disconnected or closed
     |
     |  write_pattern_line(
     |      self,
     |      step_milliseconds: 'float',
     |      color: 'Color',
     |      pos: 'int',
     |      ledn: 'int' = 0
     |  ) -> 'None'
     |      Write a color & step time color pattern line to RAM
     |      :param step_milliseconds: how long for this pattern line to take
     |      :param color: LED color
     |      :param pos: color pattern line number, 0 to pattern_lines-1
     |      :param ledn: LED number to adjust, 0=all, 1=LEDA, 2=LEDB
     |      :raises: ValueError: if pos is outside the device's pattern memory
     |      :raises: Blink1ConnectionFailed: if blink(1) is disconnected
     |
     |      Note this applies gamma correction, while read_pattern_line()
     |      returns raw device values.
     |
     |  ----------------------------------------------------------------------
     |  Static methods defined here:
     |
     |  color_to_rgb(color: 'Color') -> 'RGB'
     |      Convert color name, hexcode or (r,g,b) sequence to an (r,g,b) tuple
     |      :param color: a color string, e.g. "#FF00FF" or "red", or an
     |          (r,g,b) tuple or list with each channel 0-255
     |      :raises: InvalidColor: if the color cannot be interpreted
     |
     |  find(serial_number: 'str | None' = None)
     |      Find a particular blink(1) device, or the first one
     |      :param serial_number: serial number of blink(1) device (from Blink1.list())
     |      :raises: Blink1ConnectionFailed: if blink(1) is not present
     |
     |  list() -> 'List[str]'
     |      List blink(1) devices connected, by serial number
     |      :return: List of blink(1) device serial numbers
     |
     |  notfound() -> 'None'
     |      Deprecated, always returns None. Use Blink1ConnectionFailed instead.
     |
     |  parse_pattern(pattern_str: 'str') -> 'Tuple[int, List[dict]]'
     |      Parse a Blink1Control pattern string to a list of pattern lines
     |          e.g. of the form '10,#ff00ff,0.1,0,#00ff00,0.1,0'
     |      :param pattern_str: The Blink1Control-style pattern string to parse
     |      :returns: tuple of (num_repeats, list of pattern line dicts)
     |      :raises: ValueError: if the repeat count or a field is unparseable
     |
     |      Omitted and empty fields take their defaults, so
     |      '2,#ff99cc,,0.3' parses rather than raising.
     |

    class ColorCorrect(builtins.object)
     |  ColorCorrect(gamma: 'Sequence[float]', white_point: 'WhitePoint') -> 'None'
     |
     |  Apply a gamma correction to any selected RGB color, see:
     |  http://en.wikipedia.org/wiki/Gamma_correction
     |
     |  Methods defined here:
     |
     |  __call__(self, r: 'float', g: 'float', b: 'float') -> 'RGB'
     |      Call self as a function.
     |
     |  __init__(self, gamma: 'Sequence[float]', white_point: 'WhitePoint') -> 'None'
     |      :param gamma: Tuple of r,g,b gamma values
     |      :param white_point: White point expressed as (r,g,b), integer color
     |          temperature (in Kelvin) or a string value.
     |      :raises: UnknownWhitePoint: if white_point names no known temperature
     |
     |      Gamma values above 1 darken mid-tones; the library default is
     |      (2, 2, 2). Values below 1 brighten them.
     |
     |  uncorrect(self, r: 'float', g: 'float', b: 'float') -> 'RGB'
     |      Undo __call__, mapping device values back towards the input range.
     |
     |  ----------------------------------------------------------------------
     |  Static methods defined here:
     |
     |  gamma_correct(gamma: 'float', white: 'float', luminance: 'float') -> 'int'
     |
     |  gamma_uncorrect(gamma: 'float', white: 'float', value: 'float') -> 'int'
     |

FUNCTIONS
    blink1(
        switch_off: 'bool' = True,
        gamma: 'Sequence[float] | None' = None,
        white_point: 'WhitePoint | None' = None,
        serial_number: 'str | None' = None,
        pattern_lines: 'int | None' = None
    ) -> 'Iterator[Blink1]'
        Context manager which automatically shuts down the Blink(1)
        after use.
        :param switch_off: turn blink(1) off when exiting context
        :param gamma: set gamma curve (as tuple)
        :param white_point: set white point (as tuple)
        :param serial_number: serial number of blink(1) to open, otherwise first found
        :param pattern_lines: size of color pattern memory, detected if None
```

## Developer installation

Having checked out the `blink1-python` library, cd to its directory and run the setup script:
```
  git clone https://github.com/todbot/blink1-python
  cd blink1-python
  pip3 install --editable ".[dev]"
  python3 ./blink1_demo/demo1.py
```
You can now use the `blink1` package on your system and edit it.

To run the tests, which do not need a blink(1) attached:
```
  pytest
```
Tests that do need a real device are marked `hardware` and skipped
unless you ask for them:
```
  pytest --run-hardware
```

To get internal blink1 library debug, messages set the environment variable `DEBUGBLINK1`:
```
DEBUGBLINK1=1 python3 ./blink1_demo/demo_logging.py
```

To uninstall the development version:
```
  pip3 uninstall blink1
```
