""" 
Judder.py

Code to shake platform in 6 DoF for acceleration tests
"""

import sys, os
import time

import logging as log
import logging.handlers
import argparse
import operator  # for map sub
import importlib
import socket
import traceback
import math # for conversion of radians to degrees
import serial

RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(RUNTIME_DIR))

from kinematics.dynamics import Dynamics
from kinematics.kinematicsV2 import Kinematics
from kinematics.cfg_SlidingActuators import *
from  system_config import  cfg
import output.d_to_p as d_to_p
from output.muscle_output import MuscleOutput

DATA_PERIOD = 50  # ms between samples

ECHO_UDP_IP = "127.0.0.1"
ECHO_UDP_PORT = 10020
echo_address = (ECHO_UDP_IP, ECHO_UDP_PORT )

slider_config_module = "cfg_SlidingActuators"
chair_config_module = "cfg_SuspendedChair"

accel_mode = {'Calibrate':'C', 'Real':'R', 'World':'W'} 

class state():
    def __init__(self, values):
        self.values = values
        self.value_idx = 0
        
    def val(self):
        return self.values[self.value_idx]
    
    def next(self):
        # return next value or none if no more values
        if self.value_idx >= len(self.values)-1:
            self.value_idx = 0
            return 0, True  # state has overflowed back to first state
        else:
            self.value_idx +=1
            return self.values[self.value_idx], False

class Judder():
    def __init__(self,festo_ip='192.168.0.10'):
        self.echo_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.festo_ip = festo_ip
        self.load_config('kinematics.cfg_SlidingActuators')
        self.rotate_orientation = False
        self.time_interval = DATA_PERIOD / 1000.0 
        self.configure_state_machine()
        self.readings = [] # csv data


    def configure_state_machine(self):
        self.axis_names = ['X', 'Y', 'Z', 'Roll', 'Pitch', 'Yaw']
        self.axis = state([0,1,2,3,4,5])
        self.pulse_interval = state([.25,0.5,0.75,1,1.25])
        self.move_intensity = 1
        self.pulse_state = state([self.move_intensity, -self.move_intensity,0])     
        self.pulse_started_flag = False # flag used to create plot spike at start of each pulse
        self.next_transition_time = None # set to the monotonic time to begin next transition
                
    def get_data(self):
        # list of adxl readings will be returned if received, else None
        if self.ser.in_waiting > 24:
            data = self.ser.read_until().decode().rstrip()
            vals = data.split(',')
            self.readings.append(data[1:]) # remove header
            vals.append(self.show_pulse_start())
            return vals[1:] 
        return None

    def show_pulse_start(self):
        # add data indicating state (only needed for testing)
        if self.pulse_state.value_idx == 0:
            if  not self.pulse_started_flag:
                self.pulse_started_flag = True
                return 2
            else:
                return -2
        else:        
            self.pulse_started_flag = False # ready for next pulse start
            return -2
     
    def service_state(self):   
        if self.next_transition_time == None:
            # here if starting
            return self.process_new_state()
            
        elif self.next_transition_time <= time.monotonic():
            pulse_state, overflow = self.pulse_state.next()            
            if overflow:
                 pulse_interval, overflow = self.pulse_interval.next()
                 if overflow:
                    axis, overflow = self.axis.next()
                    if overflow:                    
                        return 'COMPLETED'
            return self.process_new_state()
        return None  # state still in progress

    def process_new_state(self):
        transform = [0]*6
        axis = self.axis.val()
        transform[axis] = self.pulse_state.val()
        self.move(transform)
        self.next_transition_time = time.monotonic() + self.pulse_interval.val()
        pulse = self.pulse_state.val()
        if pulse >= 0:
            pulse = " " + str(pulse)
        else:
             pilse = str( self.pulse_state.val())
        return "Axis {}, pulse {}, t {} sec".format(self.axis_names[axis],  pulse, self.pulse_interval.val())
        
    def configure_kinematics(self):
        # load_config() must be called before this method 
        self.k = Kinematics()
        self.cfg.calculate_coords()

        self.k.set_geometry(self.cfg.BASE_POS, self.cfg.PLATFORM_POS)
        if self.cfg.PLATFORM_TYPE == "SLIDER":
            self.k.set_slider_params(self.cfg.joint_min_offset, self.cfg.joint_max_offset, self.cfg.strut_length, self.cfg.slider_angles)
            self.is_slider = True
        else:
            self.k.set_platform_params(self.cfg.MIN_ACTUATOR_LEN, self.cfg.MAX_ACTUATOR_LEN, self.cfg.FIXED_LEN)
            self.is_slider = False
            
        self.invert_axis = self.cfg.INVERT_AXIS 
        self.swap_roll_pitch = self.cfg.SWAP_ROLL_PITCH
   
        self.DtoP = d_to_p.D_to_P(200) # argument is max distance 
        self.dynam = Dynamics()
        self.dynam.begin(self.cfg.limits_1dof,"shape.cfg")
    
    def connect_coms(self, comport):
        self.comport = comport
        try:
            self.ser = serial.Serial(comport, 57600)
            self.ser.timeout = 2
            if self.ser:  
                """            
                if self.ser.in_waiting > 1:
                    data = self.ser.read_until().decode().rstrip()
                    if(data):
                        self.ser.timeout = .025
                        return True
                """
                return True
            else:
                print("Unable to open port", comport)            
        except serial.SerialException as e:
            print("Unable to connect to", comport)
            print("Fix and then restart program to continue")
        except Exception as e:
            print("exception", e)
            print(traceback.format_exc())        
        return False    
        
    def set_accel_mode(self, mode):
        print("Setting acceleration mode to", mode)
        self.ser.write(accel_mode[mode].encode())        
    
    def start_capture(self):
        self.readings = []
        self.ser.reset_input_buffer()
  
    def move(self, transform):
        if self.rotate_orientation:        
            transform = [inv * axis for inv, axis in zip(self.invert_axis, transform)]
            if self.swap_roll_pitch:
                # swap roll, pitch and x,y
                transform[0],transform[1], transform[3],transform[4] =  transform[1],transform[0],transform[4], transform[3]

        request = self.dynam.regulate(transform) # convert normalized to real values
        percents = self.k.actuator_percents(request)
        
        self.muscle_output.move_percent(percents)
        ##distances = self.k.actuator_lengths(request)
        ##self.echo( request.tolist(), distances)

    def save_data(self, fname ):
        try:
            outfile = open(fname,"w")
            for data in self.readings:
                outfile.write(data + "\n")
            outfile.close()
        except Exception as e:
            s = traceback.format_exc()
            log.error("Error saving data file, is it already open? %s %s", e, s)
            
    def centre_pos(self):
        transform = [0]*6
        self.move(transform)
        
    def load_pos(self):
        transform = [0]*6
        transform[2] = -1
        self.move(transform)

    def echo(self, transform, distances):
        # print(transform, distances)
        t = [""]*6
        for idx, val in enumerate(transform):
            if idx < 3:
                if idx == 2:
                    val = -val #  TODO invert z ?
                t[idx] = str(round(val))
            else:
                t[idx] = str(round(val*180/math.pi, 1))
        
        # req_msg = "request," + ','.join(str(round(t*180/math.pi, 1)) for t in transform)
        req_msg = "request," + ','.join(t)
        dist_msg = ",distances," +  ",".join(str(int(d)) for d in distances)
        msg = req_msg + dist_msg + "\n"
        # print(msg)
        self.echo_sock.sendto(bytes(msg, "utf-8"), echo_address)

            
    def load_config(self, cfg_path):
        try:        
            cfg = importlib.import_module(cfg_path)
            self.cfg = cfg.PlatformConfig()
            self.cfg.calculate_coords()
            self.configure_kinematics()
            self.muscle_output = MuscleOutput(self.DtoP.distance_to_pressure, self.festo_ip)
            # load distance to pressure curves from file
            self.DtoP.load( "output\\DtoP.csv") 

        except Exception as e:
            print(str(e) + "\nunable to import cfg from:", cfg_path)
            print(traceback.format_exc())


class Calibrate():
    def __init__(self):
        self.reset()

    def reset(self):
        self.xyz_max = [0.0,0.0,0.0]
        self.xyz_min = [0.0,0.0,0.0]
        
    def update(self, data):
        # data is a list of three floats
        # returns true if new max or min
        if len(data) != 3:
            print("bad data")
            return False
        ret = False
        for idx, val in enumerate(data):
            if val > self.xyz_max[idx]:
                self.xyz_max[idx] = val
                ret = True
            elif val < self.xyz_min[idx]:
                self.xyz_min[idx] = val
                ret = True 
        return ret
        
    def get_min_max(self):
        print("Gain factors:", end=' ')
        offsets = [0, 0, 0]
        for i in range(3):
            extent = (xyz_max[i] -xyz_min[i])/2
            offsets[i]  = 1 - extent
            print("{:.4f}".format(1/extent), end=' ')
        print("\noffsets:", end=' ')
        for i in range(3):
            print("{:.4f}".format(offsets[i]), end=' ')    
        print()
        return ( self.xyz_min,  self.xyz_max)
                    

def start_logging(level):
    log_format = log.Formatter('%(asctime)s,%(levelname)s: %(message)s')
    logger = log.getLogger()
    logger.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler("PlatformCalibration.log", maxBytes=(10240 * 5), backupCount=2)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    console_handler = log.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)


def man():
    parser = argparse.ArgumentParser(description='PlatformCalibration\nA real time testing application')
    parser.add_argument("-l", "--log",
                        dest="logLevel",
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")
    parser.add_argument("-f", "--festo_ip",
                        dest="festoIP",
                        help="Set IP address of Festo controller")  
    
    parser.add_argument("-p", "--port",
                        dest="comport",
                        help="Set coma port for accelerometer data") 

    parser.add_argument("-c", "--calibrate",
                        action='store',
                        nargs='*',
                        dest="calibrate",
                        help="Calibrate accelerometer")                            
    return parser


if __name__ == '__main__':
    # multiprocessing.freeze_support()
    args = man().parse_args()
    if args.logLevel:
        start_logging(args.logLevel)
    else:
        start_logging(log.INFO)

    log.info("Python: %s", sys.version[0:5])
    log.info("Starting Acceleration tester")

    if args.comport:
        comport = args.comport
    else:
        comport = "COM6"

    if args.calibrate is not None:
       calibrate(comport)
       sys.exit
       
    if args.festoIP:
        judder = Judder(args.festoIP)        
    else:
        judder = Judder()
    
    if judder.connect_coms(comport):
        judder.start_capture()
        while True:
            result = judder.service_state()
            if result and result == 'COMPLETED':
                break
            time.sleep(.01)

        fname = input("enter fname for csv: ")
        if fname != "":
            judder.save_data(fname)


       