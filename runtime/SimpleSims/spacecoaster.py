"""
  Simple spacecoaster 

  Receives UDP xtatus messages on port 10009
  telemetry input from file

  this script converts input to normalized values  
  
  Command messages are:
  "command,enable,\n"   : activate the chair for movement
  "command,disable,\n"  : disable movement and park the chair
  "command,exit,\n"     : shut down the application
"""

import sys
import os
import socket
from math import radians, degrees
import threading
import time
from queue import Queue
import traceback
import csv,os
import logging as log
#from serial_remote import SerialRemote


import ctypes # for mouse

class State:
    initializing, waiting, ready, running, completed = range(0,5)

class RideState:  # only used to contol LED in remote
    DISABLED, READY_FOR_DISPATCH, RUNNING, PAUSED, EMERGENCY_STOPPED, RESETTING = range(6)


class Sim(object):
    
    def set_focus(self, window_class):
        # not used in this version
        #needs: import win32gui # for set_focus
        guiHwnd = win32gui.FindWindow(window_class,None)
        print(guiHwnd)
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


    def __init__(self, sleep_func, interval_ms = 25):
        self.sleep_func = sleep_func
        self.interval_ms = interval_ms
        self.name = "Space Coaster"
        self.is_started = False
        self.is_normalized = True
        self.expect_degrees = False # convert to radians if True
        self.HOST = ""
        self.PORT = 10009
        if self.is_normalized:
            log.info('Platform Input is UDP with normalized parameters')
        else:
            log.info('Platform Input is UDP with realworld parameters')
   
        self.max_values = [80, 80, 80, 0.4, 0.4, 0.4]
        self.levels = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0] # pre normalized
        
        self.normalized = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.previous_msg_time = 0;
        self.telemetry = []

        self.start_frame = 0
        self.start_time = 0
        self.frame_number = 0

        self.state_strings = ("Initializing", "Waiting", "Ready", "Running", "Completed")
        self.state = -1 # state not yet set
        self.state_callback = None # pass state info if set

        self.rootTitle = "Space Coaster interface"
        self.xyzrpyQ = Queue()
        self.cmdQ = Queue()
        self.thread_handle = None # listener thread started in connect method
        
        """
        actions = {'detected remote': self.detected_remote, 'activate': self.activate,
           'deactivate': self.deactivate, 'pause': self.pause, 'dispatch': self.dispatch,
           'reset': self.reset_vr, 'emergency_stop': self.emergency_stop, 'intensity' : self.set_intensity}
        self.RemoteControl = SerialRemote(actions)
        """
        self.read_telemetry()
        self.cmd_func = None
        self.move_func = None
     
    """     
    def detected_remote(self, info):
        if "Detected Remote" in info:
             self.remote_status_label.config(text=info, fg="green3")
        elif "Looking for Remote" in info:
            self.remote_status_label.config(text=info, fg="orange")
        else:
            self.remote_status_label.config(text=info, fg="red")
    """
  
    def set_norm_factors(self, norm_factors):
        # values for each element that when multiplied will normalize data to a range of +- 1 
        self.norm_factors = norm_factors

    def set_state_callback(self, callback):
        self.state_callback = callback

    def select_ride_callback(self, cb):
        pass # space coaster cannot select ride

    def load(self, loader):
        # this method is not used by agent_startup
        try:
            log.info("Starting Spacecoaster executing: " + loader)
            os.startfile(loader)
            return("loading...")  # is this used??
        except Exception as e:
            print(e)
            return(str(e)) 

    def connect(self):
        # returns string code or None if no error
        if self.thread_handle  == None:
            try:
                self.thread_handle = threading.Thread(target=self.listener_thread, args= (self.HOST, self.PORT))
                self.thread_handle.daemon = True
                self.thread_handle.start()
                self.is_connected = True
                return None 
            except ConnectionError:
                return "Not connecting, is Space Coaster loaded?"
            except Exception as e:
                log.info("Space Coaster connect err: " + str(e)) 
                return(e)
       
        else:
            return None # already connected
      
    def run(self):
        self.left_mouse_click()
        log.debug("dispatched")
        self.frame_number = self.start_frame

    def pause(self):
        self.command("swellForStairs")

    def read(self):
        self.service()
        # print(time.time() - self.start_time)
        nbr_frames = len(self.telemetry)
        self.report_state("Running frame %d of %d" % (self.frame_number, nbr_frames))  
        # print("in read:", self.levels, time.time())
        return self.levels

            
    def reset_vr(self):
         self.right_mouse_click()

    def set_intensity(self, intensity_msg):
        self.command(intensity_msg)

    def emergency_stop(self):
        print("legacy emergency stop callback")
 
    def command(self, cmd):
        if self.cmd_func is not None:
            print( "Requesting command:", cmd)
            self.cmd_func(cmd)
    
    def dispatch(self):
        print('dispatch')
        self.command("ready")  # slow rise of platform
        self.command("unparkPlatform")
        self.left_mouse_click()
        print( "dispatched" )
        self.frame_number = 30 # start 1.5 seconds removed
    

    def begin(self, cmd_func, move_func, limits):
        self.cmd_func = cmd_func
        self.move_func = move_func
        self.limits = limits  # note limits are in mm and radians

    def service(self):
        # self.RemoteControl.service()
        try:
            while self.cmdQ.qsize() > 0:
                cmd = self.cmdQ.get()
                print("command=", cmd)
                self.process_command_msg(cmd) 

            if(self.xyzrpyQ.qsize() > 0):
                if self.state == State.running:
                    #self.coaster_connection_label.config(text="Receiving coaster data", fg="green3")
                    # only process messages if coaster is sending data
                    if self.frame_number < len(self.telemetry):
                        self.levels = self.telemetry[self.frame_number]
                        #  print [ '%.2f' % elem for elem in self.levels]
                        self.frame_number += 1
                        if self.move_func:
                            self.move_func(self.levels)
                        x = self.xyzrpyQ.get()
                        while self.xyzrpyQ.qsize() > 2:
                            x1 = self.xyzrpyQ.get()
                            ##  print x
                            x=x1 
                        self.xyzrpyQ.queue.clear()
                        return self.frame_number
        except Exception as e:  
            s = traceback.format_exc()
            print( "service error", e, s)
        return None

    def report_state(self, state_info):
        if self.state_callback:
            self.state_callback(state_info)
            
    def process_state(self, new_state):
        if self.state == -1 and new_state == State.initializing:
            print( "State transition to inital message from coaster")
        elif self.state == State.initializing and new_state == State.waiting:
            self.report_state("Space Coaster waiting in lobby")
            time.sleep(2)
            self.left_mouse_click()
        elif self.state == State.waiting and new_state == State.ready:
            pass
            # self.RemoteControl.send(str(RideState.READY_FOR_DISPATCH))
            self.report_state("Space Coaster ready for dispatch")
        elif self.state == State.ready and new_state == State.running :
            #  self.activate()
            self.report_state("Space Coaster starting run")
            self.start_time = time.time()
            self.frame_number = self.start_frame
            #self.RemoteControl.send(str(RideState.RUNNING))
        elif self.state == State.running and new_state == State.completed:
            self.report_state("Space Coaster run completed")
            time.sleep(6)
            # print "ready to reset"
            self.left_mouse_click()
            #self.RemoteControl.send(str(RideState.RESETTING))
            #  self.deactivate()
        elif self.state == State.completed and new_state == State.waiting:
            self.report_state("Space Coaster waiting in lobby")
            time.sleep(2)
            self.left_mouse_click()
        elif self.state == State.running and new_state == State.waiting:
            # this event happens if coaster sends running state after completed
            self.report_state("Space Coaster waiting in lobby")
            time.sleep(2)
            self.left_mouse_click()
        else:
            print( "Ignoring out of sequence transition from state", self.state_strings[self.state], "to", self.state_strings[new_state])
            
        self.state = new_state 
        # print("Coaster state is: " + self.state_strings[self.state])
         
    def process_command_msg(self, msg):
        msg = msg.rstrip()
        fields = msg.split(",")
        if fields[0] == "command":
            print( "command is {%s}:" % (fields[1]))
            self.cmd_label.config(text="Most recent command: " + fields[1])
            if self.cmd_func:
                self.cmd_func(fields[1])
        elif fields[0] == "config":
            print( "config mesage is {%s}:" % (fields[1]))
            self.process_config_msg(fields[1])
        elif fields[0] == "state":
            try:
               new_state = int(fields[1])
               self.process_state(new_state)
            except ValueError:
                print( "bad state mesage: {%s}:" % (fields[1]))

           
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


    def listener_thread(self, HOST, PORT):
        try:
            self.MAX_MSG_LEN = 80
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.bind((HOST, PORT))
            log.info( format("opening socket on port %d" % PORT))
            # self.xyzrpyQ = xyzrpyQ
        except Exception as e:
            s = traceback.format_exc()
            log.error("format(thread init err %s, %s" % str(e), str(s))
        while True:
            try:
                msg = client.recv(self.MAX_MSG_LEN).decode('utf-8')
                if msg is not None:
                    if msg.find("xyzrpy") == 0:
                        now = time.time()
                        self.xyzrpyQ.put([now,msg])
                    elif msg.find("command") == 0:
                        self.cmdQ.put(msg)
                    elif msg.find("config") == 0:
                        self.cmdQ.put(msg) # config messages go onto command queue
                    elif msg.find("state") == 0:
                        self.cmdQ.put(msg) # state messages go onto command queue
               
            except Exception as e:
                s = traceback.format_exc()
                log.error(format("listener err %s, %s" % str(e), str(s)))

    def read_telemetry(self):
        try:    
            # cwd = os.getcwd()
            # path = os.path.join(cwd, "SimpleSims/spacecoaster_telemetry.csv")
            path = "SimpleSims\\spacecoaster_telemetry.csv"
            with open(path, 'r') as csvfile:
                rows = csv.reader(csvfile, delimiter=',');
                for row in rows:
                    #  print row
                    if row is not None:
                        if len(row) >=6:
                            data = [float(f) for f in row[:6]]
                            # normalize
                            for idx, level in enumerate(data):
                                data[idx] = self.scale( data[idx], [-self.max_values[idx], self.max_values[idx], -1, 1] )
                            # print( data)
                            self.telemetry.append(data)
                log.info( format("read %d frames into telemetry frame list" % (len(self.telemetry))))
                #print self.telemetry
        except Exception as e:
            s = traceback.format_exc()
            log.error("Error reading telemetry file", e,s)
            
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
    import time
    Desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') + '/Vr/'
    coaster = Sim(time.sleep)
    coaster.load(Desktop + "SpaceCoaster.lnk")
    coaster.connect()
    input("press return to start ")
    coaster.run()
    while True:
        coaster.service()
        time.sleep(.05)        
            