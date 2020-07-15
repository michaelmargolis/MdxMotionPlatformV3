"""
  Space_coaster itf for test UI)

  Receives UDP xtatus messages on port 10009
  telemetry input from file

  this script converts input to normalized values  
  
  Command messages are:
  "command,enable,\n"   : activate the chair for movement
  "command,disable,\n"  : disable movement and park the chair
  "command,exit,\n"     : shut down the application
"""

import sys
import socket
from math import radians, degrees
import threading
import time
from Queue import Queue
import Tkinter as tk
import traceback
import csv,os
from serial_remote import SerialRemote


import ctypes # for mouse

class State:
    initializing, waiting, ready, running, completed = range(0,5)

class RideState:  # only used to contol LED in remote
    DISABLED, READY_FOR_DISPATCH, RUNNING, PAUSED, EMERGENCY_STOPPED, RESETTING = range(6)


class InputInterface(object):
    USE_GUI = True  # set True if using tkInter
    print "USE_GUI", USE_GUI
    
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


    def __init__(self):
        #  set True if input range is -1 to +1
        self.is_started = False
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
        self.telemetry = []
        # duration = 95 # check this is big enough
        # self.telemetry = [[0.0 for vals in range(6)] for interval in range(duration * 20)]
        print self.telemetry

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
        
        actions = {'detected remote': self.detected_remote, 'activate': self.activate,
           'deactivate': self.deactivate, 'pause': self.pause, 'dispatch': self.dispatch,
           'reset': self.reset_vr, 'emergency_stop': self.emergency_stop, 'intensity' : self.set_intensity}
        self.RemoteControl = SerialRemote(actions)

        #  self.read_telemetry()
        self.cmd_func = None
        self.move_func = None
        
    def init_gui(self):
        master = tk.Tk()
        self.master = master
        frame = tk.Frame(master)
        frame.grid()
        spacer_frame = tk.Frame(master, pady=4)
        spacer_frame.grid(row=0, column=0)
        self.label0 = tk.Label(spacer_frame, text="").grid(row=0)

        self.dispatch_button = tk.Button(master, height=2, width=16, text="Dispatch",
                                         command=self.dispatch, underline=0)
        self.dispatch_button.grid(row=1, column=0, padx=(24, 4))

        self.pause_button = tk.Button(master, height=2, width=16, text="Prop", command=self.pause, underline=0)
        self.pause_button.grid(row=1, column=2, padx=(30))

        self.reset_button = tk.Button(master, height=2, width=16, text="Reset Rift",
                                      command=self.reset_vr, underline=0)
        self.reset_button.grid(row=1, column=3, padx=(24))

        label_frame = tk.Frame(master, pady=20)
        label_frame.grid(row=3, column=0, columnspan=4)

        self.coaster_status_label = tk.Label(label_frame, text="Waiting for Coaster Status", font=(None, 24),)
        self.coaster_status_label.grid(row=1, columnspan=2, ipadx=16, sticky=tk.W)

        self.intensity_status_Label = tk.Label(label_frame, font=(None, 12),
                 text="Intensity", fg="orange")
        self.intensity_status_Label.grid(row=2, column=0, columnspan=2, ipadx=16, sticky=tk.W)
        
        self.coaster_connection_label = tk.Label(label_frame, fg="orange", font=(None, 12),
               text="Waiting for data from Coaster Software (start Coaster.exe if not started)")
        self.coaster_connection_label.grid(row=3, columnspan=2, ipadx=16, sticky=tk.W)

        self.remote_status_label = tk.Label(label_frame, font=(None, 12),
                 text="Looking for Remote Control", fg="orange")
        self.remote_status_label.grid(row=4, columnspan=2, ipadx=16, sticky=tk.W)

        self.chair_status_Label = tk.Label(label_frame, font=(None, 12),
                 text="Using Festo Controllers", fg="orange")
        self.chair_status_Label.grid(row=5, column=0, columnspan=2, ipadx=16, sticky=tk.W)

        bottom_frame = tk.Frame(master, pady=16)
        bottom_frame.grid(row=5, columnspan=3)

        self.is_chair_activated = tk.IntVar()
        self.is_chair_activated.set(0)  # disable by default

        self.activation_button = tk.Button(master, underline=0, command=self.activate)
        self.activation_button.grid(row=4, column=1)
        self.deactivation_button = tk.Button(master, command=self.deactivate)
        self.deactivation_button.grid(row=4, column=2)
        self.set_activation_buttons(False)

        self.close_button = tk.Button(master, text="Shut Down and Exit", command=self.quit)
        self.close_button.grid(row=4, column=3)

        self.label1 = tk.Label( bottom_frame, text="     ").grid(row=0, column=1)

        self.org_button_color = self.dispatch_button.cget("background")
        self.is_started = True

    def detected_remote(self, info):
        if "Detected Remote" in info:
             self.remote_status_label.config(text=info, fg="green3")
        elif "Looking for Remote" in info:
            self.remote_status_label.config(text=info, fg="orange")
        else:
            self.remote_status_label.config(text=info, fg="red")
            
    def quit(self):
        self.command("quit")
        
    def activate(self):
        self.command("enable")
        self.set_activation_buttons(True)

    def deactivate(self):
        self.command("disable")
        self.set_activation_buttons(False)

    def set_activation_buttons(self, isEnabled): 
        if isEnabled:
            self.activation_button.config(text="Activated ", relief=tk.SUNKEN)
            self.deactivation_button.config(text="Deactivate", relief=tk.RAISED)
        else:
            self.activation_button.config(text="Activate ", relief=tk.RAISED)
            self.deactivation_button.config(text="Deactivated", relief=tk.SUNKEN)

    def pause(self):
        self.command("swellForStairs")
        
    def reset_vr(self):
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
        print 'dispatch'
        self.command("ready")  # slow rise of platform
        self.command("unparkPlatform")
        print "todo check delay is needed to free platform"
        #  self._sleep_func(1)
        self.left_mouse_click()
        print "dispatched" 
        self.frame_number = 30 # start 1.5 seconds removed
    
    def intensity_status_changed(self, intensity):
       self.intensity_status_Label.config(text=intensity[0], fg=intensity[1])

    def begin(self, cmd_func, move_func, limits):
        self.cmd_func = cmd_func
        self.move_func = move_func
        self.limits = limits  # note limits are in mm and radians

    def fin(self):
        # client exit code goes here
        pass
        
    def get_current_pos(self):
        return self.levels

    def service(self):
        self.RemoteControl.service()
        try:
           self.master.update_idletasks()
           self.master.update()
        except:
            pass  

        try:
            while self.cmdQ.qsize() > 0:
                cmd = self.cmdQ.get()
                self.process_command_msg(cmd) 

            if(self.xyzrpyQ.qsize() > 0):
                if self.state == State.running:
                    self.coaster_connection_label.config(text="Receiving coaster data", fg="green3")
                    # only process messages if coaster is sending data
                    ##  self.levels = self.telemetry[self.frame_number]
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
            else:
                try:
                    self.coaster_connection_label.config(text="No longer receiving coaster data", fg="orange")
                except:
                    pass
        except Exception as e:  
            s = traceback.format_exc()
            print "service error", e, s
        return None

    def process_state(self, new_state):
        if self.state == -1 and new_state == State.initializing:
            print "State transition to inital message from coaster"
        elif self.state == State.initializing and new_state == State.waiting:
            print "State transition from startup to waiting in lobby"
            time.sleep(2)
            self.left_mouse_click()
        elif self.state == State.waiting and new_state == State.ready:
            self.RemoteControl.send(str(RideState.READY_FOR_DISPATCH))
            print "coaster is ready for dispatch"
        elif self.state == State.ready and new_state == State.running :
            self.activate()
            print "Coaster is starting run"
            self.start_time = time.time()
            self.RemoteControl.send(str(RideState.RUNNING))
        elif self.state == State.running and new_state == State.completed:
            print "State transition from running to completed"
            time.sleep(6)
            print "ready to reset"
            self.left_mouse_click()
            self.RemoteControl.send(str(RideState.RESETTING))
            self.deactivate()
        elif self.state == State.completed and new_state == State.waiting:
            print "State transition from completed to waiting in lobby"
            time.sleep(2)
            self.left_mouse_click()
        elif self.state == State.running and new_state == State.waiting:
            # this event happens if coaster sends running state after completed
            print "State transition from running to waiting in lobby"
            time.sleep(2)
            self.left_mouse_click()
        else:
            print "Ignoring out of sequence transition from state", self.state_strings[self.state], "to", self.state_strings[new_state]
            
        self.state = new_state 
        self.coaster_status_label.config(text="Coaster state is: " + self.state_strings[self.state])
         
    def process_command_msg(self, msg):
        msg = msg.rstrip()
        fields = msg.split(",")
        if fields[0] == "command":
            print "command is {%s}:" % (fields[1])
            self.cmd_label.config(text="Most recent command: " + fields[1])
            if self.cmd_func:
                self.cmd_func(fields[1])
        elif fields[0] == "config":
            print "config mesage is {%s}:" % (fields[1])
            self.process_config_msg(fields[1])
        elif fields[0] == "state":
            try:
               new_state = int(fields[1])
               self.process_state(new_state)
            except ValueError:
                print "bad state mesage: {%s}:" % (fields[1])

           
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
            print "opening socket on", PORT
            # self.xyzrpyQ = xyzrpyQ
        except Exception as e:
            s = traceback.format_exc()
            print "thread init err", e, s
        while True:
            try:
                msg = client.recv(self.MAX_MSG_LEN)
                if msg is not None:
                    # print "MSG",msg 
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
                print "listener err", e, s

    def read_telemetry(self):
        try:    
            # path = os.path.abspath('space_coaster/chairGen_telemetry.csv')
            cwd = os.getcwd()
            path = os.path.join(cwd, "chairGen_telemetry.csv")
            with open(path, 'rb') as csvfile:
                rows = csv.reader(csvfile, delimiter=',');
                for row in rows:
                    #  print row
                    if row is not None:
                        if len(row) >=6:
                            data = [float(f) for f in row[:6]]
                            # normalize
                            for idx, level in enumerate(data):
                                data[idx] = self.scale( data[idx], [-self.max_values[idx], self.max_values[idx], -1, 1] )
                            print data
                            self.telemetry.append(data)
                print format("read %d frames into telemetry frame list" % (len(self.telemetry)))
                #print self.telemetry
        except Exception as e:
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

    coaster = InputInterface()
    coaster.init_gui()
    while True:
        coaster.service()
        time.sleep(.05)        
            