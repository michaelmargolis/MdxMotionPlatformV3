"""
  remote client for space_coaster_player for V3 software
  
  This version controls two local clients with one or more running on remote pc

"""

import sys
import socket
from math import radians, degrees
import threading
import time
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

import csv,os

from tcp_client import SockClient
from remote_client_gui_defs import *


import logging
log = logging.getLogger(__name__)
# import logging.handlers

sys.path.insert(0, '../common')
from serial_remote import SerialRemote
from udp_remote import UdpRemote
import gui_utils as gutil

import ctypes # for mouse
import numpy as np  # for scaling telemetry data

class State:
    initializing, waiting, ready, running, completed = list(range(0,5))


class InputInterface(object):
    USE_UDP_MONITOR = False

    def __init__(self, sleep_func):
        self.sleep_func = sleep_func
        self.name = "Remote Client"
        self.is_normalized = True
        self.expect_degrees = False # convert to radians if True

        self.max_values = [80, 80, 80, 0.4, 0.4, 0.4]
        self.levels = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0] # pre normalized
        
        self.normalized = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.previous_msg_time = 0;
        self.telemetry = []

        self.frame_number = 0

        self.clients = []
        # self.clients.append(SockClient('127.0.0.1', 10015))
        self.clients.append(SockClient('192.168.1.23', 10015))

        self.state_strings = ("Initializing", "Waiting", "Ready", "Running", "Completed")
        # the states are set by client 0
        self.state = -1 # state not yet set
        self.is_paused = False

        actions = {'detected remote': self.detected_remote, 'activate': self.activate,
           'deactivate': self.deactivate, 'pause': self.pause, 'dispatch': self.dispatch,
           'reset': self.reset, 'emergency_stop': self.emergency_stop,
           'intensity' : self.set_intensity, 'info' : self.remote_info }
        self.SerialRemoteControl = SerialRemote(actions)
        self.UdpRemoteControl = UdpRemote(actions)


    def init_gui(self, frame):
        self.ui = Ui_Frame()
        self.ui.setupUi(frame)

        #control arrays
        self.lbl_coaster_status = [self.ui.lbl_coaster_status_1, self.ui.lbl_coaster_status_2]
        self.lbl_coaster_connection = [self.ui.lbl_coaster_connection_1, self.ui.lbl_coaster_connection_2]
        # self.lbl_temperature_status = [self.ui.lbl_temperature_status_1,self.ui.lbl_temperature_status_1]
                
        # configure signals
        self.ui.btn_dispatch.clicked.connect(self.dispatch)
        self.ui.btn_pause.clicked.connect(self.pause)
        
        self.ui.btn_reset_rift_1.clicked.connect(self.reset1)
        self.ui.btn_reset_rift_2.clicked.connect(self.reset2)

        for i in range(len(self.clients)):
            gutil.set_text(self.lbl_coaster_connection[i], "Attempting to Connect to " + self.clients[i].ip_addr,"orange") 

    def detected_remote(self, info):
        if "Detected Remote" in info:
            gutil.set_text(self.ui.lbl_remote_status, info, "green")
        elif "Looking for Remote" in info:
            gutil.set_text(self.ui.lbl_remote_status, info, "orange")
        else:
             gutil.set_text(self.ui.lbl_remote_status, info, "red")
            
    def quit(self):
        self.command("quit")
        
    def activate(self):  #todo - move remote control response from clients to platform_controller if state can be managed
        self.command("enable")

    def deactivate(self):
        self.command("disable")

    def pause(self):
        if self.state == State.running:
            self.command("pause")
            for client in self.clients:
                client.send('pause\n')
        else:
            self.command("swellForStairs")
        
    def reset(self):
        log.info("reset all rifts")
        for client in self.clients:
            client.send('reset\n')

    def reset1(self):
        log.info("reset rift 1")
        self.clients[0].send('reset\n')
        
    def reset2(self):
        log.info("reset rift 2")
        self.clients[1].send('reset\n')

    def set_intensity(self, intensity_msg):
        self.command(intensity_msg)

    def emergency_stop(self):
        log.info("legacy emergency stop callback")
        self.deactivate()
 
    def command(self, cmd):
        if self.cmd_func is not None:
            log.info("Requesting command: %s", cmd)
            self.cmd_func(cmd)
    
    def dispatch(self):
        log.debug('preparing to dispatch')
        self.command("ready")  # slow rise of platform
        self.command("unparkPlatform")
        #  self._sleep_func(1)
        for client in self.clients:
            client.send('dispatch\n')
        log.debug("dispatched")
        # self.frame_number = 30 # start 1.5 seconds in

    def remote_info(self):
        log.debug("remote request for info")
        self.UdpRemoteControl.send("state," + self.state_strings[self.state])

    # def chair_status_changed(self, chair_status):
    #     log.debug(chair_status[0])
    
    def intensity_status_changed(self, intensity):
       gutil.set_text(self.ui.lbl_intensity_status, intensity[0], intensity[1])

    def begin(self, cmd_func, move_func, limits):
        self.cmd_func = cmd_func
        self.move_func = move_func
        self.limits = limits  # note limits are in mm and radians
        while not self.check_client_connections(): 
            self.sleep_func(1)
        if self.is_normalized:
            log.info('Platform Input is Remote Client with normalized parms, %d clients connected', len(self.clients))
        else:
            log.info('Platform Input is Remote Client with real world parms, %d clients connected', len(self.clients))
 
    def check_client_connections(self):
        all_connected = True 
        try:
            for client in self.clients:
                if not client.status.connected:
                    client.connect()
                if not client.status.connected:
                    all_connected = False
        except:
            all_connected = False
        return all_connected

    
    def fin(self):
        # client exit code goes here
        pass

    def get_current_pos(self):
        return self.levels

    def service(self):
        if self.check_client_connections():
            for idx, client in enumerate(self.clients):
                #print "sending telemetry request for client", idx
                client.send('telemetry\n')
                while client.available() > 0:
                    event = client.receive()
                    # print "in service", event
                    msg = event.split(";")
                    try:
                        state_info = msg[0].split(',')
                        state = int(state_info[0])
                        frame = int(state_info[1])
                        is_paused = int(state_info[2])
                        
                        if idx == 0:  # track state of first client
                            if self.state != state:
                               log.debug("state changed to %s",  self.state_strings[state]) 
                            self.state = state
                            self.frame = frame
                            self.is_paused = is_paused
                            try:
                                self.levels =[float(i) for i in msg[1].split(',')]
                                log.debug("telemetry: %s",  msg[1])
                            except:
                                log.error("Unable to process telemetry %s", msg[1])
                            if self.move_func:
                               self.move_func(self.levels)
                        else:
                            if state != self.state:
                                log.debug("state mismatch with idx %d", idx)
                            if frame != self.frame:
                                 log.debug("frame difference is %d", self.frame - frame) 
                            if is_paused != self.is_paused:
                                 log.debug("pause state mismatch with idx %d", idx)

                        status = msg[2].split(',')
                        debug_info = format("%d,%d,%d  " % (state, frame,is_paused))
                        gutil.set_text(self.lbl_coaster_status[idx], debug_info+status[0], status[1])

                        if client.status.connected:
                            status = msg[3].split(',')
                        else:
                            status = ["Not connected", "red"]
                        gutil.set_text(self.lbl_coaster_connection[idx], status[0] + " on " + self.clients[idx].ip_addr, status[1]) 
                    except Exception as e:
                        log.error("error parsing %s: %s", msg, e)
                
        self.SerialRemoteControl.service()
        self.UdpRemoteControl.service()
        msg = None


######### code for remote client run from main ############

class RemoteClient(QtGui.QMainWindow):
    """
    on state or status change local client will pass:
        current coaster state, current connection state, coaster status string, color
    every frame client will pass:
        frame number, xyzrpy
        
    commands:
        reset, dispatch, pause 
    
    """
    def __init__(self, sleep_func):
        try:
            QtGui.QMainWindow.__init__(self)
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)

            self.client = InputInterface(sleep_func) 
            self.client.init_gui(self.ui.frame)
            limits = cfg.limits_1dof
            self.client.begin(self.cmd_func, self.move_func, limits)
            service_timer = QtCore.QTimer(self)
            service_timer.timeout.connect(self.client.service)
            log.info("Starting client service timer")
            service_timer.start(50) 
        except:
            e = sys.exc_info()[0]  # report error
            log.error("error starting remote client %s", e)
 
    def cmd_func(self, cmd):  # command handler function called from Platform input
        if cmd == "quit": 
            self.quit()

    def move_func(self, request):  # move handler to position platform as requested by Platform input
        pass
        # print("in move func", request)

    def quit(self):
        for client in self.client.clients:
            client.disconnect()
        log.info("Executing quit command")
        sys.exit()
 
if __name__ == "__main__":
    sys.path.insert(0, '../output')
    import gui_sleep
    from local_client_gui_defs import *
    import importlib  
   
   #start_logging(log.DEBUG)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%H:%M:%S')
    log.info("Starting remote client")
    
    # platform_selection = 'ConfigV3'
    platform_selection = 'configNextgen'
    cfg = importlib.import_module(platform_selection).PlatformConfig()

    gui_sleep._gui__app = QtGui.QApplication(sys.argv) 
    
    try:       
        remote_client = RemoteClient(gui_sleep.sleep )
        remote_client.show()
        gui_sleep._gui__app.exec_()
        
        gui_sleep._gui__app.exit()
        log.info("Exiting Remote client\n")
    except Exception as e:
        log.error("error starting remote client %s", e)
