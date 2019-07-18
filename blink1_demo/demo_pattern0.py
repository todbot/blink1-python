#!/usr/bin/env python

"""
demo_pattern0 -- demo of blink1 library color pattern reading
"""
import sys
from blink1.blink1 import Blink1

try:
    blink1 = Blink1( gamma=(1,1,1) ) # disable gamma
except:
    print("no blink1 found")
    sys.exit()

print("Reading full color pattern:")
pattern = blink1.read_pattern()
print(pattern)
