#!/usr/bin/env python3

import hid

REPORT_ID = 1
VENDOR_ID = 0x27b8
PRODUCT_ID = 0x01ed

devs = hid.enumerate( VENDOR_ID, PRODUCT_ID)
#print(devs)
serials = []
for d in devs:
    print(d)
    serials.append(d.get('serial_number'))

serialz = map(lambda d:d.get('serial_number'), devs)

serial_number = None

#devs = map(lambda d: print(d), devs)
print("serials:", serials)
print("serialz:", serialz)

hidraw = hid.device( VENDOR_ID, PRODUCT_ID, serial_number )
hidraw.open( VENDOR_ID, PRODUCT_ID, serial_number )
#hidraw.send_feature_report([0x02, 0x10, 0x00,0x00,0x00,0x00,0x00,0x00])
featureReport = [REPORT_ID, 99, 255, 0, 255, 0, 11, 0, 0];
hidraw.send_feature_report( featureReport )
