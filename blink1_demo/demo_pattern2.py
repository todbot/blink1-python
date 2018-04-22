#!/usr/bin/env python

"""
demo_pattern2 -- demo of blink1 library color pattern playing, with subloops
"""
import time,sys
from blink1.blink1 import Blink1


blink1 = Blink1(gamma=(1,1,1))  # disable gamma

if ( blink1.dev == None ):
    print("no blink1 found")
    sys.exit()
else:
    print("blink(1) found")

print("serial number: " + blink1.get_serial_number())
print("firmware version: " + blink1.get_version())

print("setting patternline 0 to #00FFFE @ 500 msec");
blink1.writePatternLine( 500, '#00fffe', 0)
print("setting patternline 1 to #EEDD00 @ 550 msec");
blink1.writePatternLine( 550, '#eedd00', 1)
print("setting patternline 2 to #333333 @ 560 msec");
blink1.writePatternLine( 560, '#333333', 2)

print("reading pattern line 1")
(r,g,b, fade_millis) = blink1.readPatternLine( 1 )
print("patternline 1: #%02X%02X%02X @ %d msec" % (r,g,b, fade_millis) )


print("reading entire pattern")
pattern = blink1.readPattern()

print("pattern:",pattern)

print("done")
