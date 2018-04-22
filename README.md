

Python3 Blink(1) library
========================

Official Python library for blink(1) USB RGB LED notification devices
https://blink1.thingm.com/

## About this library

This is a rewrite of the original Python library. It includes the following modifications:

* 100% test coverage on all library components
* Python 3.x compatible
* Automatic installation via Python Package Index.
* High level control over the blink(1).
* Single implementation with `cython-hidapi` (instead of PyUSB)

This library lives at https://github.com/todbot/blink1-python

Originally written by @salimfadhley, at https://github.com/salimfadhley/blink1/tree/master/python/pypi.
Moved to this repository and rewritten for `cython-hidapi` by @todbot.

## Installation

Use the pip utility to fetch the latest release of this package and any
additional components required in a single step:
```
  pip install blink1
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
  pip install --editable
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

### OS-specific notes

While `blink1-python` is not OS-specific, the [cython-hidapi](https://github.com/trezor/cython-hidapi) library it uses does have platform-specific requirements.

#### Linux:
You will need to install extra packages:
```
  sudo apt-get install python-dev libusb-1.0-0-dev libudev-dev
```

And udev rules for non-root user access:
```
  echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="27b8", ATTRS{idProduct}=="01ed", MODE:="666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/51-blink1.rules
  sudo udevadm control --reload
  sudo udevadm trigger
```


#### Mac OS X:
You will need Xcode installed with command-line tools.

#### Windows:
You will need "Microsoft Visual C++ Compiler for Python 2.7" http://aka.ms/vcpython27

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
  print("blink(1) devices found:", ','.join(blink1_serials))
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
  b1.fade_to_color(1000, '#ffffff') # Hexdecimal RGB as a string
  b1.fade_to_color(1000, 'green') # Named color - any color name understood by css3
  b1.fade_to_color(1000, (22,33,44) # RGB as a tuple. Luminance values are 0 <= lum <= 255
```
Attempting to select a color outside the plausible range will generate an InvalidColor exception.

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
