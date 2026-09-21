#!/usr/bin/env python

"""
demo_namespace -- demo of the flat `from blink1 import ...` namespace
"""
import sys
import time

from blink1 import Blink1, Blink1ConnectionFailed

try:
    b1 = Blink1()
except Blink1ConnectionFailed as e:
    print("no blink1 found:", e)
    sys.exit(1)

b1.fade_to_color(100, 'green')
time.sleep(1)
b1.fade_to_color(100, 'black')
b1.close()
