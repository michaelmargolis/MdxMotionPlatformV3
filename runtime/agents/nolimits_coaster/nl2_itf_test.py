"""
NL2 interface test

This version requires NoLimits attraction license and NL ver 2.5.3.5 or later

"""

import socket
from time import time,sleep
from struct import *
import collections
from my_quaternion import Quaternion
from math import pi, degrees, sqrt
import sys
import ctypes #  for bit fields
import os
import  binascii  # only for debug
import traceback


# bit fields for station message
bit_e_stop = 0x1
bit_manual = 0x2
bit_can_dispatch = 0x4
bit_gates_can_close = 0x8
bit_gates_can_open = 0x10
bit_harness_can_close = 0x20
bit_harness_can_open = 0x40
bit_platform_can_raise = 0x80
bit_platform_can_lower = 0x100
bit_flyercar_can_lock =  0x200
bit_flyercar_can_unlock = 0x400
bit_train_in_station = 0x800
bit_current_train_in_station = 0x1000

class CoasterInterface():

    N_MSG_OK = 1
    N_MSG_ERROR = 2
    N_MSG_GET_VERSION = 3 # datasize 0
    N_MSG_VERSION = 4
    N_MSG_GET_TELEMETRY = 5  # datasize 0
    N_MSG_TELEMETRY = 6
    N_MSG_GET_STATION_STATE = 14 #size=8 (int32=coaster index, int32=station index)
    N_MSG_STATION_STATE = 15 #DataSize = 4 
    N_MSG_SET_MANUAL_MODE = 16 # datasize 9
    N_MSG_DISPATCH = 17  # datasize 8
    N_MSG_SET_PLATFORM = 20  # datasize 9
    N_MSG_LOAD_PARK = 24   # datasize 1 + string 
    N_MSG_CLOSE_PARK = 25  # datasize 0
    N_MSG_SET_PAUSE = 27   # datasize 1
    N_MSG_RESET_PARK = 28  # datasize 1
    N_MSG_SELECT_SEAT = 29 # datasize = 16 
    N_MSG_SET_ATTRACTION_MODE = 30   # datasize 1
    N_MSG_RECENTER_VR = 31 # datasize 0
    
    c_nExtraSizeOffset = 9  # Start of extra size data within message

    telemetryMsg = collections.namedtuple('telemetryMsg', 'state, frame, viewMode, coasterIndex,\
                                           coasterStyle, train, car, seat, speed, posX, posY,\
                                           posZ, quatX, quatY, quatZ, quatW, gForceX, gForceY, gForceZ')

    def __init__(self):
        self.telemetry_err_str = "Waiting to connect to NoLimits Coaster"
        self.telemetry_status_ok = False
        self.telemetry_data = None
        self._telemetry_state_flags = 0
        self.prev_yaw = None
        self.prev_time = time()
        self.lift_height = 32  # max height in meters
        self.pause_mode = False  # for toggle todo replace with explicit pause state
        # self.is_play_mode = False # set to true if NL2 telemetry is in play mode
        self.station_status = 0
        self.coaster_status = 0
        self.nl2_version = None
        self.start_time = time()
        
        self.nl2_msg_buffer_size = 255
        self.nl2_msg_port = 15151
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(0.05) # telemetry requests sent after each timeout

    def connect_to_coaster(self, coaster_ip_addr):
        try:
            print("attempting connect to NoLimits @",coaster_ip_addr, self.nl2_msg_port)
            self.sock.connect((coaster_ip_addr, self.nl2_msg_port))
            print("connected to NoLimits")
            return True
        except Exception as e:
            print("error connecting to NoLimits", e)
            return False

        #print "telemetry flags = ", self._telemetry_state_flags 
        return True # self.check_coaster_status(ConnectStatus.is_in_play_mode)

    def _create_simple_message(self, msgId, requestId):  # message with no data
        result = pack(b'>cHIHc', b'N', msgId, requestId, 0, b'L')
        return result

    def _create_NL2_message(self, msgId, requestId, msg):  # message is packed
        #  fields are: N Message Id, reqest Id, data size, L
        start = pack(b'>cHIH', b'N', msgId, requestId, len(msg))
        end = pack(b'>c', b'L')
        result = start + msg + end
        return result

    def get_msg_id(self):
        id = int((time() - self.start_time) * 1000);
        # print "msg id=", id
        return id

    def send(self, r):
        #  msg, requestId, size = (unpack('>HIH', r[1:9]))
        #  print "sending:", msg, requestId
        # above just for debug
        try:
            self.sock.sendall(r)
        except:
            e = sys.exc_info()[0]  # report error
            # print e
        sleep(.001)

    def get_nl2_version(self):
        self.nl2_version = None
        self.send(self._create_simple_message(self.N_MSG_GET_VERSION, self.get_msg_id()))
        sleep(0.1)
        #self.service()
        #return self.nl2_version

    def get_telemetry(self):
        # returns most recent message, request sent will be handled on the next call 
        self.send(self._create_simple_message(self.N_MSG_GET_TELEMETRY,self.get_msg_id()))
        #self.service()
        #return self.telemetry_data

    def _process_nl2_msgs(self, msg, requestId, data, size):
        try:
            #  print "telemetry msg: ", msg, requestId, size
            if msg == self.N_MSG_VERSION:
                #  print "raw data:", ":".join("{:02x}".format(ord(c)) for c in data)
                v0, v1, v2, v3 = unpack('cccc', data[self.c_nExtraSizeOffset:self.c_nExtraSizeOffset+4])
                self.nl2_version = format("%c.%c.%c.%c" % (chr(ord(v0)+48),chr(ord(v1)+48),chr(ord(v2)+48), chr(ord(v3)+48)))
                #self.nl2_version = nl2_version
                print('NL2 version', self.nl2_version)
                
            elif msg == self.N_MSG_STATION_STATE:
                s = unpack('>I', data[self.c_nExtraSizeOffset:self.c_nExtraSizeOffset+4])
                #  print format( "in telemetry, got station state msg %x" % (s[0]))
                self.station_status = s[0]
            elif msg == self.N_MSG_TELEMETRY:
                #  print "raw data:", ":".join("{:02x}".format(ord(c)) for c in data)
                if size == 76:
                    t = (unpack('>IIIIIIIIfffffffffff', data[self.c_nExtraSizeOffset:self.c_nExtraSizeOffset+76]))
                    tm = self.telemetryMsg._make(t)
                    # print "tm", tm
                    self.telemetry_data = self._process_telemetry_msg(tm)
                    self.telemetry_status_ok = True
                    #self.is_play_mode = True
                    #self.set_coaster_status(ConnectStatus.is_nl2_connected, True)
                    #  print "telemetry ", self.telemetry_status_ok 
                else:
                    print('invalid msg len expected 76, got ', size)
                #sleep(self.interval)
                #self.send(self._create_simple_message(self.N_MSG_GET_TELEMETRY, self.N_MSG_GET_TELEMETRY))
            elif msg == self.N_MSG_OK:
                self.telemetry_status_ok = True
                print("telemetry status ok")
                pass
            elif msg == self.N_MSG_ERROR:
                self.telemetry_status_ok = False
                self.telemetry_err_str = data[self.c_nExtraSizeOffset: self.c_nExtraSizeOffset+size]
                print("telemetry err:", self.telemetry_err_str)
            else:
                print('unhandled message', msg, requestId, size, data)
        except socket.error:
            print("Connection to NoLimits broken")
        except:
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print("process msg error", e, s)


    def _process_telemetry_msg(self, msg):
        """
        returns four fields:
            boolean indicating if NL2 is in play mode
            boolean indicating if coaster is running (not paused)
            float  coaster speed in meters per seconds
            list of the six xyzrpy values
        """
        self._telemetry_state_flags = msg.state
        is_play_mode = (msg.state & 1) != 0
        if is_play_mode:  # only process if coaster is in play
            #  code here is non-normalized (real) translation and rotation messages
            quat = Quaternion(msg.quatX, msg.quatY, msg.quatZ, msg.quatW)
            pitch = degrees(quat.toPitchFromYUp())
            yaw = degrees(quat.toYawFromYUp())
            roll = degrees(quat.toRollFromYUp())
            print(format("telemetry (speed, frame, rpy): %.2f, %d, %.2f, %.2f, %.2f" % (msg.speed, msg.frame, roll, pitch, yaw)))
        else:
            print("in telemetry, Coaster not in play mode")
        return [False, False, 0, None]


server_address = '127.0.0.1'

if __name__ == "__main__":
    nl2 = CoasterInterface()
    print("\nserver address:", server_address)
    while nl2.connect_to_coaster(server_address) == False:
        sleep(1)
    nl2.get_nl2_version()
    while True:
        try:
            msg = data = None
            data = nl2.sock.recv(nl2.nl2_msg_buffer_size)
            if data and len(data) > 8:
                msg, requestId, size = (unpack('>HIH', data[1:9]))
                print("msg:", msg, size, requestId) 
                nl2._process_nl2_msgs(msg, requestId, data, size)
  
        except socket.timeout:
            nl2.send(nl2._create_simple_message(nl2.N_MSG_GET_TELEMETRY, nl2.get_msg_id()))
            print("timeout in listener")
        except:
            if msg:
                print("bad msg:",msg, "len=", len(msg))
            if data: 
                print("bad data",data,"len=", len(data))
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print("listener thread err", e, s)

        if input('\nType quit to stop this script ') == 'quit':
            break
        nl2.get_telemetry()

