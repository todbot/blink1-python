#!/usr/bin/env python

"""
demo_servertickle -- demo of blink1 library servertickle feature
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

print("setting blink(1) green")
blink1.fade_to_color(100, 'green')

for i in range(0,5):
    print("enabling server tickle for 5 seconds")
    blink1.serverTickle( enable=True, timeout_millis=5000, stay_lit=True )
    time.sleep(2.0)

print("stopped updating servertickle, waiting for 10 seconds")
print("blink1 will play its pattern in 5 seconds")
time.sleep(10)

print("Disabling servertickle")
blink1.serverTickle( enable=False )

blink1.close()


