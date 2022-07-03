""" fs_panel.py

This script is an interface to hardware providing analog and digital inputs
to a flight simulator. 

Serial connectivity is provided by a script named SerialProcess.py

"""
import os, sys
import time
import logging as log
import logging.handlers
import argparse
import math
import json
import traceback

RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(RUNTIME_DIR))
from common.serialProcess import SerialProcess

FLAPS_SW_INDEX = True # set True if panel sends flaps index value (not up/down)

def scale( val, src, dst) :   # the Arduino 'map' function written in python  
  return round((val - src[0]) * (dst[1] - dst[0]) / (src[1] - src[0])  + dst[0])
  
class Panel(SerialProcess):
# arduno interface to hardware panel

    def __init__(self, sim):
        super(Panel, self).__init__()
        self.flaps_index = None
        self.flaps_sw_released = True
        self.gear_sw = None
        self.brake_sw = None
        self.sim = sim
        self.pot_simvar = []
        self.auto_brake_enabled = True
     

    def open(port, baud):
        super(Panel, self).open_port(port, baud) 
        
    def read(self):
        if super(Panel, self).available():
            msg = super(Panel, self).read()
            if msg:
                #  print(msg)
                data = msg.rstrip('\r\n').split(';')
                if len(data) == 2 and data[0] == 'report':
                    # Data format:   'report;"pots"[throttle,prop, mix],"flaps":(index 0-3),"gear":(0 up or 1 down), "brake",(0,1)\n'
                    # print(data[1])
                    d = json.loads(data[1])
                    self.process_pots(d['pots'])
                    self.process_flaps(d['flaps'])
                    self.process_gear(d['gear'])
                    self.process_brake(d['brake'])
                    # print(pots, switches)
                elif data[0] == 'debug':
                    pass
                    # print(data[1])
                else:
                    print("unexpected msg format:", data)
      
    def process_flaps(self, value):
        self.flaps = value
        self.set_flaps_index(value)

    def process_gear(self, value):        
        if self.gear_sw != value:
            self.gear_sw = value
            self.set_gear(self.gear_sw)
            
    def process_brake(self, value):
        if self.brake_sw != value:
            print("self.brake_sw", self.brake_sw) 
            self.brake_sw = value
            self.set_brake(self.brake_sw)
    
    def process_pots(self, values):    
        # print(values, self.pot_simvar)
        self.pots = values
        if len(values) == len(self.pot_simvar):
            for idx, simvar in enumerate(self.pot_simvar):
                if simvar != 'Not Used':
                    if simvar == 'Throttle' or simvar == 'Propeller' or simvar == 'Mixture':
                        to_range = (0, 100)
                    else:
                        print("todo set pot range for ", simvar)
                    value = scale(int(values[idx]), (0,255), to_range)
                    # print("pot {} = {} for {}".format(idx, value, pot_map_vars[simvar]))
                    # fixme pot_map not used !!!
                    self.sim.set_simvar_axis(simvar, value)                   
          

    def set_brake(self, value):
        print("set brake to:", "on" if value else "off" )    
        if self.sim.is_connected:
            # 0 brake off, 1 is on     
            self.sim.set_parking_brake(value)
        
    def set_gear(self, value):
        print("set gear to:", value)
        if self.sim.is_connected:
            self.sim.set_gear(value)

    def set_flaps(self, value):
        print("set flaps to:", value)
        if self.sim.is_connected:
            self.sim.set_flaps(value)
    
    def set_flaps_index(self, value):
        # print("set flaps index to:", value)
        self.flaps_index = value
        if self.sim.is_connected:
            self.sim.set_flaps_index(value)  
            
    def gear_state(self, value):
        # returns 0 if gear up, 2 if down, 1 is moving
        if value == None:
            return
        elif value == 0:
            return 0
        elif value < 1.0:
            return 1
        else:
            return 2

    def set_gear_indicator(self, values):
        msg = "g,{},{},{}\n".format(self.gear_state(values[0]), self.gear_state(values[1]), self.gear_state(values[2]))
        self.send_to_panel(msg)
        
    def set_brake_indicator(self, value):
       msg = "b,{}n".format(value)
       self.send_to_panel(msg)
       
    def set_flaps_indicator(self, percent, max_angle):
        msg = "f,{},{}\n".format( percent, max_angle)
        self.send_to_panel(msg)
 
    def send_to_panel(self, msg):
        if self.is_started :
            self.write(msg.encode())


DATA_PERIOD =  20
BAUD = 115200
GEAR_TEXT = ('Gear Up', 'Gear Down')

