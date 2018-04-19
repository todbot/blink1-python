import time
from blink1.blink1 import blink1

with blink1() as b1:
    b1.fade_to_color(300, 'goldenrod')
    time.sleep(2)

time.sleep(1)

# notice how blink(1) is turned off and closed
# outside of the 'with' block
# you can override this this 'switch_off' flag

with blink1(switch_off=False) as b1:
    b1.fade_to_color(300, 'pink')
    time.sleep(2)

with blink1() as b1:
    b1.fade_to_color(300, 'aqua')
    time.sleep(2)

    

