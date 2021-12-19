# sim class for X-Plane

import os
import socket
import logging as log
import traceback

class Sim():
    def __init__(self, sleep_func, interval_ms = 25):
        # todo Create  link
        self.sleep_func = sleep_func
        self.interval_ms = interval_ms
        self.sm = None
        self.is_connected = False
        self.norm_factors = [.01, .01, .01, 1, 1, 1]
        self.name = "X-Plane"
        self.ip_addr = 'localhost'
        self.port = 49007
        self.buffer_size = 24

    def __del__(self):
        if self.sm:
            self.sm.exit()
    
    def set_norm_factors(self, norm_factors):
        # values for each element that when multiplied will normalize data to a range of +- 1 
        self.norm_factors = norm_factors
    
    def load(self):
        print("todo load xplane")
   
    def connect(self):
        # returns string code or None if no error
        try:
            # create socket
            # message formatted in following way [float_as_4byte, float_as_4byte, float_as_4byte, float_as_4byte, float_as_4byte, float_as_4byte]
            self.xplane = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # aggregator uses UDP messages
            self.xplane.bind((self.ip_addr, self.port)) # bind to the aggregator port
            log.info("X-Plane UDP bound at %s on port %d", self.ip_addr, self.port)
            return None
        except Exception as e:
            print(e)
            print("todo start xplane here")  
            return(e)
            # os.startfile("M:/MSFS SDK/Tools/bin/fsdevmodelauncher.exe")

    def is_connected(self):
        # todo
        return True            

    def run(self):
        print("todo prep for run")  
        self.is_connected = True
        
    def read(self):
        try:
            data = self.xplane.recv(self.buffer_size)
            (theta,) = unpack('f', data[0:4])
            (phi,) = unpack('f', data[4:8])
            (psi,) = unpack('f', data[8:12])
            (gforce_normal,) = unpack('f', data[12:16])
            (gforce_axil,) = unpack('f', data[16:20])
            (gforce_side,) = unpack('f', data[20:24])
            print("Pitch ", theta, "Roll ", phi, "Yaw ", psi, "G normal ", gforce_normal, "G axil ", gforce_axil, "G side ", gforce_side)
            # return (x, y, z, roll, pitch, yaw)
            return (0,0,0,0,0,0)
        except:
            return (0,0,0,0,0,0)



if __name__ == '__main__':
    sim = Sim()
    if(sim.is_connected):
        sim.set_norm_factors([.01, .01, .01, 1, 1, 1])
        while(1):
            xyzrpy = sim.read()
            csv = ['%.3f' %  elem for elem in xyzrpy]
            print(','.join(csv))   
    quit()