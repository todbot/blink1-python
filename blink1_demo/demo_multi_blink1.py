#!/usr/bin/env python
"""
demo2 -- demo of blink1 library, accessing multiple blink(1) devices

"""

import time,sys
from blink1.blink1 import Blink1

blink1_serials = Blink1.list()
if blink1_serials:
    print("blink(1) devices found: "+ ','.join(blink1_serials))
else:
    print("no blink1 found")
    sys.exit()

# To open a particular blink(1), do:
# blink1 = Blink1(serial_number=u'20006487')
print("opening first blink(1)")
blink1 = Blink1( serial_number=blink1_serials[0] ) # first blink1
print("  serial number: " + blink1.get_serial_number())
print("  firmware version: " + blink1.get_version())

print("  playing green, purple, off...")
blink1.fade_to_rgb(500, 0, 255, 0)
time.sleep(0.5)
blink1.fade_to_rgb(500, 255, 0, 255)
time.sleep(0.5)
blink1.fade_to_rgb(500, 0, 0, 0)
time.sleep(0.5)

print("closing.")
blink1.close()

print("opening last blink(1)")
blink1 = Blink1( serial_number=blink1_serials[-1] ) # last blink1
print("  serial number: " + blink1.get_serial_number())
print("  firmware version: " + blink1.get_version())
print("  playing aqua, off...")

blink1.fade_to_color(200, 'aqua')
time.sleep(0.5)
blink1.fade_to_color(200, 'black')
time.sleep(0.5)

print("closing.")
blink1.close()
