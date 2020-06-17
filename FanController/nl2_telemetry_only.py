"""
NL2 interface module

This version requires NoLimits attraction license and NL ver 2.5.3.5 or later

"""
from __future__ import print_function
import sys
from Queue import Queue
import socket
from time import time,sleep
from struct import *
import collections
# from my_quaternion import Quaternion # uncomment this for rotation info
from math import pi, degrees, sqrt
import threading
from Queue import Queue
import ctypes #  for bit fields
import os

import  binascii  # only for debug
import traceback

class SystemStatus(object):
    def __init__(self): 
        self._is_pc_connected = False
        self._is_nl2_connected = False
        self._is_in_play_mode = False 
        self._is_moving = False
        self._is_paused = False

    @property
    def is_pc_connected(self):
        return self._is_pc_connected
    @is_pc_connected.setter
    def is_pc_connected(self, value):
        self._is_pc_connected = value

    @property
    def is_nl2_connected(self):
        return self._is_nl2_connected
    @is_nl2_connected.setter
    def is_nl2_connected(self, value):
        self._is_nl2_connected = value

    @property
    def is_in_play_mode(self):
        return self._is_in_play_mode
    @is_in_play_mode.setter
    def is_in_play_mode(self, value):
        self._is_in_play_mode = value

    @property
    def is_moving(self):
        return self._is_moving
    @is_moving.setter
    def is_moving(self, value):
        self._is_moving = value

    @property
    def is_paused(self):
        return self._is_paused
    @is_paused.setter
    def is_paused(self, value):
        self._is_paused = value

    def __str__(self):
        if self._is_pc_connected:
            if  self._is_nl2_connected:
                if self._is_in_play_mode:
                    if self._is_paused:
                        return "coaster is paused"
                    if self._is_moving:
                        return "coaster is moving"
                    return "coaster in play mode"
                else:
                     return "noLimits not in play mode"
            else:
                return "noLimits not connected"
        else:    
            return "PC not connected"

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
        self.pause_mode = False  # for toggle todo replace with explicit pause state
        # self.is_play_mode = False # set to true if NL2 telemetry is in play mode
        self.system_status = SystemStatus()
        self.nl2_version = None
        self.start_time = time()
        ##self.latencyMA = MovingAverage(16) # average nl2 messages
        ##self.average_latency = 15 #for nl2 msgs, updated in real time        
        self.nl2_msg_buffer_size = 255
        self.nl2_msg_port = 15151
        self.nl2Q = Queue()

    def begin(self):
        print("nl2 interface begin")
        self.nl2_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nl2_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.nl2_sock.settimeout(0.5) # telemetry requests sent after each timeout

    def start_listening(self):
        t = threading.Thread(target=self.listener_thread, args= (self.nl2_sock,))
        t.daemon = True
        t.start()
        
    def connect_to_coaster(self, coaster_ip_addr):
        # returns true iff connected to NL2    (no longer testing for play mode?)
        if self.system_status.is_nl2_connected == False:
            try:
                print("Attempting connect to NoLimits @",coaster_ip_addr, self.nl2_msg_port)
                self.nl2_sock = socket.create_connection((coaster_ip_addr, self.nl2_msg_port),1) # timeout after one second
                print("nl2 connected")
                self.system_status.is_nl2_connected = True
                self.start_listening() # create listening thread
                sleep(1)
                self.get_nl2_version()
                return True
            except Exception as e:
                self.system_status.is_nl2_connected = False
                # if "Errno 10056" in str(e):
                self.nl2_sock.close()
                self.nl2_version == None
                print("error connecting to NoLimits socket", str(e))
                return False
        else:
            return True

    #  see NL2TelemetryClient.java in NL2 distribution for message format
    def _create_simple_message(self, msgId, requestId):  # message with no data
        result = pack('>cHIHc', 'N', msgId, requestId, 0, 'L')
        return result

    def _create_NL2_message(self, msgId, requestId, msg):  # message is packed
        #  fields are: N Message Id, reqest Id, data size, L
        start = pack('>cHIH', 'N', msgId, requestId, len(msg))
        end = pack('>c', 'L')
        result = start + msg + end
        return result

    def _get_msg_id(self):
        id = int((time() - self.start_time) * 1000);
        # print "msg id=", id
        return id

    def _send(self, r):
        #  msg, requestId, size = (unpack('>HIH', r[1:9]))
        #print("sending:", r)
        # above just for debug
        try:
            self.nl2_sock.sendall(r)
        except:
            e = sys.exc_info()[0]  # report error
            # print e
        sleep(.001)

    def get_nl2_version(self):
        self.nl2_version = None
        self._send(self._create_simple_message(self.N_MSG_GET_VERSION, self._get_msg_id()))
        print("getting version ")
        for i in range(10):
            sleep(.1)            
            self.service()
            if self.nl2_version != None:                            
                return self.nl2_version
        return None  # NL2 did not respone

    def get_telemetry_err_str(self):
        return self.telemetry_err_str

    def get_telemetry_status(self):
        return self.telemetry_err_str

    def get_telemetry(self, timeout):
        self._send(self._create_simple_message(self.N_MSG_GET_TELEMETRY,self._get_msg_id()))
        start = time()
        self.telemetry_data = None
        while time() - start < timeout:
            self.service()
            if self.telemetry_data != None:
                # print("get_telemetry", self.telemetry_data)
                # print "in get_telemetry, latency=", time() - start 
                return self.telemetry_data
        # print("timeout in get_telemetry")
        return None

    def service(self):
        while self.nl2Q.qsize() > 0:
            msg, requestId, data, size = self.nl2Q.get()
            #  print("in service", msg, requestId, size)
            self._process_nl2_msgs(msg, requestId, data, size)

    def _process_nl2_msgs(self, msg, requestId, data, size):
        try:
            # print("telemetry msg: ", msg, requestId, size)
            if msg == self.N_MSG_VERSION:
                v0, v1, v2, v3 = unpack('cccc', data)
                self.nl2_version = format("%c.%c.%c.%c" % (chr(ord(v0)+48),chr(ord(v1)+48),chr(ord(v2)+48), chr(ord(v3)+48)))
                print('NL2 version', self.nl2_version)
                self.system_status.is_nl2_connected = True
            elif msg == self.N_MSG_TELEMETRY:
                if size == 76:
                    t = (unpack('>IIIIIIIIfffffffffff', data))
                    tm = self.telemetryMsg._make(t)
                    # print "tm", tm
                    self.telemetry_data = self._process_telemetry_msg(tm)
                    self.telemetry_status_ok = True
                else:
                    print('invalid msg len expected 76, got ', size)
                #sleep(self.interval)
                #self._send(self._create_simple_message(self.N_MSG_GET_TELEMETRY, self.N_MSG_GET_TELEMETRY))
            elif msg == self.N_MSG_OK:
                self.telemetry_status_ok = True
                self.system_status.is_nl2_connected = True
                pass
            elif msg == self.N_MSG_ERROR:
                self.telemetry_status_ok = False
                self.telemetry_err_str = data
                #print("telemetry err:", self.telemetry_err_str)
                print(format("telemetry err for msg  %d, req id %d: %s\n" % (msg, requestId, self.telemetry_err_str)))

            else:
                print('unhandled message', msg, requestId, size, data)
        except:
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print("Error processing NoLimits message",e,s)
            #self.self.system_status.is_nl2_connected = False

    def _process_telemetry_msg(self, msg):
        """
        returns two fields:
            float  coaster speed in meters per seconds
            list of the six xyzrpy values
        """
        telemetry_data = None 
        self._telemetry_state_flags = msg.state
        is_play_mode = (msg.state & 1) != 0
        if self.system_status.is_in_play_mode == False:
           #  print "in process msg, play state changed to", is_play_mode
           self.system_status.is_in_play_mode = is_play_mode
        if is_play_mode:  # only process if coaster is in play
            """ uncomment this block to get the rotation and translation values
            #print "quat", msg.quatX, msg.quatY, msg.quatZ, msg.quatW,
            quat = Quaternion(msg.quatX, msg.quatY, msg.quatZ, msg.quatW) 
            self.quat = quat
            roll = quat.toRollFromYUp() / pi
            pitch = -quat.toPitchFromYUp() * 0.6 # reduce intensity of pitch
            yaw = -quat.toYawFromYUp()

            #  y from coaster is vertical
            #  z forward
            #  x side

            heave = msg.posY   # note this ignores lift height 
            #print "heave", heave
            
            #surge = max(min(1.0, msg.gForceZ), -1)
            #sway = max(min(1.0, msg.gForceX), -1)
            
            if  msg.gForceZ >=0:
                surge = sqrt( msg.gForceZ)
            elif msg.gForceZ < 0:
                surge = -sqrt(-msg.gForceZ)

            if  msg.gForceX >=0:
                sway = sqrt( msg.gForceX)
            elif msg.gForceX < 0:
                sway = -sqrt(-msg.gForceX)

            data = [surge, sway, heave, roll, pitch, yaw]
            intensity_factor = 0.4  # larger values are more intense
            
            #print "telemetry_data", telemetry_data
            #telemetry_data = ['%.3f' % (elem * intensity_factor)  for elem in data]
            telemetry_data = [(elem * intensity_factor)  for elem in data]
            #if speed != 0:
            #    print ['%.3f' % (elem * intensity_factor)  for elem in data]
            """
            self.system_status.is_paused = msg.state == 7  # 3 is running, 7 is paused
            speed = float(msg.speed)
            self.system_status.is_moving = speed > 0.5
            #print "is moving=", self.system_status.is_moving, speed
            return (speed, telemetry_data)


            #print "pitch=", degrees( quat.toPitchFromYUp()),quat.toPitchFromYUp(), "roll=" ,degrees(quat.toRollFromYUp()),quat.toRollFromYUp()
        #  print "in telemetry, Coaster not in play mode"
        self.system_status.is_in_play_mode = False
        return [0, None]

    def listener_thread(self, sock):
        """ received msgs added to queue, telemetry requests sent on socket timeout """
        print ("starting listener thread")
        header = bytearray(9)
        while True: # self.system_status.is_nl2_connected:
            try:
                if self.system_status.is_nl2_connected:
                    header[0] = sock.recv(1)
                    if header[0] != 0x4e:
                        print("sock header error:",  header[0], hex(header[0]))
                        continue
                    for i in range(8):
                        header[i+1] = sock.recv(1)
                    msg, requestId, size = (unpack('>HIH', header[1:9]))
                    data = sock.recv(size)
                    if sock.recv(1) != 'L':
                        print("Invalid message received")
                        continue
                    #  print("got valid msg, len=", len(data), ":".join("{:02x}".format(ord(c)) for c in data))
                    self.nl2Q.put((msg, requestId, data, size))
                         # todo - perhaps check time of most recent incoming telemetry msg and issue fresh request if greater than timeout time
            except socket.timeout:
                self._send(self._create_simple_message(self.N_MSG_GET_TELEMETRY, self._get_msg_id()))
                print("timeout in listener\n")
                pass
            except ValueError:
                print("got zero form socket, assume its disconnected")
                self.system_status.is_nl2_connected = False
                sleep(1)
            except Exception as e: 
                #e = sys.exc_info()[0]
                """
                if "Errno 10053" in str(e):
                    print("NoLimits closed connection - todo tell GUI")
                    # sock.close()
                    self.system_status.is_nl2_connected = False
                    sleep(1)
                """
                s = traceback.format_exc()
                print("listener thread err", str(e), s)
        print("exiting listener thread")

if __name__ == "__main__":
    coaster = CoasterInterface()
    coaster_thread = threading.Thread(target=coaster.get_telemetry(0.5))
    coaster_thread.daemon = True
    coaster_thread.start()
    while coaster.connect_to_coaster('localhost') == False:  # this assumes nl2 running on this PC
        pass


    while True:
        coaster.service()
        input_field = coaster.get_telemetry(.2)  # argument is timeout value
        if input_field and len(input_field) == 2:
            if coaster.system_status.is_in_play_mode:
                speed = input_field[0]
                print("coaster speed is ", speed, "m/s")
                if coaster.system_status.is_paused == False:
                    print("set fan speed here")
                else:
                    print("Paused, turn fan off here")
            else:
                print("Coaster not in play mode")
                print("turn fan off here")
            """ 
            if input_field[1] and len(input_field[1]) == 6:  # check if we have data for all 6 DOF
                #  print(input_field[1])  # show orientation
                pass  
            """
        else:
            if coaster.system_status.is_nl2_connected:
                print("Telemetry error: %s" % self.coaster.get_telemetry_err_str())
            else:
                print("No connection to NoLimits, is it running?")
        sleep(0.2)

