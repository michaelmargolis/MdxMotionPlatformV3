"""
gui for speed control of coaster fan

"""

import os
import sys
import Tkinter as tk
import ttk
from time import time
import fan_config as fan_cfg
from fan_interface import *


class FanGui(object):

    def __init__(self, master, interp_update_func, set_speed_threshold):
        self.master = master
        self.interp_update = interp_update_func
        self.set_speed_threshold = set_speed_threshold # callback to inform fan controller
        frame = tk.Frame(self.master)
        frame = tk.Frame(self.master)
        frame.pack()

        # values read from config f
        self.com_port = fan_cfg.com_port
        self.speeds = fan_cfg.speeds
        self.gains = fan_cfg.power  #  gains
        self.master_gain = fan_cfg.master_gain
        self.threshold_speed = fan_cfg.threshold_speed # m/s to start fan
        self.threshold_power = fan_cfg.threshold_power  # min power to start fan
        self.max_power = fan_cfg.max_power # max power of current not exceeding 9A
        self.config_fname = "fan_config.py"
        self.init_config()
        """
        GUI code below for fan speed control
        """

        self.intensity_label = tk.Label(frame, text="Set power percent for speed bands in meters per second").pack(fill=tk.X, pady=5)

        s = tk.Scale(frame, from_=2, to=0, resolution=.2, length=120,
                     command=self.set_threshold_speed, label="Threshold")
        #  print "in init, threshold speed = ",self.threshold_speed 
        s.set(self.threshold_speed)
        s.pack(side=tk.LEFT, padx=(12, 4))
        
        sLabels = ("2.5", "5", "10", "20", "30", "40")
        for i in range(6):
            s = tk.Scale(frame, from_=100, to=0, resolution=1, length=120,
                         command=lambda g, i=i: self.set_gain(i, g), label=sLabels[i])
            #  print "g=",self.gains[i], "<"
            s.set(float(self.gains[i]))
            s.pack(side=tk.LEFT, padx=(6, 4))

        s = tk.Scale(frame, from_=100, to=0, resolution=1, length=120,
                     command=self.set_master_gain, label="Master")
        s.set(self.master_gain)
        #  s.pack(side=tk.LEFT, padx=(12, 4))  master not used

        frame1 = tk.Frame(self.master)
        frame1.pack(fill=tk.X, side=tk.TOP, pady=2)
        self.info_label = tk.Label(frame1, text="Waiting for coaster telemetry")
        self.info_label.pack(fill=tk.X, pady=5)


        frame2 = tk.Frame(self.master)
        frame2.pack(fill=tk.X, side=tk.BOTTOM, pady=12)
        self.update_button = tk.Button(frame2, height=2, width=6, text="Update",
                                       command=self.update_config)
        self.update_button.pack(side=tk.LEFT, padx=(220, 4))
        

        
        self.save_button = tk.Button(frame2, height=2, width=5, text="Save",
                                     command=self.save_config)
        self.save_button.pack(side=tk.LEFT, padx=(100, 4))

    def init_config(self):
        print "configuration settings"
        print "  com port:", self.com_port
        print "  threshold speed:", self.threshold_speed 
        print "  threshold power:", self.threshold_power
        print "  gains:", self.gains
        print "  master:", self.master_gain

    def set_gain(self, idx, value):
        self.gains[idx] = value
        #  print "in shape", idx, " gain set to ", value

    def set_master_gain(self, value):
        self.master_gain = float(value)
        #  print "in shape, master gain set to ", value

    def get_master_gain(self):
        return self.master_gain

    def set_threshold_speed(self, value):
         self.threshold_speed = float(value)
         self.set_speed_threshold(float(value))
        
    def get_threshold_speed(self):
        return self.threshold_speed
         
    def set_intensity(self, value):
        #  expects float between 0 and 1.0
        self.intensity = value

    def get_intensity(self):
        return self.master_gain * self.intensity

    def get_overall_intensity(self):
        return self.master_gain * self.intensity 

    def show_info(self, speed, power):
        self.info_label.config(text=format("Speed= %.1f m/s (%d mph), power = %d percent" % (speed, speed * 2.237, power)))

    def show_info_string(self, string):
        self.info_label.config(text=string)

    def update_config(self):
        self.interp_update(self.speeds, self.gains) # update interpolation table
        print "todo update threshold and master?"


    def save_config(self):
        with open(self.config_fname, "w") as outfile:
            outfile.write('# fan_config\n')
            outfile.write('com_port = "' +  self.com_port +  '"\n')
            outfile.write('# speeds (in meters/sec) above this start the fan\n')
            outfile.write("threshold_speed = " + str(self.threshold_speed) +  "\n")
            outfile.write('# lowest power percent to start the fan\n')
            outfile.write("threshold_power = " + str(self.threshold_power) +  "\n")
            outfile.write('# highest power drawing less than 9 amps\n')
            outfile.write("max_power = " + str(self.max_power) +  "\n")
            outfile.write('# max_coaster_speed = 40  # in meters per second\n')
            outfile.write("speeds = [" + ', '.join(str(g) for g in self.speeds) + "]\n")
            outfile.write("power = [" + ', '.join(str(g) for g in self.gains) + "]\n")
            outfile.write('# master gain not used in this version\n')
            outfile.write("master_gain =" + str(self.get_master_gain()) + "\n")

def service():
    telemetry_data = coaster.get_telemetry(.2)  # argument is timeout value
    coaster.service()
    print(coaster.system_status)

    # print telemetry_data
    if telemetry_data and len(telemetry_data) == 2:
        if coaster.system_status.is_in_play_mode:
            speed = telemetry_data[0]
            #  print("coaster speed is ", speed, "m/s")
            if coaster.system_status.is_paused == False:
                power = fan.set_fan_speed(speed)
            else:
                power = fan.set_fan_speed(0)  # coaster is paused
            gui.show_info(speed, power)
        else:
            print("Coaster not in play mode")
            power = fan.set_fan_speed(0)
            gui.show_info_string("Coaster not in play mode")

        """ 
        if telemetry_data[1] and len(telemetry_data[1]) == 6:  # check if we have data for all 6 DOF
            #  print(telemetry_data[1])  # show orientation
            pass  
        """
    else:
        if coaster.system_status.is_nl2_connected:
            print("Telemetry error: %s" % coaster.get_telemetry_err_str())
        else:
            print("No connection to NoLimits, is it running?")
            sleep(1)

    master.after(200, service)  # reschedule 

def get_power_limits():
    return (fan_cfg.threshold_power, fan_cfg.max_power)


if __name__ == "__main__":
    master = tk.Tk()
    fan = FanController(get_power_limits)
    gui = FanGui(master, fan.interp.update, fan.set_speed_threshold)
    coaster = CoasterInterface()
    coaster.begin()
    abort = False

    if  fan.connect_serial(fan_cfg.com_port) == False:
        if fan.select_port() == False: # slect_port returns true if comms opened ok
            abort = True
            sys.exit()
          
    print("fan connected")
    while coaster.connect_to_coaster('localhost') == False:   # this assumes nl2 running on this PC
        sleep(5)
    coaster.system_status.is_pc_connected  = True # must be connected if localhost
    service() 
    master.mainloop()
