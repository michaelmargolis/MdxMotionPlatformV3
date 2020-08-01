"""
  Space_coaster for V3 software
  
  This version reads telemetry data from a CSV file
  Orientation from this file synced to UDP frames sent by SpaceCoaster
  on port 10009 (only state data in coaster msg frames is used)
"""

import sys
from os import path
import socket
from math import radians, degrees
from threading import Thread, Lock
import time
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

import traceback
import csv,os
import win32gui

import logging
log = logging.getLogger(__name__)

import ctypes # for mouse
import numpy as np  # for scaling telemetry data

#  from space_coaster_gui_defs import *
from PyQt5 import QtCore, QtGui, QtWidgets

from clients.client_api import ClientApi
from clients.SpaceCoaster.space_coaster_gui_defs import Ui_Frame
from clients.ride_state import RideState
from common.tcp_server import TcpServer
from common.dialog import ModelessDialog
import common.gui_utils as gutil
from platform_config import cfg

class SC_State:  # these are space coaster specific states
    initializing, waiting, ready, running, completed = list(range(0,5))

class ConnectionException(Exception):
    pass

class InputInterface(ClientApi):
    USE_GUI = True  # set True if using tkInter

    def __init__(self, is_local_client = False):
        super(InputInterface, self).__init__()
        self.sleep_func = gutil.sleep_qt
        self.name = "Space Coaster"
        self.is_local_client = is_local_client
        self.log = None
        self.is_normalized = True
        self.expect_degrees = False # convert to radians if True
        self.max_values = [80, 80, 80, 0.4, 0.4, 0.4]
        self.telemetry = []
        self.start_frame = 30
        self.cosmetic_frame = 0
        self.frame_number = self.start_frame
        self.coaster_status = "Waiting to complete initial run" 
        self.connection_status = "Not yet set"
       
        self.sc_state_str = ("Initializing", "Waiting", "Ready", "Running", "Completed")
        self.sc_state = -1 # this is the internal space coaster state
        self.state = RideState.DISABLED  # this is the generic ride state used by all clients
        self.is_paused = False

        self.actions = {'detected remote': self.detected_remote, 'pause': self.pause,
                        'dispatch': self.dispatch, 'reset': self.reset_vr,
                        'emergency_stop': self.emergency_stop, 'intensity' : self.set_intensity,
                        'info' : self.remote_info }
        if self.is_local_client:
           log.info("Starting as local client")

    def init_gui(self, frame):
        self.frame = frame
        self.ui = Ui_Frame()
        self.ui.setupUi(frame)

        # configure signals
        self.ui.btn_dispatch.clicked.connect(self.dispatch_pressed)
        self.ui.btn_pause.clicked.connect(self.pause_pressed)
        self.ui.btn_reset_rift.clicked.connect(self.reset_vr)

        self.report_connection_status(self.connection_status, 'red')
        self.report_coaster_status(self.coaster_status, 'black')
        self.dialog = ModelessDialog(frame)
        log.info("Client GUI initialized")

    def set_focus(self, window_class=None, window_title=None):
        guiHwnd = win32gui.FindWindow(window_class,window_title)
        log.debug("window name=%s, class=%s, Hwnd= %d", window_title, window_class, guiHwnd)
        win32gui.SetForegroundWindow(guiHwnd)
        
    def left_mouse_click(self):
        #print "left mouse click"
        ctypes.windll.user32.SetCursorPos(100, 20)
        #self.set_focus("UnityWndClass")
        ctypes.windll.user32.mouse_event(2, 0, 0, 0,0) # left down
        ctypes.windll.user32.mouse_event(4, 0, 0, 0,0) # left up
        #self.set_focus("TkTopLevel")
   
    def right_mouse_click(self):
        ctypes.windll.user32.SetCursorPos(100, 20)
        ctypes.windll.user32.mouse_event(8, 0, 0, 0,0) # right down
        ctypes.windll.user32.mouse_event(16, 0, 0, 0,0) # right up

    def set_rc_label(self, info):
        gutil.set_text(self.ui.lbl_remote_status, info[0], info[1])

    def dispatch_pressed(self):
        self.command("dispatch")

    def pause_pressed(self):
        self.command("pause")

    def get_ride_state(self):
        return self.state

    def report_coaster_status(self, text, color):
        self.coaster_status_str = format("%s,%s" % (text,color))
        gutil.set_text(self.ui.lbl_coaster_status, text, color) 
    
    def report_connection_status(self, text, color):
        self.connection_status_str =  format("%s,%s" % (text,color))
        gutil.set_text(self.ui.lbl_coaster_connection, text, color) 
    
    def form_telemetry_msg(self):
        # state,frame,is_paused;x,y,z,r,p,y;coaster_state;connection_state
        xyzrpy = ",".join('%0.4f' % item for item in self.get_transform())
        self.telemetry_msg = format("%d,%d,%d;%s;%s;%s\n" % (self.state,self.cosmetic_frame,self.is_paused,
                             xyzrpy, self.coaster_status_str,self.connection_status_str))
        return self.telemetry_msg

    def detected_remote(self, info):
        # fixme - is this needed?
        if "Detected Remote" in info:
            gutil.set_text(self.ui.lbl_remote_status, info, "green")
        elif "Looking for Remote" in info:
            gutil.set_text(self.ui.lbl_remote_status, info, "orange")
        else:
             gutil.set_text(self.ui.lbl_remote_status, info, "red")
            
    def quit(self):
        self.command("quit")

    def pause(self):
        log.debug("in pause, ride state is %s, Is_paused=%s", RideState.str(self.state), self.is_paused)
        if self.state == RideState.PAUSED:
                log.debug("Unpausing coaster")
                self.set_focus("UnityWndClass") # or could use window title:'Coaster MSU'
                self.is_paused = False
                self.state = RideState.RUNNING
                self.report_coaster_status("Coaster running", "green")
        elif self.state == RideState.RUNNING:
                log.debug("Pausing coaster")
                log.warning("if pause does not work, check space coaster local client MainWindow name")
                self.set_focus("Qt5QWindowIcon", "MainWindow") 
                self.is_paused = True
                self.state = RideState.PAUSED
                self.report_coaster_status("Coaster paused", "orange")

    def reset_vr(self):
        log.info("resetting Rift")
        self.right_mouse_click()

    def set_intensity(self, intensity_msg):
        self.command(intensity_msg)

    def emergency_stop(self):
        log.info("legacy emergency stop callback")
        self.deactivate()
 
    def command(self, cmd):
        # print(("command", cmd))
        if self.cmd_func is not None:
            log.debug("Requesting command: %s", cmd)
            self.cmd_func(cmd)
    
    def dispatch(self):
        self.left_mouse_click()
        log.debug("dispatched")
        self.frame_number = self.start_frame # start 1.5 seconds in

    def remote_info(self):
        log.warning("remote request for info not supported")

    def intensity_status_changed(self, intensity):
       gutil.set_text(self.ui.lbl_intensity_status, intensity[0], intensity[1])

    def activate(self):
        pass

    def deactivate(self):
        pass

    def begin(self, cmd_func, limits):
        self.cmd_func = cmd_func
        self.limits = limits  # note limits are in mm and radians
        self.read_telemetry()
        self.xyzrpyQ = Queue()
        self.cmdQ = Queue()
        # space coaster must be run on same pc running this client
        self.set_address(('', cfg.SPACE_COASTER_PORT))
                # space coaster must be run on same pc running this client
        self.set_address(('localhost', cfg.SPACE_COASTER_PORT))
        t = Thread(target=self.listener_thread, args= (self.get_address()))
        t.daemon = True
        t.start()
        self.connect()
        try:
            log.debug("attempting to set focus")
            self.set_focus("UnityWndClass","Coaster MSU")
            log.info("found space coaster window")
            self.left_mouse_click()
            # break
        except:
            print("fixme, unable to find coaster window")


    def fin(self):
        # client exit code goes here
        pass

    def connect(self):
        self.is_coaster_connected = -1
        self.sleep_func(2)
        while self.is_coaster_connected != 1:
            
            self.dialog.setWindowTitle('Coaster not detected')
            self.dialog.txt_info.setText("If coaster not yet started, start CoasterMSU")
            self.dialog.show()
            self.report_connection_status("Connecting to Coaster", "orange") 
            self.sleep_func(2)
        if self.is_coaster_connected == 0:
            self.report_connection_status("Not connected to Coaster", "red") 
        else:
            self.report_connection_status("Space Coaster Connected", "green") 
            self.dialog.close()

    def service(self):
        if self.is_coaster_connected == 0:
            self.report_connection_status("Not connected to Coaster", "red") 
        else:
            self.report_connection_status("Space Coaster Connected", "green") 
        msg = None
        try:
            while  self.cmdQ.qsize() > 0:
                sc_state = self.cmdQ.get()
                self.process_state(sc_state)

            if self.xyzrpyQ.qsize() == 0: 
                status = "Stopped at telemetry frame %d" % (self.frame_number - self.start_frame)
                self.report_coaster_status(status, "orange")
                if not self.is_paused:
                    log.warning("in service, setting is_paused True because coaster q is empty")
                    self.is_paused = True
            else:
                if self.state == RideState.RUNNING:
                    try:
                        self.set_transform(self.telemetry[self.frame_number])
                    except IndexError:
                         log.warning("Invalid telemetry frame, reset frame to 0")
                         self.frame_number = 0
                    #  print "coaster running", self.frame_number, [ '%.2f' % elem for elem in self.transform]
                    cosmetic_frame = self.frame_number - self.start_frame
                    self.cosmetic_frame = cosmetic_frame 
                    if self.frame_number % 20 == 0:
                                status = format("Running frame %d, time %d" % (cosmetic_frame, cosmetic_frame/20))
                                self.report_coaster_status(status, "green") 
                    self.frame_number += 1
        except Exception as e:
            s = traceback.format_exc()
            log.error("SC service error %s, %s, frame=%d", e, s, self.frame_number)

    def process_state(self, new_sc_state):
        if self.sc_state == new_sc_state:  return
        
        if self.sc_state == -1 and new_sc_state == SC_State.initializing:
            log.info("SC state transition to initial message from coaster")
            self.report_coaster_status("Starting software", "orange") 
            self.state = RideState.RESETTING
        elif self.sc_state == SC_State.initializing and new_sc_state == SC_State.waiting:
            log.info("SC state transition from startup to waiting in lobby")
            self.report_coaster_status("Loading coaster", "orange") 
            self.sleep_func(2)
            self.left_mouse_click()
            self.state = RideState.RESETTING
        elif self.sc_state == SC_State.waiting and new_sc_state == SC_State.ready:
            log.info("coaster is ready for dispatch")
            self.report_coaster_status("Ready for dispatch", "green")
            self.state = RideState.READY_FOR_DISPATCH
        elif self.sc_state == SC_State.ready and new_sc_state == SC_State.running :
            log.info("Coaster is starting run")
            self.report_coaster_status("Running", "Green")
            self.state = RideState.RUNNING
        elif self.sc_state == SC_State.running and new_sc_state == SC_State.completed:
            self.report_coaster_status("Entering hyperspace", "green")
            self.sleep_func(6)
            log.info("ready to reset")
            self.left_mouse_click()
            self.state = RideState.RESETTING
        elif self.sc_state == SC_State.completed and new_sc_state == SC_State.waiting:
            log.info("SC state transition from completed to waiting in lobby")
            self.report_coaster_status("Getting ready", "orange")
            self.sleep_func(2)
            self.left_mouse_click()
            self.state = RideState.RESETTING
        elif self.sc_state == SC_State.running and new_sc_state == SC_State.waiting:
            # this event happens if coaster sends running state after completed
            log.info("SC state transition from running to waiting in lobby")
            self.report_coaster_status("Waiting", "orange")
            self.sleep_func(2)
            self.left_mouse_click()
            self.state = RideState.RESETTING
        elif self.sc_state == SC_State.completed and new_sc_state == SC_State.running:
            # anomaly to be ignored
            self.sc_state = SC_State.completed
        elif self.sc_state == SC_State.running and new_sc_state == SC_State.initializing:
            # this happens because of a brief running state after completion
            pass 
        else:
            log.warning("Ignoring out of sequence transition from state %s to %s", self.sc_state_str[self.sc_state], self.sc_state_str[new_sc_state])
            
        self.sc_state = new_sc_state 
        # self.report_coaster_status("Coaster state is: " + self.sc_state_str[self.state], "green")

    def listener_thread(self, HOST, PORT, ):
        try:
            MAX_MSG_LEN = 512
            sc_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sc_sock.bind((HOST, PORT))
            log.info("opening space coaster socket on port %s:%d", HOST, PORT)
            while True:
                try:
                    msg = sc_sock.recv(MAX_MSG_LEN)
                    self.is_coaster_connected = 1
                    # print msg
                    msg = msg.rstrip()
                    if msg.find("accel") == 0: 
                        msg = msg.replace(" ", "") # remove whitespace
                        accel = msg.split(',')
                        if not all(v == '0' for v in accel[1:7]): 
                            self.xyzrpyQ.put(accel[1:7])
                    elif msg.find("state") == 0:
                        s = msg.split(',')
                        self.cmdQ.put(int(s[1])) # state messages go onto command queue
                    elif "command" in msg:
                        #print msg
                        pass
                except Exception as e:
                    s = traceback.format_exc()
                    if msg:
                        log.error("listener err %s,%s, msg(%s)", e, s, msg)
                    else:
                        log.error("listener err %s,%s", e, s)
                    self.is_coaster_connected = 0
                    self.report_connection_status("Coaster connection error", "red")
        except Exception as e:
            s = traceback.format_exc()
            log.fatal("Space coaster connection thread init err %s,%s", e, s)
            self.is_coaster_connected = 0

    def read_telemetry(self):
        try:
            path = os.path.abspath('clients/SpaceCoaster/chairGen_telemetry.csv')
            if not os.path.isfile(path): path = 'chairGen_telemetry.csv'
            with open(path, 'rb') as csvfile:
                log.info("opened space coaster telemetry file: chairGen_telemetry.csv")
                rows = csv.reader(csvfile, delimiter=',');
                for row in rows:
                    #  print row
                    if row is not None:
                        if len(row) >=6:
                            data = [float(f) for f in row[:6]]
                            # normalize
                            for idx, level in enumerate(data):
                                data[idx] = self.scale( data[idx], [-self.max_values[idx], self.max_values[idx], -1, 1] )
                            # print data
                            self.telemetry.append(data)
                log.info("Read %d frames into telemetry frame list",  (len(self.telemetry)))
                # following scales values to limits of configured platform 
                max = np.max(self.telemetry, axis = 0)
                min = np.min(self.telemetry, axis = 0)
                pos_factor = np.nan_to_num(self.limits/max)
                neg_factor = np.nan_to_num(self.limits/min)*-1
                #self.telemetry *= np.where(self.telemetry > 0, pos_factor,neg_factor)
                self.telemetry *= np.asarray([.7,.7,.7,.7,.7,.7])
                # print "new max", np.max(self.telemetry, axis = 0)
                # print "new min", np.min(self.telemetry, axis = 0)
                self.telemetry = np.asarray(self.telemetry, dtype=np.float32)
                # np.set_printoptions(precision=3,suppress=T
                # print self.telemetry
        except Exception as e:
            s = traceback.format_exc()
            log.error("Error reading telemetry file %s %s", e,s)
            
    #function to scale a value, range is a list containing: (from_min, from_max, to_min, to_max)   
    def scale(self, value, range):
        if value > range[1]:  # limit max
            return range[3]
        if value < range[0]:  # limit min
            return range[2]       
        if range[1] == range[0]:
            return range[2] #avoid div by zero error
        else:      
            return ( (value - range[0]) / (range[1] - range[0]) ) * (range[3] - range[2]) + range[2]

if __name__ == "__main__":
    from clients.local_client import client_main, LocalClient #  code used to run this client on external pc
    client = InputInterface(True) 
    client_main(client)
