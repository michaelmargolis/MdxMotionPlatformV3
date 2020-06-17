import time
from PyQt4 import QtGui 

_gui__app = None

def sleep(duration_secs):
    start = time.time()
    show_flag = True
    while time.time() - start < duration_secs:
        if _gui__app != None:
            _gui__app.processEvents()
        elif show_flag:
            print "gui_sleep is blocking for", duration_secs, "seconds"
            show_flag = False
