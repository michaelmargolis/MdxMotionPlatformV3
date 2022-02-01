"""
NL2 interface module
Copyright Michael Margolis, Middlesex University 2019; see LICENSE for software rights.

This version requires NoLimits attraction license and NL ver 2.5.3.5 or later

"""
from __future__ import print_function
import sys
try:
    from queue import Queue
except ImportError:
    from Queue import Queue
import socket
from time import time
from struct import *
import collections
from math import pi, degrees, sqrt
import sys
import threading
import ctypes #  for bit fields
import os
import  binascii  # only for debug
import traceback
import numpy as np # only for yaw test

from clients.coaster.my_quaternion import Quaternion
from clients.coaster.coaster_state import SystemStatus 

import logging
log = logging.getLogger(__name__)

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

    def __init__(self, sleep_func):
        self.sleep_func = sleep_func
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
        self.station_msg_time = 0
        self.coaster_status = 0
        self.system_status = SystemStatus()
        self.nl2_version = None
        self.start_time = time()
        ##self.latencyMA = MovingAverage(16) # average nl2 messages
        ##self.average_latency = 15 #for nl2 msgs, updated in real time        
        self.nl2_msg_buffer_size = 255
        self.nl2_msg_port = 15151
        self.nl2Q = Queue()
        
        self.yaw_dbg = []
        
    def begin(self):
        log.info("Starting nl2 interface")
        self.nl2_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nl2_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.nl2_sock.settimeout(0.5) # telemetry requests sent after each timeout

    def start_listening(self):
        t = threading.Thread(target=self.listener_thread, args= (self.nl2_sock,))
        t.daemon = True
        t.start()
        
    def connect_to_coaster(self, coaster_ip_addr):
        # returns true iff connected to NL2 and in play mode
        # if self.system_status.is_pc_connected == False:
        #     log.error("Not connected to VR PC")
        #     return False
        if self.system_status.is_nl2_connected == False:
            try:
                log.debug("Attempting connect to NoLimits @ %s:%d",coaster_ip_addr, self.nl2_msg_port)
                while  self.system_status.is_nl2_connected == False:
                    self.nl2_sock = socket.create_connection((coaster_ip_addr, self.nl2_msg_port),1) # timeout after one second
                    log.debug("nl2 connected")
                    self.system_status.is_nl2_connected = True
                    self.start_listening() # create listening thread
                    self.sleep_func(1)
                    self.get_nl2_version()
            except Exception as e:
                self.system_status.is_nl2_connected = False
                # if "Errno 10056" in str(e):
                self.nl2_sock.close()
                self.nl2_version == None
                log.error("Error connecting to NoLimits socket %s", str(e))
                return False

        #print "telemetry flags = ", self._telemetry_state_flags 
        return True  # TODO ???


    def dispatch(self, train, station):
        self.yaw_dbg = []
        msg = pack('>ii', train, station)  # coaster, station
        r = self._create_NL2_message(self.N_MSG_DISPATCH, self._get_msg_id(), msg)
        #  print "dispatch msg",  binascii.hexlify(msg),len(msg), "full", binascii.hexlify(r)
        self._send(r)


    def prepare_for_dispatch(self):
        if self._get_station_status(bit_platform_can_lower):
            self.disengageFloor()
            log.debug("waiting for floor to lower")
            return False
        elif self._get_station_status(bit_harness_can_close):
            self.close_harness()
            log.debug("waiting for harness to close")
            return False
        else:
            return True
            #  can_dispatch = self._get_station_status(bit_can_dispatch)
            #  log.debug("can dispatch: %s", can_dispatch)
            # return can_dispatch

    def open_harness(self):
        # print 'Opening Harness'
        pass

    def close_harness(self):
        # print 'Closing Harness'
        pass
     
    def disengageFloor(self):
        #  print 'Disengaging floor'
        msg = pack('>ii?', 0, 0, True)  # coaster, car, True lowers, False raises
        r = self._create_NL2_message(self.N_MSG_SET_PLATFORM, self._get_msg_id(), msg)
        self._send(r)

    def set_manual_mode(self, mode):
        msg = pack('>ii?', 0, 0, mode)  # coaster, car, True sets manual mode, false sets auto
        r = self._create_NL2_message(self.N_MSG_SET_MANUAL_MODE, self._get_msg_id(), msg)
        #  print("set mode msg", mode, binascii.hexlify(r))
        self._send(r)

    def reset_vr(self):
        self._send(self._create_simple_message(self.N_MSG_RECENTER_VR, self._get_msg_id()))
        log.info("reset rift")
        np.savetxt('yaw.csv', self.yaw_dbg, delimiter=',', fmt='%0.3f') 

    def load_park(self, isPaused, park):
        #  print "in load park", park
        path = park
        #  print path
        start = time()
        msg = pack('>?', isPaused) + path  # start in pause, park string
        #  print msg
        #r = self._create_extended_NL2_message(self.N_MSG_LOAD_PARK, 43981, msg, len(path)+1)
        r = self._create_NL2_message(self.N_MSG_LOAD_PARK, 43981, msg)
        #  print "load park r", binascii.hexlify(r),"msg=", binascii.hexlify(msg)
        self.system_status.is_in_play_mode = False
        self._send(r)

        while True:
            # print self._telemetry_state_flags & 1,  self.get_coaster_status()
            # print(".", end=' ')
            self.sleep_func(2)
            self.get_telemetry(0.5)
            if self.telemetry_status_ok  and self.system_status.is_in_play_mode:
            # was if self._telemetry_state_flags & 1: # test if in play mode
                log.info("Setting manual mode")
                self.set_manual_mode(True)
                self.sleep_func(.3)
                #print "todo is this reset needed?"
                if self._get_station_status(bit_manual):
                   #print "resetting Park"
                   while self.telemetry_status_ok != True: 
                       self.get_telemetry(0.5)
                       print('?')
                   log.info("set manual mode")
                   break

    def close_park(self):
        self._send(self._create_simple_message(self.N_MSG_CLOSE_PARK, self._get_msg_id()))

    def set_pause(self, isPaused):
        msg = pack('>?', isPaused) # pause if arg is True
        r = self._create_NL2_message(self.N_MSG_SET_PAUSE, self._get_msg_id(), msg)
        # print("set pause msg", isPaused)
        self._send(r)
        self.pause_mode = isPaused

    def reset_park(self, start_paused):
        msg = pack(b'>?', start_paused) # start paused if arg is True
        r = self._create_NL2_message(self.N_MSG_RESET_PARK, self._get_msg_id(), msg)
        #  print "reset park msg", binascii.hexlify(r)
        self._send(r)

    def select_seat(self, seat):
        msg = pack(b'>iiii', 0, 0, 0, seat)  # coaster, train, car, seat 
        r = self._create_NL2_message(self.N_MSG_SELECT_SEAT, self._get_msg_id(), msg)
        # print "select seat msg", seat, binascii.hexlify(msg),len(msg), "full", binascii.hexlify(r)
        self._send(r)

    def set_attraction_mode(self, state):
        msg = pack(b'>?', state)   # enable mode if state True
        r = self._create_NL2_message(self.N_MSG_SET_ATTRACTION_MODE, self._get_msg_id(), msg)
        # print("set attraction mode msg", binascii.hexlify(r))
        self._send(r)

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
        id = int((time() - self.start_time) * 1000);
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

    def _get_station_status(self, status_mask):
        if self.system_status.is_in_play_mode == False:
            log.debug("Not in play mode")
            return False
        if time() - self.station_msg_time >= 1 or self.system_status.is_moving == False: 
            # send stutus request at most once per second
            msg = pack('>ii', 0, 0)  # coaster, station
            r = self._create_NL2_message(self.N_MSG_GET_STATION_STATE, self._get_msg_id(), msg)
            #  print "get station state msg", self.N_MSG_GET_STATION_STATE,  binascii.hexlify(msg),len(msg), "full", binascii.hexlify(r)
            self._send(r)
            self.station_msg_time = time()
        self.service()
        # print("station status", self.station_status)
        if status_mask == bit_manual and self.station_status & status_mask == status_mask: 
            return True
        if self.system_status.is_pc_connected == False: # TODO is this needed (play mode should be set to false if not connected
            return False
        #  print format("in get station status %x" % (self.station_status))
        if self.station_status & bit_manual != bit_manual:
            self.set_manual_mode(True)
            self.sleep_func(0.1)
        if self.station_status & bit_train_in_station == bit_train_in_station:
           #print "train status", self.station_status & bit_current_train_in_station, self.station_status & bit_current_train_in_station !=  bit_current_train_in_station
           if self.station_status & bit_current_train_in_station != bit_current_train_in_station:
               #  print "dispatching other train"
               self.dispatch(0,0)  # assume one coaster and one station
        #  print format("station status %x" % (self.station_status))
        return self.station_status & status_mask == status_mask # return true if all bits are set

    def is_train_in_station(self):
        #  print "is train in station", self._get_station_status(bit_train_in_station), self._get_station_status( bit_current_train_in_station)
        ret = self._get_station_status(bit_train_in_station | bit_current_train_in_station)
        #if ret: print "current train is in station"
        return ret

    def get_telemetry_err_str(self):
        return self.telemetry_err_str

    def get_telemetry_status(self):
        return self.telemetry_err_str

    def get_telemetry(self, timeout):
        try:
            self._send(self._create_simple_message(self.N_MSG_GET_TELEMETRY,self._get_msg_id()))
            start = time()
            self.telemetry_data = None
            while time() - start < timeout:
                self.service()
                if self.telemetry_data != None:
                    #  print(self.telemetry_data)
                    # print "in get_telemetry, latency=", time() - start 
                    return self.telemetry_data
            log.debug("timeout in get_telemetry")
        except Exception as e:
            log.error("error in get_telemetry: %s", e)
            print(traceback.format_exc())
        return None, None

    def service(self):
        """
        start = time()
        while self.nl2Q.qsize() < 1:
            if time()- start > 0.02:  #max wait for msg
                print "timeout"
                self._send(self._create_simple_message(self.N_MSG_GET_TELEMETRY,self._get_msg_id()))
                return
        """
        while self.nl2Q.qsize() > 0:
            msg, requestId, data, size = self.nl2Q.get()
            #  print("in service", msg, requestId, size)
            self._process_nl2_msgs(msg, requestId, data, size)

    def _process_nl2_msgs(self, msg, requestId, data, size):
        """
        if self.system_status.is_moving == False:
            # only calculate and show latency when stoppped
            delta = self._get_msg_id() - int(requestId)
            self.average_latency = self.latencyMA.next(delta)
            #  print "latency for msg",msg, "is", delta, self.average_latency
        """
        try:
            #  print("telemetry msg: ", msg, requestId, size)
            if msg == self.N_MSG_VERSION:
                v0, v1, v2, v3 = unpack('cccc', data)
                self.nl2_version = format("%c.%c.%c.%c" % (chr(ord(v0)+48),chr(ord(v1)+48),chr(ord(v2)+48), chr(ord(v3)+48)))
                log.info('NL2 version: %s', self.nl2_version)
                self.system_status.is_nl2_connected = True
            elif msg == self.N_MSG_STATION_STATE:
                s = unpack('>I', data)
                #  print format( "in telemetry, got station state msg %x" % (s[0]))
                self.station_status = s[0]
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
                self.system_status.is_nl2_connected = True
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
            #self.self.system_status.is_nl2_connected = False

    def _process_telemetry_msg(self, msg):
        """
        returns two fields:
            float  coaster speed in meters per seconds
            list of the six xyzrpy values
        """
        self._telemetry_state_flags = msg.state
        is_play_mode = (msg.state & 1) != 0
        if self.system_status.is_in_play_mode == False:
           # print("in process msg, play state changed to", is_play_mode)
           self.system_status.is_in_play_mode = is_play_mode
        if is_play_mode:  # only process if coaster is in play
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
                    time_delta = time() - self.prev_time
                    self.prev_time = time()
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
                self.yaw_dbg.append(y)
                data = [surge, sway, heave, roll, pitch, yaw_rate]
                intensity_factor = 0.4  # larger values are more intense
                yaw_rate = yaw_rate * 2 # increase intensity of yaw

                self.system_status.is_paused = msg.state == 7  # 3 is running, 7 is paused
                speed = float(msg.speed)
                self.system_status.is_moving = speed > 0.5
                #print "is moving=", self.system_status.is_moving, speed
                #print "telemetry_data", telemetry_data
                #telemetry_data = ['%.3f' % (elem * intensity_factor)  for elem in data]
                telemetry_data = [(elem * intensity_factor)  for elem in data]
                #if speed != 0:
                #    print ['%.3f' % (elem * intensity_factor)  for elem in data]
                return (speed, telemetry_data)


            #print "pitch=", degrees( quat.toPitchFromYUp()),quat.toPitchFromYUp(), "roll=" ,degrees(quat.toRollFromYUp()),quat.toRollFromYUp()
        #  print "in telemetry, Coaster not in play mode"
        self.system_status.is_in_play_mode = False
        #self.set_coaster_status(ConnectStatus.is_in_play_mode, False)
        return [0, None]

    def listener_thread(self, sock):
        """ received msgs added to queue, telemetry requests sent on socket timeout """
        # print ("starting listener thread")
        header = bytearray(9)
        while self.system_status.is_nl2_connected:
            try:
                if self.system_status.is_nl2_connected:
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
                        self.system_status.is_nl2_connected = False

            except socket.timeout:
                self._send(self._create_simple_message(self.N_MSG_GET_TELEMETRY, self._get_msg_id()))
                log.debug("timeout in listener")
                pass
            except ValueError:
                print("got zero from socket, assume its disconnected")
                self.system_status.is_nl2_connected = False
                self.sleep_func(1)
            except Exception as e: 
                #e = sys.exc_info()[0]
                """
                if "Errno 10053" in str(e):
                    print("NoLimits closed connection - todo tell GUI")
                    # sock.close()
                    self.system_status.is_nl2_connected = False
                    self.sleep_func(1)
                """
                s = traceback.format_exc()
                print("listener thread err", str(e), s)
        print("exiting listener thread")

if __name__ == "__main__":
    #  identifyConsoleApp()
    coaster = CoasterInterface()
    coaster_thread = threading.Thread(target=coaster.get_telemetry(0.5))
    coaster_thread.daemon = True
    coaster_thread.start()

    while True:
        if input('\nType quit to stop this script') == 'quit':
            break
