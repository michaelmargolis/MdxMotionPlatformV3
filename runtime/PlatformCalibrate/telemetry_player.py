"""
  telemetry_player
  
  This version reads telemetry data from a comma separated .tlm file
  Attitude information is read from this file can be synced to VR player

"""

import sys
from math import radians, degrees
import time
import traceback
import csv,os
#  from Queue import Queue
import numpy as np
import SpaceCoaster_itf as sc


class Telemetry(object):
    """
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
    """

    def __init__(self, callback, limits):
        #  set True if input range is -1 to +1
        self.log = None
        self.is_normalized = True
        self.is_running = False
        self.expect_degrees = False # convert to radians if True
        self.move_func = callback
        self.limits = limits
        
        self.max_values = [80, 80, 80, 0.4, 0.4, 0.4]
        self.levels = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0] # pre normalized
        
        self.normalized = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.previous_msg_time = 0;
        self.telemetry = []

        self.frame_interval = 0.05 # 20 frames per second
        self.start_time = 0
        self.frame_number = 0

        self.coaster = sc.SimInterface()
        self.is_spacecoaster = False


    def start(self, client):
        self.read(client + ".tlm") 
        if client == "SpaceCoaster":
            self.is_spacecoaster = True
            if self.coaster.is_started == False:
                self.coaster.init_gui()

    def stop(self):
        print "todo telemetry stop"

    def service(self):
        msg = None
        if self.is_spacecoaster:
            self.frame_number = self.coaster.service()
            if self.frame_number == None:
                return
        else:
            self.frame_number += 1
        try:
            if self.frame_number >= len(self.telemetry):
                return 101  # finished
            self.levels = self.telemetry[self.frame_number]
            if self.move_func:
                self.move_func(self.levels)
            """    
            if self.coaster.state == sc.State.running:
                print "process frame"
            else:
                #print "not receiving UPD data"
                pass
            """
            return 100 * (float(self.frame_number)/len(self.telemetry))

        except:  
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print "service error", e, s
            print "frame=", self.frame_number

    def read(self, path): 
        try: 
            with open(path, 'rb') as csvfile:
                rows = csv.reader(csvfile, delimiter=',');
                telemetry = []
                for row in rows:
                    #  print row
                    if row is not None:
                        if len(row) >=6:
                            data = [float(f) for f in row[:6]]
                            # normalize
                            #  for idx, level in enumerate(data):
                            #      data[idx] = self.scale( data[idx], [-self.max_values[idx], self.max_values[idx], -1, 1] )
                            # print data
                            telemetry.append(data)
                #  print format("read %d frames into telemetry frame list" % (len(self.telemetry)))
                self.telemetry = np.asarray(telemetry, dtype=np.float32)
                np.set_printoptions(precision=3,suppress=True)
                #  print self.telemetry_player
                
                # following scales values to limits of configured platform 
                max = np.max(self.telemetry, axis = 0)
                min = np.min(self.telemetry, axis = 0)
                pos_factor = np.nan_to_num(self.limits/max)
                neg_factor = np.nan_to_num(self.limits/min)*-1
                self.telemetry *= np.where(self.telemetry > 0, pos_factor,neg_factor)
                print "new max", np.max(self.telemetry, axis = 0)
                print "new min", np.min(self.telemetry, axis = 0)
                np.savetxt("SpaceCoasterLimited.csv",self.telemetry, delimiter=',') 
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
    def cb(xyzrpy):
       print xyzrpy
       
    import os,time
    t = Telemetry(cb)
    cwd = os.getcwd()
    fname = os.path.join(cwd, "SpaceCoaster.tlm")
    print fname
    t.start(fname)
    if len(t.telemetry) == 0:
        print "unable to read telemetry file", fname
    else:
       for xyzrpy in t.telemetry:
            print xyzrpy
            time.sleep(t.frame_interval/5)  # 5x speed
       
    