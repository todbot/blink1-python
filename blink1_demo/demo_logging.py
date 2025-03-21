#!/usr/bin/env python

"""
demo_logging -- simple demo of blink1 library with logging

run with:
DEBUGLBLINK1=1 python3 ./blink1_demo/demo_logging.py

"""
from blink1.blink1 import Blink1

import time,sys

import logging

logging.basicConfig()
#logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
#logging.basicConfig(filename="test.log", format='%(filename)s: %(message)s', filemode='w')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.info("hello info")
log.debug("hello debug")
log.warning("hello warning")
log.error("hello error")

try:
    blink1 = Blink1()
except:
    log.error("no blink1 found")
    sys.exit()

log.info("blink(1) found")

log.info("  serial number: " + blink1.get_serial_number())
log.info("  firmware version: " + blink1.get_version())

log.info("fading to #ffffff")
blink1.fade_to_rgb(1000, 255, 255, 255)

log.info("waiting 2.5 seconds, unplug to check error raising...");
time.sleep(2.5)

log.info("fading to #000000")
blink1.fade_to_color(1000, 'black')

log.info("closing connection to blink(1)")
blink1.close()

log.info("done")
