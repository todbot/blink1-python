#!/usr/bin/env python

"""
demo_serial -- demo of blink1 library showing serial number and versions

"""
from blink1.blink1 import Blink1

try:
    blink1 = Blink1()
except:
    print("no blink1 found")
    sys.exit()
print("blink(1) found")

print("  serial number: " + blink1.get_serial_number())
print("  firmware version: " + blink1.get_version())

print("closing connection to blink(1)")
blink1.close()

print("done")
