"""
  Space_coaster_itf for V3 software
  
  This version reads telemetry data from a CSV file
  Attitude information is read from this file synced to UDP frames
  sent by SpaceCoaster on port 10009 (data in coaster msg frames is ignored)
"""

import sys
import socket
from math import radians, degrees
import threading
import time
from Queue import Queue
import traceback
import csv,os

from space_coaster_gui_defs import *

import logging
log = logging.getLogger(__name__)

import ctypes # for mouse
import numpy as np  # for scaling telemetry data

class State:
    initializing, waiting, ready, running, completed = range(0,5)

class RideState:  # only used to contol LED in remote
    DISABLED, READY_FOR_DISPATCH, RUNNING, PAUSED, EMERGENCY_STOPPED, RESETTING = range(6)
    
ride_state_str = {'Disabled','Ready for Dispatch','Running','Paused','Emergency Stopped','Resetting'}

class SpaceCoasterItf(object):

    def __init__(self, sleep_func):
        self.sleep_func = sleep_func
        self.log = None
        self.is_normalized = True
        self.expect_degrees = False # convert to radians if True
        self.HOST = "localhost"
        self.PORT = 10009
        if self.is_normalized:
            print 'Platform Input is UDP with normalized parameters'
        else:
            print 'Platform Input is UDP with realworld parameters'
   
        self.max_values = [80, 80, 80, 0.4, 0.4, 0.4]
        self.levels = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0] # pre normalized
        
        self.normalized = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.previous_msg_time = 0;
        self.previous_msg_time = 0;
        self.telemetry = []
        # duration = 95 # check this is big enough
        # self.telemetry = [[0.0 for vals in range(6)] for interval in range(duration * 20)]
        #print self.telemetry

        self.start_time = 0
        self.frame_number = 0

        self.state_strings = ("Initializing", "Waiting", "Ready", "Running", "Completed")
        self.state = -1 # state not yet set

        self.rootTitle = "Space Coaster interface"
        self.xyzrpyQ = Queue()
        self.cmdQ = Queue()
        t = threading.Thread(target=self.listener_thread, args= (self.HOST, self.PORT))
        t.daemon = True
        t.start()


    def set_focus(self, window_class):
        # not used in this version
        #needs: import win32gui # for set_focus
        guiHwnd = win32gui.FindWindow(window_class,None)
        print guiHwnd
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

    def quit(self):
        self.command("quit")

    def pause(self):
        self.command("swellForStairs")
        
    def reset(self):
         self.right_mouse_click()

    def set_intensity(self, intensity_msg):
        self.command(intensity_msg)

    def emergency_stop(self):
        print "legacy emergency stop callback"
        self.deactivate()
 
    def command(self, cmd):
        if self.cmd_func is not None:
            print "Requesting command:", cmd
            self.cmd_func(cmd)
    
    def dispatch(self):
        self.left_mouse_click()
        log.debug("dispatched")
        self.frame_number = 30 # start 1.5 seconds in


    def begin(self, cmd_func, move_func, limits):
        self.cmd_func = cmd_func
        self.move_func = move_func
        self.limits = limits  # note limits are in mm and radians
        self.read_telemetry()

    def fin(self):
        # client exit code goes here
        pass
        
        
    def get_telemetry(self, timeout):


    def service(self):
        self.SerialRemoteControl.service()
        self.UdpRemoteControl.service()
        msg = None
        try:
            while self.cmdQ.qsize() > 0:
                cmd = self.cmdQ.get()
                self.process_command_msg(cmd) 

            if(self.xyzrpyQ.qsize() > 0):
                if self.state == State.running:
                    # self.set_text(self.ui.lbl_coaster_connection,"Receiving coaster data", "green")
                    # only process messages if coaster is sending data
                    self.levels = self.telemetry[self.frame_number]
                    #  print self.frame_number, [ '%.2f' % elem for elem in self.levels]
                    self.frame_number += 1
                    if self.move_func:
                        self.move_func(self.levels)
                    x = self.xyzrpyQ.get()
                    while self.xyzrpyQ.qsize() > 2:
                        x1 = self.xyzrpyQ.get()
                        # print x
                        x=x1
                    self.xyzrpyQ.queue.clear()
                    if self.frame_number % 20 == 0:
                        self.UdpRemoteControl.send(format("time,%d,%d," % (self.frame_number/20, len(self.telemetry)/20)))
                        status = format("Telemetry frame %d, time %d" % (self.frame_number, self.frame_number/20))
                        self.set_text(self.ui.lbl_coaster_connection, status, "green")
            else:
                self.set_text(self.ui.lbl_coaster_connection, "No longer receiving coaster data", "orange")

        except:  
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print "service error", e, s
            print "frame=", self.frame_number

    def process_state(self, new_state):
        if self.state == -1 and new_state == State.initializing:
            log.debug("State transition to initial message from coaster")
        elif self.state == State.initializing and new_state == State.waiting:
            log.debug("State transition from startup to waiting in lobby")
            self.sleep_func(2)
            self.left_mouse_click()
        elif self.state == State.waiting and new_state == State.ready:
            self.SerialRemoteControl.send(str(RideState.READY_FOR_DISPATCH))
            self.UdpRemoteControl.send("state," + "Ready for Dispatch")
            log.debug("coaster is ready for dispatch")
        elif self.state == State.ready and new_state == State.running :
            self.activate()
            log.debug("Coaster is starting run")
            self.start_time = time.time()
            self.SerialRemoteControl.send(str(RideState.RUNNING))
            self.UdpRemoteControl.send("state," + "Running")
        elif self.state == State.running and new_state == State.completed:
            print "State transition from running to completed"
            self.sleep_func(6)
            log.debug("ready to reset")
            self.left_mouse_click()
            self.SerialRemoteControl.send(str(RideState.RESETTING))
            self.UdpRemoteControl.send("state," + "Resetting")
            self.deactivate()
        elif self.state == State.completed and new_state == State.waiting:
            log.debug("State transition from completed to waiting in lobby")
            self.sleep_func(2)
            self.left_mouse_click()
        elif self.state == State.running and new_state == State.waiting:
            # this event happens if coaster sends running state after completed
            log.debug("State transition from running to waiting in lobby")
            self.sleep_func(2)
            self.left_mouse_click()
        else:
            print "Ignoring out of sequence transition from state", self.state_strings[self.state], "to", self.state_strings[new_state]
            
        self.state = new_state 
        self.set_text(self.ui.lbl_coaster_status, "Coaster state is: " + self.state_strings[self.state], "green")
         
    def process_command_msg(self, msg):
        msg = msg.rstrip()
        fields = msg.split(",")
        if fields[0] == "command":
            log.debug("command is {%s}:", (fields[1]))
            # self.cmd_label.config(text="Most recent command: " + fields[1])
            if self.cmd_func:
                self.cmd_func(fields[1])
        elif fields[0] == "config":
            log.debug("config mesage is {%s}:", (fields[1]))
            self.process_config_msg(fields[1])
        elif fields[0] == "state":
            try:
               new_state = int(fields[1])
               self.process_state(new_state)
            except ValueError:
                log.error("bad state mesage: {%s}:", (fields[1]))

    def listener_thread(self, HOST, PORT):
        try:
            self.MAX_MSG_LEN = 100
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.bind((HOST, PORT))
            print "opening socket on", PORT
            # self.xyzrpyQ = xyzrpyQ
        except:
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print "thread init err", e, s
        while True:
            try:
                msg = client.recv(self.MAX_MSG_LEN).rstrip()
                if msg is not None:                
                    if msg.find("xyzrpy") == 0:
                        now = time.time()
                        self.xyzrpyQ.put([now,msg])
                    elif msg.find("accel") == 0: 
                       accel = msg.split(',')
                       print accel[1:]
                       if not all(v = 0 for v in values)
                          print "accel not zero"
                          log.debug("SC non zero: frame=%d", self.frame_number)
                    elif msg.find("command") == 0:
                        self.cmdQ.put(msg)
                    elif msg.find("config") == 0:
                        self.cmdQ.put(msg) # config messages go onto command queue
                    elif msg.find("state") == 0:
                        self.cmdQ.put(msg) # state messages go onto command queue
               
            except:
                e = sys.exc_info()[0]
                s = traceback.format_exc()
                print "listener err", e, s
                print "message=", msg, len(msg)

    def read_telemetry(self):
        try:
            path = os.path.abspath('space_coaster/chairGen_telemetry.csv')
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
        except:
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print "Error reading telemetry file", e,s
            
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

    import logging as log
    import logging.handlers