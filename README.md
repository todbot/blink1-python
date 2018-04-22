

Python3 Blink(1) library
========================

Official Python library for blink(1) USB RGB LED notification devices
https://blink1.thingm.com/

* [About this library](#about-this-library)
* [Installation](#installation)
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

## OS-specific notes
The `blink1-python` library relies on [`cython-hidapi`](https://github.com/trezor/cython-hidapi) for USB HID access.  This package may require a C compiler and attendant utilities to be installed before installing this library.

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

The blink(1) device has a 16 line non-volatile color pattern memory.
This color pattern plays automatically if power is applied but not connected to a computer.  You can also trigger this pattern (or sub-patterns) over USB,
leaving your application free to do other things besides blink lights.

Each line in the color pattern consists of an R,G,B triplet and a fade time to reach that color.

To play the pattern or sub-patterns:
```
blink1.play()  # play entire color pattern, infinitely looped
blink1.stop()  # stop a color pattern playing (if playing)

blink1.play(2,3, count=7)  # play color pattern lines 2,3 in a loop 7 times
```

To alter the lines of the pattern memory:
```
# write 100msec fades to green then black then yellow at lines 3,4,5
blink1.writePatternLine( 100, 'green',  3)
blink1.writePatternLine( 100, 'black',  4)
blink1.writePatternLine( 100, 'yellow', 5)

blink1.play( 3,5, 4)  # play that sub-loop 4 times
```

To save the pattern to non-volatile memory (overwriting the factory pattern):
```
blink1.savePattern()
```

### Servertickle watchdog
blink(1) also has a "watchdog" of sorts called "servertickle".
When enabled, you must periodically send it to the blink(1) or it will
trigger, playing the stored color pattern.  This is useful to announce
a computer that has crashed.  The blink(1) will flash on its own until
told otherwise.

To use, enable severtickle with a timeout value (max timeout 62 seconds):
```

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
to apply a small colour correction in order to make colors appear more accurate. For example, if we were operating
the blink(1) in a room lit predimenantly by candle-light:
```
  with blink1(white_point='candle', switch_off) as b1:
    b1.fade_to_color(100, 'white')
```
Viewed in daylight this would make the Blink(1) appear yellowish, hoever in a candle-lit room this would be perceived
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
  pip install --editable .
```
You can now use the `blink1` package on your system and edit it.

To get internal blink1 library debug, messages set the environment variable `DEBUGBLINK1`:
```
DEBUGBLINK1=1 python ./blink1_demo/demo1.py
```

To uninstall the development version:
```
  python setup.py develop --uninstall
```
