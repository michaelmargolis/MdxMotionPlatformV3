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
        self.flaps_1_sw = None
        self.flaps_2_sw = None
        self.flaps_sw_released = True
        self.gear_sw = None
        self.brake_sw = None
        self.sim = sim
        self.pot_simvar = []
     

    def open(port, baud):
        super(Panel, self).open_port(port, baud) 
        
    def read(self):
        if super(Panel, self).available():
            msg = super(Panel, self).read()
            if msg:
                # print(msg)
                data = msg.rstrip('\r\n}').split(';')
                if len(data) == 3 and data[0] == 'report':
                    # Data format:   "report;pots",throttle,prop, mix";switches," sw0, sw1, sw2, sw3\n"
                    self.pots = data[1].split(',')[1:]
                    self.process_pots(self.pots)
                    switches = data[2].split(',')[1:]
                    self.process_switches(switches)
                    # print(pots, switches)
                elif data[0] == 'debug':
                    pass
                    # print(data[1])
                else:
                    print("unexpected msg format:", data)
      
    def process_switches(self, switches):
        # print(switches)        
        self.flaps_1_sw = int(switches[0])
        self.flaps_2_sw = int(switches[1])
        if FLAPS_SW_INDEX:  # here if panel sends flaps index
            if self.flaps_1_sw == 1 and self.flaps_2_sw == 1:
                self.set_flaps_index(3) # not used in this version
            elif self.flaps_1_sw == 1:
                self.set_flaps_index(1)
            elif self.flaps_2_sw == 1:
                self.set_flaps_index(2)
            else:
                self.set_flaps_index(0)
        else:
            # here if switches indicate up or down movement
            if self.flaps_1_sw == 1:
                if self.flaps_sw_released == True :
                    self.set_flaps(0)
                    self.flaps_sw_released = False
            elif self.flaps_2_sw == 1:
                if self.flaps_sw_released == True:
                    self.set_flaps(1)
                    self.flaps_sw_released = False
            else:
                self.flaps_sw_released = True
            
        if self.gear_sw != int(switches[2]):
            self.gear_sw = int(switches[2])
            self.set_gear(self.gear_sw)
        # print("self.brake_sw", self.brake_sw, int(switches[3])) 
        if self.brake_sw != int(switches[3]):
            print("self.brake_sw", self.brake_sw) 
            self.brake_sw = int(switches[3])
            self.set_brake(self.brake_sw)
    
    def process_pots(self, values):    
        # print(values, self.pot_simvar)
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
        print("set brake to:", value )    
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

