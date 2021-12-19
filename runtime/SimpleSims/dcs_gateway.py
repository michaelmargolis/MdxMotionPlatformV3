#!/usr/bin/env python3

# dcs_gateway.py

import sys
import socket
import time
import csv
from collections import namedtuple
import threading
import traceback
from queue import Queue

PORT = 31090        # Port to listen on for DCS hook messages 

# These are the fields sent by DCS hook
DCS_telemetry = namedtuple('DCS_telemetry', \
   ['NMCIAS', 'NMCMachnumber', 'NMCTAS', 'NMCGS', 'NMCAOA', 'NMCVerticalSpeed', \
   'NMCHeight', 'NMCinertial_Bank', 'NMCinertial_Yaw', 'NMCinertial_Pitch', \
   'NMCOmega_x', 'NMCOmega_y', 'NMCOmega_z', 'NMCAccel_x', 'NMCAccel_y', \
   'NMCAccel_z', 'NMCTime', 'NMCCounter'])

# DCS fields used by Motion platform  
# positive values: surge forward, sway left, heave up, roll right side down, pitch nose down, yaw CCW 
Platform_fields = ['NMCAccel_x', 'NMCAccel_z', 'NMCAccel_y', 'NMCOmega_y', 'NMCOmega_z', 'NMCOmega_x',]

class DCS_gateway:  
    def __init__(self, DCS_port = PORT):
        self.port = DCS_port
        self.dcs_hook_Q = None
        self.is_hook_connected = False
        self.telemetry = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ]  # the most recent DCS fields for the platform stored here
        self.normalize = [1.0, -1.0, 1.0, 1.0, 1.0, 1.0 ]  # multiplied to each field to adjust direction and max value to +-1
    
    # return latest DCS data or None if not connected     
    def read(self):
        if not self.dcs_hook_Q:
            print("Error: you must call the listen method at startup prior to calls to read")
            quit()
        msg = None
        while self.dcs_hook_Q.qsize() > 1:
            ignored = self.dcs_hook_Q.get()
            # print("ignored", ignored)       
        if self.dcs_hook_Q.qsize() > 0:
            msg = self.dcs_hook_Q.get()
            # print("debg in read", msg)
            telem = self.parse_dcs(msg)
            if telem is not None:
                self.telemetry = telem # store latest values  
        if self.is_hook_connected:     
            return self.telemetry 
        else:
            return None # not connected

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
        self.dcs_msg_buffer_size = 1024
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.sock.settimeout(1)
        self.sock.bind(('127.0.0.1', self.port))
        print("listening on port ", self.port)
        self.sock.listen()
        self.dcs_hook_Q = Queue()
        self.is_active = True
        t = threading.Thread(target=self.listener_thread, args= (self.sock, self.dcs_hook_Q))
        t.daemon = True
        t.start()
        
    def listener_thread(self, sock, que):
        # received msgs are put into to que
        line_reader = LineReader(sock)
        while self.is_active: 
            try:
                print("ready to accept")
                line_reader.accept()  
                self.is_hook_connected = True                
                while self.is_active and self.is_hook_connected: 
                    data = line_reader.get_line()
                    if data is None:
                       self.is_hook_connected = False
                       print("DCS hook disconnected")
                    else:
                        if len(data) > 0:
                            que.put(data)
            except socket.timeout:
                pass
            except:
                e = sys.exc_info()[0]
                s = traceback.format_exc()
                print("listener thread err", e, s)

# LineReader class extracts a newline terminated message from the TCP stream 
class LineReader:
    def __init__(self,sock):
        self.sock = sock
        self.buffer = b''
    
    def accept(self):
        self.conn, addr = self.sock.accept()

    def get_line(self):
        while b'\n' not in self.buffer:
            data = self.conn.recv(1024)   
            data.replace(b'\n\n', b'\n') # remove extranios newlines
            if data == b'':
                return None # socket closed
            self.buffer += data
        line,sep,self.buffer = self.buffer.partition(b'\n')
        return line.decode()
        
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
    