#!/usr/bin/env python

import time

#from blink1 import Blink1
from blink1.blink1 import Blink1

blink1_serials = Blink1.list()
print("serials: ", ','.join(blink1_serials))

#blink1 = Blink1(serial_number=u'20006487')
blink1 = Blink1()

if ( blink1.dev == None ):
    print("no blink1 found")
else:
    print("blink(1) found")

print("serial number: " + blink1.get_serial_number())
print("firmware version: " + blink1.get_version())

blink1.fade_to_rgb(500, 0, 255, 0)
time.sleep(0.5)
blink1.fade_to_rgb(500, 255, 0, 255)
time.sleep(0.5)
blink1.fade_to_rgb(500, 0, 0, 0)
