"""
NL2 simple interface module

this version only supports run, pause and simple telemetry

"""
import sys
from queue import Queue
import socket
import time
from struct import *
import collections
from math import pi, degrees, sqrt
import sys
import threading
import ctypes #  for bit fields
import os
import  binascii  # only for debug
import traceback
import logging
log = logging.getLogger(__name__)


# Helper class to decode rotation quaternion into pitch/yaw/roll
from numpy import sin, cos, arctan2, sqrt, pi  # import from numpy
import numpy as np


class Quaternion (object):
    def __init__(self, x, y, z, w):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def __repr__(self):
        return format("%.5f,%.5f,%.5f,%.5f" % (self.x, self.y, self.z, self.w))

    def toPitchFromYUp(self):
        vx = 2 * (self.x * self.y + self.w * self.y)
        vy = 2 * (self.w * self.x - self.y * self.z)
        vz = 1.0 - 2 * (self.x * self.x + self.y * self.y)
        return arctan2(vy, sqrt(vx * vx + vz * vz))

    def toYawFromYUp(self):
        return arctan2(2 * (self.x * self.y + self.w * self.y),
                       1.0 - 2 * (self.x * self.x + self.y * self.y))

    def toRollFromYUp(self):
        return arctan2(2 * (self.x * self.y + self.w * self.z),
                       1.0 - 2 * (self.x * self.x + self.z * self.z))
                       
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

    def __init__(self, sleep_func):
        self.sleep_func = sleep_func
        self.telemetry_err_str = "Waiting to connect to NoLimits Coaster"
        self.telemetry_status_ok = False
        self.telemetry_data = None
        self._telemetry_state_flags = 0
        self.prev_yaw = None
        self.prev_time = time.time()
        self.lift_height = 32  # max height in meters
        self.is_paused = False
        self.is_nl2_connected = False
        self.nl2_version = None
        self.start_time = time.time()  
        self.nl2_msg_buffer_size = 255
        self.nl2_msg_port = 15151
        self.nl2Q = Queue()     

        
    def begin(self):
        log.info("Starting nl2 interface")
        self.nl2_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nl2_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.nl2_sock.settimeout(0.5) # telemetry requests sent after each timeout

    def start_listening(self):
        t = threading.Thread(target=self.listener_thread, args= (self.nl2_sock,))
        t.daemon = True
        t.start()
        
    def connect_to_coaster(self, coaster_ip_addr = '127.0.0.1'):
        # returns true iff connected to NL2 and in play mode
        # if is_pc_connected == False:
        #     log.error("Not connected to VR PC")
        #     return False
        if self.is_nl2_connected == False:
            try:
                log.debug("Attempting connect to NoLimits @ %s:%d",coaster_ip_addr, self.nl2_msg_port)
                while  self.is_nl2_connected == False:
                    self.nl2_sock = socket.create_connection((coaster_ip_addr, self.nl2_msg_port),1) # timeout after one second
                    log.debug("nl2 connected")
                    self.is_nl2_connected = True
                    self.start_listening() # create listening thread
                    self.sleep_func(1)
                    self.get_nl2_version()
            except Exception as e:
                self.is_nl2_connected = False
                # if "Errno 10056" in str(e):
                self.nl2_sock.close()
                self.nl2_version == None
                log.error("Error connecting to NoLimits socket %s", str(e))
                return False

        #print "telemetry flags = ", self._telemetry_state_flags 
        return True  # TODO ???


    def dispatch(self, train=0, station=0):
        msg = pack('>ii', train, station)  # coaster, station
        r = self._create_NL2_message(self.N_MSG_DISPATCH, self._get_msg_id(), msg)
        #  print "dispatch msg",  binascii.hexlify(msg),len(msg), "full", binascii.hexlify(r)
        self._send(r)

    def set_pause(self, isPaused):
        msg = pack('>?', isPaused) # pause if arg is True
        r = self._create_NL2_message(self.N_MSG_SET_PAUSE, self._get_msg_id(), msg)
        # print("set pause msg", isPaused)
        self._send(r)
        self.pause_mode = isPaused

    #  see NL2TelemetryClient.java in NL2 distribution for message format
    def _create_simple_message(self, msgId, requestId):  # message with no data
        result = pack(b'>cHIHc', b'N', msgId, requestId, 0, b'L')
        return result

    def _create_NL2_message(self, msgId, requestId, msg):  # message is packed
        #  fields are: N Message Id, reqest Id, data size, L
        start = pack(b'>cHIH', b'N', msgId, requestId, len(msg))
        end = pack(b'>c', b'L')
        result = start + msg + end
        return result

    def _get_msg_id(self):
        id = int((time.time() - self.start_time) * 1000);
        # print "msg id=", id
        return id

    def _send(self, r):
        #  msg, requestId, size = (unpack('>HIH', r[1:9]))
        #print("sending:", r)
        # above just for debug
        try:
            self.nl2_sock.sendall(r)
        except Exception as e:
            print(str(e))
        # self.sleep_func(.001)

    def get_nl2_version(self):
        self.nl2_version = None
        self._send(self._create_simple_message(self.N_MSG_GET_VERSION, self._get_msg_id()))
        #  print("getting version")
        for i in range(10):
            self.sleep_func(.1)            
            self.service()
            if self.nl2_version != None:
                return self.nl2_version
        return None  # NL2 did not respone

    def get_telemetry_err_str(self):
        return self.telemetry_err_str

    def get_telemetry_status(self):
        return self.telemetry_err_str

    def get_telemetry(self, timeout):
        try:
            self._send(self._create_simple_message(self.N_MSG_GET_TELEMETRY,self._get_msg_id()))
            start = time.time()
            self.telemetry_data = None
            while time.time() - start < timeout:
                self.service()
                if self.telemetry_data != None:
                    #  print(self.telemetry_data)
                    # print "in get_telemetry, latency=", time.time() - start 
                    return self.telemetry_data
            log.debug("timeout in get_telemetry")
        except Exception as e:
            log.error("error in get_telemetry: %s", e)
            print(traceback.format_exc())
        return None, None

    def service(self):
        while self.nl2Q.qsize() > 0:
            msg, requestId, data, size = self.nl2Q.get()
            #  print("in service", msg, requestId, size)
            self._process_nl2_msgs(msg, requestId, data, size)

    def _process_nl2_msgs(self, msg, requestId, data, size):
        try:
            #  print("telemetry msg: ", msg, requestId, size)
            if msg == self.N_MSG_VERSION:
                v0, v1, v2, v3 = unpack('cccc', data)
                self.nl2_version = format("%c.%c.%c.%c" % (chr(ord(v0)+48),chr(ord(v1)+48),chr(ord(v2)+48), chr(ord(v3)+48)))
                log.info('NL2 version: %s', self.nl2_version)
                self.is_nl2_connected = True
            elif msg == self.N_MSG_TELEMETRY:
                if size == 76:
                    t = (unpack('>IIIIIIIIfffffffffff', data))
                    tm = self.telemetryMsg._make(t)
                    # print("tm", tm)
                    self.telemetry_data = self._process_telemetry_msg(tm)
                    self.telemetry_status_ok = True
                else:
                    print('invalid msg len expected 76, got ', size)
                #self.sleep_func(self.interval)
                #self._send(self._create_simple_message(self.N_MSG_GET_TELEMETRY, self.N_MSG_GET_TELEMETRY))
            elif msg == self.N_MSG_OK:
                self.telemetry_status_ok = True
                self.is_nl2_connected = True
                pass
            elif msg == self.N_MSG_ERROR:
                self.telemetry_status_ok = False
                self.telemetry_err_str = data
                #print("telemetry err:", self.telemetry_err_str)
                log.debug("telemetry err for msg %d, req id %d: %s" , msg, requestId, self.telemetry_err_str)

            else:
                print('unhandled message', msg, requestId, size, data)
        except:
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print("Error processing NoLimits message",e,s)
            #self.self.is_nl2_connected = False

    def _process_telemetry_msg(self, msg):
        """
        returns two fields:
            float  coaster speed in meters per seconds
            list of the six xyzrpy values
        """
        self._telemetry_state_flags = msg.state
        is_in_play_mode = (msg.state & 1) != 0
        if is_in_play_mode == False:
           # print("in process msg, play state changed to", is_play_mode)
           self.is_in_play_mode = is_play_mode
        if is_in_play_mode:  # only process if coaster is in play
            y =[]
            if(False): # set this to True to use real world values (not supported in this version)
                #  code here is non-normalized (real) translation and rotation messages
                quat = Quaternion(msg.quatX, msg.quatY, msg.quatZ, msg.quatW)
                pitch = degrees(quat.toPitchFromYUp())
                yaw = degrees(quat.toYawFromYUp())
                roll = degrees(quat.toRollFromYUp())
                #print format("telemetry %.2f, %.2f, %.2f" % (roll, pitch, yaw))
            else:  # normalize
                #print "quat", msg.quatX, msg.quatY, msg.quatZ, msg.quatW,
                quat = Quaternion(msg.quatX, msg.quatY, msg.quatZ, msg.quatW) 
                self.quat = quat
                roll = quat.toRollFromYUp() / pi
                pitch = -quat.toPitchFromYUp() * 0.6 # reduce intensity of pitch
                yaw = -quat.toYawFromYUp()
                y.append(yaw)
                
                self.flip=0
                if self.prev_yaw != None:
                    # handle crossings between 0 and 360 degrees
                    if yaw - self.prev_yaw > pi:
                        yaw_rate = (self.prev_yaw - yaw) + (2*pi)
                        self.flip= 2
                    elif  yaw - self.prev_yaw < -pi:
                        yaw_rate = (self.prev_yaw - yaw) - (2*pi)
                        self.flip= -2
                    else:
                        yaw_rate = self.prev_yaw - yaw
                    time_delta = time.time() - self.prev_time
                    self.prev_time = time.time()
                    dbgYr1 = yaw_rate
                else:
                    yaw_rate = 0
                if self.prev_yaw != None:
                    y.append(yaw-self.prev_yaw)
                else:
                    y.append(0)
                y.append(yaw_rate)
                self.prev_yaw = yaw
                ###if yaw_rate != 0:
                ###   print(yaw,yaw_rate, self.flip)
                # the following code limits dynamic range nonlinearly
                if yaw_rate > pi:
                   yaw_rate = pi
                elif yaw_rate < -pi:
                    yaw_rate = -pi
                dbgYr2 = yaw_rate
                yaw_rate = yaw_rate / 2
                if yaw_rate >= 0:
                    yaw_rate = sqrt(yaw_rate)
                elif yaw_rate < 0:
                    yaw_rate = -sqrt(-yaw_rate)
                dbgYr3 = yaw_rate
                #self.dbg_yaw = format("%.3f, %.3f, %.3f, %.3f, %d" % (yaw, dbgYr1,dbgYr2,dbgYr3, flip))

                #  y from coaster is vertical
                #  z forward
                #  x side
                if msg.posY > self.lift_height:
                   self.lift_height = msg.posY
                heave = ((msg.posY * 2) / self.lift_height) -1
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

                y.append(yaw_rate)
                data = [surge, sway, heave, roll, pitch, yaw_rate]
                intensity_factor = 0.4  # larger values are more intense
                yaw_rate = yaw_rate * 2 # increase intensity of yaw

                self.is_paused = msg.state == 7  # 3 is running, 7 is paused
                speed = float(msg.speed)
                telemetry_data = [(elem * intensity_factor)  for elem in data]
                return (speed, telemetry_data)


            #print "pitch=", degrees( quat.toPitchFromYUp()),quat.toPitchFromYUp(), "roll=" ,degrees(quat.toRollFromYUp()),quat.toRollFromYUp()
        #  print "in telemetry, Coaster not in play mode"
        self.is_in_play_mode = False
        #self.set_coaster_status(ConnectStatus.is_in_play_mode, False)
        return [0, None]

    def listener_thread(self, sock):
        """ received msgs added to queue, telemetry requests sent on socket timeout """
        # print ("starting listener thread")
        header = bytearray(9)
        while self.is_nl2_connected:
            try:
                if self.is_nl2_connected:
                    header = bytearray(sock.recv(1))
                    if header and len(header) > 0:
                        if header != b'N':
                            print("sock header error:",  header[0], hex(header[0]))
                            continue
                        for i in range(8):
                            b = bytearray(sock.recv(1))
                            header.extend(b)
                        msg, requestId, size = (unpack('>HIH', header[1:9]))
                        data = bytearray(sock.recv(size))
                        if bytearray(sock.recv(1)) != b'L':
                            print("Invalid message received")
                            continue
                        #  print("got valid msg, len=", len(data), ":".join("{:02x}".format(ord(c)) for c in data))
                        self.nl2Q.put((msg, requestId, data, size))
                    else:
                        self.is_nl2_connected = False

            except socket.timeout:
                self._send(self._create_simple_message(self.N_MSG_GET_TELEMETRY, self._get_msg_id()))
                log.debug("timeout in listener")
                pass
            except ValueError:
                print("got zero from socket, assume its disconnected")
                self.is_nl2_connected = False
                self.sleep_func(1)
            except Exception as e: 
                #e = sys.exc_info()[0]
                s = traceback.format_exc()
                print("listener thread err", str(e), s)
        print("exiting listener thread")


if __name__ == "__main__":
    coaster = CoasterInterface(time.sleep)
    coaster.begin()
    coaster.connect_to_coaster()


    while True:
        coaster.service()
        print(coaster.get_telemetry(1))
