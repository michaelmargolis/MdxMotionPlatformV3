"""
  condor.py

  Receives UDP messages on port 55278 from Condor flight sim 

  
"""

import sys
import time
import numpy as np
import socket
import threading
from Queue import Queue
import Tkinter as tk
import traceback

dummy = "time=12.0225369024886\nairspeed=1.78508853912354\naltitude=1642.98791503906\nvario=6.26458131591789E-5\n\n"

#from telemetry_logger import TelemetryLogger
#logger = TelemetryLogger(False)

test_msg_org = '{"LinearAcceleration": "x:0.005790,y:0.033458,z:0.000686","AngularAcceleration": "x:0.000000,y:-0.000000,z:0.000013","IsDocked": "1","FSDDeparting": "0","FSDArriving": "0","FSDChargeProp": "0.000000"}'
test_msg = '{"LinearAcceleration": [0.005790,0.033458,0.000686],"AngularAcceleration": [0.000000,-0.000000,0.013],"IsDocked": "1","FSDDeparting": "0","FSDArriving": "0","FSDChargeProp": "0.000000"}'

class InputInterface(object):
    USE_GUI = True  # set True if using tkInter 
    
    def __init__(self):
        self.rootTitle = "Condor Flight Sim Interface"
        self.HOST = ""
        self.PORT = 55278
        self.USE_UDP_MONITOR = True
        self.dict = {}
        
        self.is_normalized = True
        self.service_rate = 0.05  # this must match frame rate value used in platform_controller.py
        self.levels = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.gains = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0])  # xyzrpy gains
        self.master_gain = 1.0
        #  washout_time is number of seconds to decay below 2%
        self.washout_time = [12, 12, 12, 12, 12, 12]
        self.washout_factor = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        for idx, t in enumerate(self.washout_time):
            self.set_washout(idx, self.washout_time[idx])
        self.ma_samples  = [1, 1, 1, 1, 1, 1]
        self.prev_washed = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # previous washout values
        self.prev_value = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # previous request

        self.inQ = Queue()
        t = threading.Thread(target=self.listener_thread, args=(self.inQ, self.HOST, self.PORT))
        t.daemon = True
        t.start()
        
        self.start_time = time.time()  # todo move this to start of demo

    def init_gui(self, root):
        self.master = master
        frame = tk.Frame(master)
        frame.pack()
        self.label0 = tk.Label(frame, text="Accepting UDP messages on port " + str(self.PORT))
        self.label0.pack(fill=tk.X, pady=10)

        self.units_label = tk.Label(frame, text="Units")
        self.units_label.pack(side="top", pady=10)
        self.display_units()

        self.msg_label = tk.Label(frame, text="")
        self.msg_label.pack(side="top", pady=10)

        self.cmd_label = tk.Label(frame, text="")
        self.cmd_label.pack(side="top", pady=10)

    def chair_status_changed(self, chair_status):
        print(chair_status[0])

    def intensity_status_changed(self, status):
        pass

    def begin(self, cmd_func, move_func, limits):
        self.cmd_func = cmd_func
        self.move_func = move_func
        self.limits = limits    # note limits are in mm and radians
        print "Waiting for UDP message on port", self.PORT

    def fin(self):
        # client exit code goes here
        pass

    def get_current_pos(self):
        return self.levels

    def set_washout(self, idx, value):
        #  expects washout duration (time to decay below 2%)
        #  zero disables washout
        self.washout_time[idx] = value
        if value == 0:
            self.washout_factor[idx] = 0
        else:
            self.washout_factor[idx] = 1.0 - self.service_rate / value * 4
            #  print "in shape", idx, " washout time set to ", value, "decay factor=", self.washout_factor[idx]

    def get_washouts(self):
        #  print "in shape", self.washout_time
        return self.washout_time

    def log(self, data):
        return
        t = time.time() - self.start_time
        xyzrpy = ",".join('%0.2f' % item for item in data)
        """"
        if self.coaster.flip and self.coaster.flip != 0:
            log_entry = format("%.2f,%s,%d\n" % (t, xyzrpy, self.coaster.flip))
        else:
            log_entry = format("%.2f,%s\n" % (t, xyzrpy))
        """
        log_entry = format("%.2f,%s,%s\n" % (t, xyzrpy,self.coaster.quat))
        logger.write(log_entry)

    def service(self):
        r = [0.0] * 6
        print("in Service, que len = ",self.inQ.qsize())
        t = {}
        
        while not self.inQ.empty():
            msg = self.inQ.get()
            lines = msg.split('\n')
            for kv in lines:
               pairs = kv.split('=')
               if len(pairs) == 2:
                  self.dict[pairs[0]] = pairs[1]
            quaternionx = self.dict['quaternionx']
            quaterniony = self.dict['quaterniony']
            quaternionz = self.dict['quaternionz']
            quaternionw = self.dict['quaternionw']
            rollrate = self.dict['rollrate']
            pitchrate = self.dict['pitchrate']
            yawrate = self.dict['yawrate']
            ax= self.dict['ax']
            ay= self.dict['ay']
            az= self.dict['az']
            print(ax,ay,az, rollrate, pitchrate, yawrate)
            
        # self.process_xyzrpy(r)

    def process_xyzrpy(self, xyzrpy):
        try:
            #print "ready to process", xyzrpy
            r = np.multiply(xyzrpy, self.gains) * self.master_gain 

            for idx, f in enumerate(self.washout_factor):
                #  if washout enabled and request is less than prev washed value, decay more
                if f != 0 and abs(xyzrpy[idx]) < abs(self.prev_value[idx]):
                    #  here if washout is enabled
                    r[idx] =  self.prev_value[idx] * self.washout_factor[idx]

            self.prev_value = r

            if self.move_func:
                #print r
                self.move_func(r)
                self.levels = r
        except:
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print "error processing elite telemetry", e,s
            
    def listener_thread(self, inQ, HOST, PORT):
        try:
            self.MAX_MSG_LEN = 1500
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.bind((HOST, PORT))
            print "opening socket on", PORT
            self.inQ = inQ
        except:
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print "thread init err", e, s
        while True:
            try:
                msg, address = client.recvfrom(self.MAX_MSG_LEN)
                #print msg   # .decode('utf-8')
                self.inQ.put(msg)
            except:
                e = sys.exc_info()[0]
                s = traceback.format_exc()
                print "listener err", e, s
                
if __name__ == "__main__":
    client = InputInterface()
    client.begin(None, None, None)   
    while True:
       client.service()
       time.sleep(2)
         
    json_obj = json.loads(test_msg)
    # print json_obj
    print json_obj.get('LinearAcceleration')
    print json_obj['LinearAcceleration'][1]
    print json_obj['AngularAcceleration'][2]