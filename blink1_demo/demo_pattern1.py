#!/usr/bin/env python

"""
demo_pattern1 -- demo of blink1 library color pattern playing 
"""
import time,sys
from blink1.blink1 import Blink1


try:
    blink1 = Blink1()
except:
    print("no blink1 found")
    sys.exit()

print("blink(1) found")

print("  serial number: " + blink1.get_serial_number())
print("  firmware version: " + blink1.get_version())

print("playing full entire pattern")
blink1.play();

print("waiting for 10 seconds")
time.sleep(10.0)

print("stopping pattern")
blink1.stop()

print("done")
