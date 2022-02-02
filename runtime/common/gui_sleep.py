import time
try:
    from PyQt4 import QtGui 
except:    
   from PyQt5 import QtGui, QtCore 

_gui__app = None

def sleep(duration_secs):
    start = time.time()
    show_flag = True
    while time.time() - start < duration_secs:
        if _gui__app != None:
            _gui__app.processEvents()
        elif show_flag:
            print("gui_sleep is blocking for", duration_secs, "seconds")
            show_flag = False

def sleep_qt(delay):
    loop = QtCore.QEventLoop()
    timer = QtCore.QTimer()
    timer.setInterval(delay*1000)
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start()
    loop.exec_() 