#!/usr/bin/env python

"""
demo_pattern2 -- demo of blink1 library color pattern writing
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

# write 100msec fades to green then yellow then black at lines 3,4,5
print("writing green,yellow,black to pattern positions 3,4,5")
blink1.write_pattern_line( 500, 'green',  3)
blink1.write_pattern_line( 500, 'yellow', 4)
blink1.write_pattern_line( 500, 'black',  5)

print("playing created subpattern 4 times")
blink1.play( 3,5, 4)  # play that sub-loop 4 times

print("done (pattern will continue to play")
blink1.close()
