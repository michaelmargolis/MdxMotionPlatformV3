"""
NL2_park.py  interface module
Copyright Michael Margolis, Middlesex University 2019; see LICENSE for software rights.
This version requires NoLimits attraction license and NL ver 2.5.3.5 or later
"""

import sys
import time
from struct import pack, unpack
import collections
import sys
import ctypes #  for bit fields
import os
import  binascii  # only for debug
import traceback

sys.path.insert(0, os.getcwd())  # for runtime root
from common.tcp_tx_rx import TcpTxRx, socket
from agents.nolimits_coaster.transform  import Transform

VERBOSE_LOG = True # set true for verbose debug logging

import logging
log = logging.getLogger(__name__)

class StationStatus():
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

class Nl2MsgType():
    OK = 1
    ERROR = 2
    GET_VERSION = 3 # datasize 0
    VERSION = 4
    GET_TELEMETRY = 5  # datasize 0
    TELEMETRY = 6
    GET_STATION_STATE = 14 #size=8 (int32=coaster index, int32=station index)
    STATION_STATE = 15 #DataSize = 4 
    SET_MANUAL_MODE = 16 # datasize 9
    DISPATCH = 17  # datasize 8
    SET_GATES = 18  # datasize 9
    SET_HARNESS = 19  # datasize 9
    SET_PLATFORM = 20  # datasize 9
    LOAD_PARK = 24   # datasize 1 + string 
    CLOSE_PARK = 25  # datasize 0
    SET_PAUSE = 27   # datasize 1
    RESET_PARK = 28  # datasize 1
    SELECT_SEAT = 29 # datasize = 16 
    SET_ATTRACTION_MODE = 30   # datasize 1
    RECENTER_VR = 31 # datasize 0

class ConnState:
    DISCONNECTED, NOT_IN_SIM_MODE, READY = list(range(3))

    @staticmethod
    def text(state):
        return ("Not Connected", "Not in sim mode", "Ready")[state]
        
def is_bit_set(integer, position):
    return integer >> position & 1 > 0

class Nl2_Link():
    def __init__(self):
        self.tcp = TcpTxRx()
        self.connection_state = ConnState.DISCONNECTED

    def connect(self):
        try:
            self.tcp.connect()
            return True
        except Exception as e:
            print(e)
        return False

    def is_connected(self):
        # return true if tcp connected but may not be in sim mode
        return  self.tcp.is_connected

    def send_msg(self, msg_type, data=None):
        """ format and send msg to nl2
        if reply is none then tcp not connected
        elif reply contains "not in play" then nl2 cannot accept requests (except load park)
        """
        self.perf_start = time.perf_counter() # for performance testing
        if data:
             self.send_raw(self._create_NL2_message(msg_type, self._get_msg_id(), data))
        else:
            self.send_raw(self._create_simple_message(msg_type, self._get_msg_id()))
        reply = self.listen_for(msg_type)
        if reply == None:
            self.connection_state  = ConnState.DISCONNECTED
            #fixme check if none because connected but bad msg format ??
        else:
            if 'Not in play mode' in str(reply):
                self.connection_state = ConnState.NOT_IN_SIM_MODE
                reply = None
            elif msg_type == Nl2MsgType.GET_TELEMETRY:
                t = (unpack('>IIIIIIIIfffffffffff', reply))
                # print("wha in nl2: telem state bit =", is_bit_set(t[0],0))
                if is_bit_set(t[0],0): # check if in play mode
                    self.connection_state = ConnState.READY
                else:
                    self.connection_state = ConnState.NOT_IN_SIM_MODE
                    reply = None
            else:
                if self.connection_state  == ConnState.DISCONNECTED:
                    self.connection_state = ConnState.NOT_IN_SIM_MODE
        return reply

    def send_raw(self, msg):
        try:
            self.tcp.send(msg)
        except Exception as e:
            print(str(e))

    def listen_for(self, msg_id):
        """ return msg or None if no connection, invalid msg, or not in sim mode"""
        # log.debug("Starting to listen for Nl2 messagess")
        try:
            blob = (self.tcp.receive(1))
            if blob and len(blob) > 0:
                header = bytearray(blob)
                if header != b'N':
                    log.error("sock header error: exoeced 0x4E got %s", hex(header[0]))
                    return None
                for i in range(8):
                    b = bytearray(self.tcp.receive(1))
                    header.extend(b)
                msg_type, requestId, size = (unpack('>HIH', header[1:9]))
                if msg_type == Nl2MsgType.ERROR:
                    None
                data = bytearray(self.tcp.receive(size))
                if bytearray(self.tcp.receive(1)) != b'L':
                    log.warning("Invalid message received in nl2 listener")
                    return None
                self.reply_latency = time.perf_counter() - self.perf_start
                return data
        except socket.timeout:
            log.error("timout waiting for Nl2 reply for msg id %d", msg_id)
        except Exception as e:
            log.error("error waiting for Nl2 reply: %s", str(e))
            print(traceback.format_exc())
        return None

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
        id = int((time.perf_counter() - self.start_time) * 1000);
        return id

class Nl2Messenger(Nl2_Link):

    telemetryMsg = collections.namedtuple('telemetryMsg', 'state, frame, viewMode, coasterIndex,\
                                           coasterStyle, train, car, seat, speed, posX, posY,\
                                           posZ, quatX, quatY, quatZ, quatW, gForceX, gForceY, gForceZ')

    def __init__(self):
        super().__init__()
        self.coaster = 0 # the current coaster
        self.station = 0 # current station
        self.telemetry_msg = None # most recent nl2 telemetry msg
        self.is_pause_state = False
        self.transform = Transform()
        log.debug("Verbose debug logging is %s", VERBOSE_LOG)

    def begin(self):
        self.start_time = time.perf_counter()

    def service(self):
        # updates telemetry_msg and connection_state
        if self.is_connected:
            self.telemetry_msg = self.get_telemetry()

    def get_conn_state_str(self): # only used for debug
        return ConnState.text(self.connection_state)

    def get_nl2_version(self):
        reply = self.send_msg(Nl2MsgType.GET_VERSION)
        if reply:
            v0, v1, v2, v3 = unpack('cccc', reply)
            nl2_version = format("%c.%c.%c.%c" % (chr(ord(v0)+48),chr(ord(v1)+48),chr(ord(v2)+48), chr(ord(v3)+48)))
            log.info('NL2 version: %s', nl2_version)
            return nl2_version

    def get_telemetry(self):
        reply = self.send_msg(Nl2MsgType.GET_TELEMETRY)
        if reply:
            t = (unpack('>IIIIIIIIfffffffffff', reply))
            self.telemetry_msg = self.telemetryMsg._make(t)
            if not is_bit_set(self.telemetry_msg.state, 0):
                self.connection_state = ConnState.NOT_IN_SIM_MODE
            self.is_pause_state = is_bit_set(self.telemetry_msg.state, 2) 
            # print(self.telemetry_msg)
            return self.telemetry_msg
        return None

    def get_transform(self):
        """ returns transform from latest telemetry msg as: xyzrpy 
            get_telemetry should be called before get_transform     """
        if self.telemetry_msg:
            # transform is: [surge, sway, heave, roll, pitch, yaw]
            return self.transform.get_transform(self.telemetry_msg)
        return None

    def is_paused(self):
        """ returns True if was paused at most recent telemetry msg"""
        return self.is_pause_state

    def update_station_state(self):
        # returns True if state is available (ie, play mode)
        data = pack('>ii', self.coaster, self.station)  
        reply = self.send_msg(Nl2MsgType.GET_STATION_STATE, data)
        if reply is None or 'Not in play mode' in str(reply):
            return False
        else:
            state = unpack('>I', reply)
            self.station_state_bitfield = state[0]
            self._decode_station_state(state[0])
            return True
            
    def dispatch(self, train, station):
        data = pack('>ii', train, station)  # coaster, station
        reply = self.send_msg(Nl2MsgType.DISPATCH, data)

    def set_gates(self, mode): # True opens, False closes
        data = pack('>ii?', self.coaster, self.station, mode)
        reply = self.send_msg(Nl2MsgType.SET_GATES, data)

    def set_harness(self, mode): # True opens, False closes
        data = pack('>ii?', self.coaster, self.station, mode)
        reply = self.send_msg(Nl2MsgType.SET_HARNESS, data)

    def set_floor(self, mode): # True lowers, False raises
        data = pack('>ii?', self.coaster, self.station, mode)  
        reply = self.send_msg(Nl2MsgType.SET_PLATFORM, data)

    def set_manual_mode(self, mode):
        data = pack('>ii?', self.coaster, self.station, mode)  # True sets manual mode, false sets auto
        reply = self.send_msg(Nl2MsgType.SET_MANUAL_MODE, data)

    def reset_vr(self):
        reply = self.send_msg(Nl2MsgType.RECENTER_VR)
        log.info("reset rift")

    def load_park(self, isPaused, park):
        path = park.encode('utf-8')
        data = pack('>?', isPaused) + path  # start in pause, park string
        reply = self.send_msg(Nl2MsgType.LOAD_PARK, data)
        if reply == None or 'invalid file path' in str(reply):
            return False
        return True

    def close_park(self):
        self.send_msg(Nl2MsgType.CLOSE_PARK)

    def set_pause(self, isPaused):
        data = pack('>?', isPaused) # pause if arg is True
        reply = self.send_msg(Nl2MsgType.SET_PAUSE, data)

    def reset_park(self, start_paused):
        data = pack(b'>?', start_paused) # start paused if arg is True
        reply = self.send_msg(Nl2MsgType.RESET_PARK, data)

    def select_seat(self, seat):
        data = pack(b'>iiii', self.coaster, 0, 0, seat)  # coaster, train, car, seat 
        reply = self.send_msg(Nl2MsgType.SELECT_SEAT, data)

    def set_attraction_mode(self, state):
        data = pack(b'>?', state)   # enable mode if state True
        reply = self.send_msg(Nl2MsgType.SET_ATTRACTION_MODE, data)

    def _decode_station_state(self, state):
        self.e_stop = is_bit_set(state, 0)
        self.manual_dispatch = is_bit_set(state, 1)
        self.can_dispatch = is_bit_set(state, 2)
        self.can_close_gates = is_bit_set(state, 3)
        self.can_open_gates = is_bit_set(state, 4)
        self.can_close_harness = is_bit_set(state, 5)
        self.can_open_harness = is_bit_set(state, 6)
        self.can_raise_platform = is_bit_set(state, 7)
        self.can_lower_platform = is_bit_set(state, 8)
        self.can_lock_flyer_car = is_bit_set(state, 9)
        self.can_unlock_flyer_car = is_bit_set(state, 10)
        self.train_in_station = is_bit_set(state, 11)
        self.train_in_station_is_current = is_bit_set(state, 12)

    def is_train_in_station(self):
        if self.update_station_state():
            ret =  self.train_in_station and self.train_in_station_is_current
            return ret
        else:
            return False


if __name__ == "__main__":
    #  identifyConsoleApp()
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(module)s: %(message)s',
                            datefmt='%H:%M:%S')
    log.info("Python: %s", sys.version[0:5])
    log.debug("logging using debug mode")

    nl2 = Nl2Messenger()
    nl2.begin()
    nl2.connect()
    nl2.get_nl2_version()
    print("reply latency was", nl2.reply_latency) 
    
    nl2.get_telemetry()
    print("reply latency was", nl2.reply_latency) 
    
    nl2.update_station_state()
    print("reply latency was", nl2.reply_latency) 

    print("estop", nl2.e_stop)
    print("manual dispatch", nl2.manual_dispatch )
    print("can dispatch", nl2.can_dispatch )
    print("can close gates", nl2.can_close_gates)
    print("can open gates", nl2.can_open_gates )
    print("can close harness", nl2.can_close_harness ) 
    print("can open harness", nl2.can_open_harness )
    print("can raise platform", nl2.can_raise_platform )
    print("can lower platform", nl2.can_lower_platform )
    print("train is in station", nl2.train_in_station)

    nl2.set_manual_mode(True)
    print("reply latency was", nl2.reply_latency) 
    
    nl2.reset_park(False)
    print("reply latency was", nl2.reply_latency) 

    nl2.is_train_in_station()



