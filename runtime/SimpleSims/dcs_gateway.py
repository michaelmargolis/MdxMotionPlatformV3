#!/usr/bin/env python3

# dcs_gateway.py
# This version listens on a UDP port

import sys
import socket
import time
import csv
from collections import namedtuple
import threading
import traceback
# from queue import Queue 
import logging as log

PORT = 31090        # Port to listen on for DCS hook messages 

# These are the fields sent by DCS hook
DCS_telemetry = namedtuple('DCS_telemetry', \
   ['NMCIAS', 'NMCMachnumber', 'NMCTAS', 'NMCGS', 'NMCAOA', 'NMCVerticalSpeed', \
   'NMCHeight', 'NMCinertial_Bank', 'NMCinertial_Yaw', 'NMCinertial_Pitch', \
   'NMCOmega_x', 'NMCOmega_y', 'NMCOmega_z', 'NMCAccel_x', 'NMCAccel_y', \
   'NMCAccel_z', 'NMCTime', 'NMCCounter'])

# DCS fields used by Motion platform  
# positive values: surge forward, sway left, heave up, roll right side down, pitch nose down, yaw CCW 

#Platform_fields = ['NMCAccel_z', 'NMCAccel_x', 'NMCAccel_y', 'NMCOmega_z', 'NMCOmega_x', 'NMCOmega_y'] # using rotation acceleration 

Platform_fields = ['NMCAccel_x', 'NMCAccel_z', 'NMCVerticalSpeed', 'NMCinertial_Bank', 'NMCinertial_Pitch', 'NMCinertial_Yaw']  # using angles of roll, pitch yaw 

class DCS_gateway:  
    def __init__(self, DCS_port = PORT):
        self.port = DCS_port
        self.lock = threading.Lock()
        self.dcs_message = None # raw msg from hook, read only in main thread
        self.is_connected = False
        self.is_active = False #set true when thread is started
        self.telemetry = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ]  # the most recent DCS fields for the platform stored here
        self.normalize = [1.0, 1.0, -0.001, 1.0, -1.0, 0.1]  # multiplied to each field to adjust direction and max value to +-1
        log.info("DCS gateway started using norm values: " + ','.join(str(n) for n in self.normalize))
    
    # return latest DCS data or None if not connected     
    def read(self):
        if self.dcs_message is None:
            return None
        msg = self.dcs_message # must make copy of self.dcs_message (it's updated in another thread)
        telem = self.parse_dcs(msg) 
        if telem is not None:
            # telem[2]= telem[2]-1 # subtract 1g IF NEEDED
            self.telemetry = telem # store latest values  
        if self.dcs_message:     
            return self.telemetry 
        else:
            return None # notthing has been received from the hook

    # parses DCS message and extracts needed fields
    def parse_dcs(self, msg):
        try:
            fields = msg.split(',')
            if len(fields) < len(DCS_telemetry._fields):
               return None
            dcs_values = [float (x) for x in fields]                       
            dcs = DCS_telemetry._make(dcs_values) # load namedtuple with values 
            
            platform_values = [dcs.NMCAccel_x, dcs.NMCAccel_y, dcs.NMCAccel_z, \
                          dcs.NMCOmega_x,  dcs.NMCOmega_y,  dcs.NMCOmega_z]  
            telem = []
            for idx, field in enumerate(Platform_fields):
                val = getattr(dcs, field) # lookup value in dcs namedtuple
                telem.append(val * self.normalize[idx]) # normalize and append to list
            # print(','.join(str(v) for v in telem)) # show values for debug
            return telem  
        except Exception as e:
            print(e)
            
    def listen(self):
        if not self.is_active:
            msg_buffer_size = 1024
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(1) 
            self.sock.bind(("localhost", self.port))

            log.info("DCS gateway listening on port " + str(self.port))
            self.is_active = True
            t = threading.Thread(target=self.listener_thread, args= (self.sock, self.lock, msg_buffer_size))
            t.daemon = True
            t.start()
        
    def listener_thread(self, sock, lock, buffer_size):
        # received msgs are passed using shared memory so do not modify in main thread

        while self.is_active: 
            try:             
                while self.is_active: 
                    msg = sock.recv(buffer_size).decode('utf-8')
                    if len(msg) > 1:
                        # perform any mods to msg before the next line
                        lock.acquire()
                        self.dcs_message = msg
                        self.is_connected = True  # set connected flag when msg received
                        lock.release()
                        log.debug("hook send msg: %s", msg.strip())
            except socket.timeout:
                if self.is_connected:
                    log.info("Timeout receiving DCS telemetry")
                self.is_connected = False            
            except:
                e = sys.exc_info()[0]
                s = traceback.format_exc()
                print("listener thread err", e, s)

        
# test code showing example usage  
def main():
    try:
        gateway = DCS_gateway(PORT)
        gateway.listen() 
        while(True):
            telemetry = gateway.read()
            if telemetry:
                print(telemetry)
            time.sleep(.05)
    except KeyboardInterrupt:
        gateway.is_active = False # signal the thread to terminate
        print("exiting")
    except exception as e:
        print(e)
        
    
if __name__ == "__main__":
    main()
    