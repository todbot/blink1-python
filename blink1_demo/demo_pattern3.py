#!/usr/bin/env python

"""
demo_pattern3 -- demo of blink1 library color pattern parsing
"""
import time,sys
from blink1.blink1 import Blink1

pattern_strs = [
    '3, #ff00ff,0.3,1, #00ff00,0.1,2,#ff00ff,0.3,2,#00ff00,0.1,1,#000000,0.5,0',
    ' 10, #ff00ff,0.3,1, #00ff00,0.1,2,  #ff00ff,0.3,2, #00ff00,0.1,1' ,
    '  10, #ff00ff,0.3,1, #00ff00,0.1,2 ',
    '  7, #ff00ff,0.3,1, #00ff00,0.1,2, #ff3333  ',
    '  1, ',
    '  2, #ff99cc,,0.3',
    '  0, #ff00ff,0.3',
    ]

patt_str = pattern_strs[0]

(num_repeats,pattern_list) = Blink1.parsePattern(patt_str)
print('num_repeats: ', num_repeats)
print('pattern_list: ', pattern_list)

try:
    blink1 = Blink1()
except:
    print("no blink1 found")
    sys.exit()
print("blink(1) found")

play_on_blink1 = True
#play_on_blink1 = False

if( play_on_blink1 ): 
    print("playing on blink1 device (thus not blocking)");
    blink1.play_pattern( patt_str )
    print("sleeping for 10 secs...")
    time.sleep(10)
else:
    print("playing using Python (blocking)")
    blink1.play_pattern( patt_str, on_device=False )

blink1.off()

blink1.close()
