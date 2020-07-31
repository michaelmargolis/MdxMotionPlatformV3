""" code for local client run from main

This module to be imported into client code
"""

import sys
import socket
import traceback
import time
import logging
log = logging.getLogger(__name__)

from local_client_gui_defs import *
from common.tcp_server import TcpServer
from platform_config import cfg

class LocalClient(QtWidgets.QMainWindow):
    """
    on state or status change local client will pass:
        current coaster state, current connection state, coaster status string, color
    every frame client will pass:
        frame number, comma separated transform
        
    commands:
        reset, dispatch, pause 
    
    """
    def __init__(self, client, pfm):
        log.info("Starting local client")
        try:
            QtWidgets .QMainWindow.__init__(self)
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)
            
            self.client = client # InputInterface(True) 
            self.client.init_gui(self.ui.frame)
            limits = pfm.limits_1dof
            self.client.begin(self.cmd_func, limits)
            self.server = TcpServer(('', cfg.REMOTE_CLIENT_PORT))
            self.server.start()
            log.info("Started tcp server, this IP address is %s", self.server.get_local_ip())
            service_timer = QtCore.QTimer(self)
            service_timer.timeout.connect(self.service)
            self.prev_service = None
            self.FRAME_RATE_ms = 50
            # log.info("Starting service timer")
            # service_timer.start(50) 
            self.service()
        except Exception as e:
            s = traceback.format_exc()
            log.error("Space coaster local client %s %s", e, s)
 
    def service(self):
        time_to_svc = int(self.FRAME_RATE_ms/2)  # default
        now = time.time()
        if self.prev_service != None:
            elapsed =  (now - self.prev_service) * 1000
            to_go = self.FRAME_RATE_ms - elapsed
            if to_go < 1:
                if to_go < -1:
                    log.debug("Service interval was %d ms", elapsed)
                self.prev_service = now
                self.client.service()
                self.server.broadcast(self.client.form_telemetry_msg()) # fixme change to send after 'telemetry' msg?
                if self.server.connected_clients() > 0:
                    self.client.detected_remote("Detected Remote Client Connection")
                else:
                     self.client.detected_remote("Remote client not Connected, this IP is: " + self.server.get_local_ip())
                while self.server.available():
                    try:
                        sender, msg = self.server.get()
                        if msg:
                            event = msg.split("\n") 
                            for e in event:
                                e = e.rstrip()
                                # print format("[%s], %d" % (e, len(e)))
                                if e in self.client.actions:
                                    log.info("got remote client cmd %s", e)
                                    self.client.actions[e]()
                    except IndexError:
                        log.warning("client queue index error")
            else:
                time_to_svc = int(max(to_go/2, 1))
                # print "tp go=", to_go, "tts=", time_to_svc
                
        else:
            self.prev_service = time.time()
            # self.f = open("timer_test.csv", "w")
            log.warning("starting service timing latency capture to file: timer_test.csv")
        QtCore.QTimer.singleShot(time_to_svc, self.service)
            
    def cmd_func(self, cmd):  # command handler function called from Platform input
        if cmd == "quit": self.quit()
        elif cmd == "dispatch": self.client.dispatch()
        elif cmd == "pause": self.client.pause()

    def quit(self):
        log.info("Executing quit command")
        sys.exit()

def client_main(client):
    from clients.local_client_gui_defs import Ui_MainWindow
    import importlib  
    
    sys.path.insert(0, 'output')  # for platform config
    
    log_level = logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%H:%M:%S')
    log.info("Python: %s, qt version %s", sys.version[0:5], QtCore.QT_VERSION_STR)
    
    # platform_selection = '.ConfigV3'
    platform_selection = 'configNextgen'
    pfm = importlib.import_module(platform_selection).PlatformConfig()

    app = QtWidgets.QApplication(sys.argv) 
    
    try: 
        local_client = LocalClient(client, pfm)
        local_client.show()
        app.exec_()
    #except ConnectionException as error:
    #    log.error("User aborted because client not found") 
    except Exception as e:
        s = traceback.format_exc()
        log.error("Local Client main %s %s", e, s)
      
    app.exit()
    log.info("Exiting Local Client\n")
    