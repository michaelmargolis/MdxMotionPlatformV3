# kbhit_sleep.py
from common.kbhit  import KBHit
import time

kb = KBHit()

# returns False if esc key pressed
def kb_sleep(dur_secs, esc = 27):
    start = time.time()
    interval = dur_secs / 50.0
    if interval < .001:
            interval = .001 # precision is 1ms
    # print(interval)
    while time.time() - start < dur_secs:
        time.sleep(interval)
        if kb.kbhit(): 
            key = kb.getch()
            if ord(key) == esc:
                return False
    # print(time.time()- start)
    return True

