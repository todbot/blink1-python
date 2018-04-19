#!/usr/bin/env python

"""
demo_serial -- demo of blink1 library showing serial number and versions

"""
import time,sys

from blink1.blink1 import Blink1


blink1 = Blink1()

if ( blink1.dev == None ):
    print("no blink1 found")
    sys.exit()
else:
    print("blink(1) found")

print("  serial number: " + blink1.get_serial_number())
print("  firmware version: " + blink1.get_version())

print("fading to #ff0000 on LED1" )
blink1.fade_to_rgb(500, 255, 0,   0, 1)
print("fading to #0000ff on LED2" )
blink1.fade_to_rgb(500,   0, 0, 255, 2)

time.sleep(0.5)

print("fading to #0000ff on LED1" )
blink1.fade_to_rgb(500,   0, 0, 255, 1)
print("fading to #ff0000 on LED2" )
blink1.fade_to_rgb(500, 255, 0,   0, 2)

time.sleep(0.5)

print("fading to #000000 on both LEDs")
blink1.fade_to_rgb(1000, 0, 0, 0)

print("closing connection to blink(1)")
blink1.close()

print("done")
