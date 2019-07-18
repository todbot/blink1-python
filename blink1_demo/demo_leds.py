#!/usr/bin/env python

"""
demo_leds -- demo of blink1 library showing independent LED access

"""
import time,sys
from blink1.blink1 import Blink1

try:
    blink1 = Blink1()
except:
    print("no blink1 found")
    sys.exit()

print("fading to 255,0,0 on LED1" )
blink1.fade_to_rgb(500, 255, 0,   0, 1)
print("fading to 0,0,255 on LED2" )
blink1.fade_to_rgb(500,   0, 0, 255, 2)

time.sleep(1.0)

print("fading to blue on LED1" )
blink1.fade_to_color(500, 'blue', 1)
print("fading to red on LED2" )
blink1.fade_to_color(500, 'red', 2)

time.sleep(1.0)

print("fading to black on both LEDs")
blink1.fade_to_color(1000, 'black', 0)

time.sleep(1.0)

print("fading to green on both LEDs")
blink1.fade_to_color(500, '#00FF00')

time.sleep(1.0)
print("fading to black on both LEDs")
blink1.fade_to_color(500, 'black')

print("closing connection to blink(1)")
blink1.close()

print("done")
