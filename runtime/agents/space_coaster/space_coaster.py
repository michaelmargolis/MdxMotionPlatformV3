"""
  Space_coaster for V3 software

  This version reads telemetry data from a CSV file
  Orientation from this file synced to UDP frames sent by SpaceCoaster
  on port 10009 (only state data in coaster msg frames is used)
"""

import sys
from os import path
import socket
# from math import radians, degrees
from threading import Thread, Lock
import time
from queue import Queue


import traceback
import csv,os
import win32gui
import ctypes 
from ctypes import wintypes 
import numpy as np  # for scaling telemetry data

sys.path.insert(0, os.getcwd())  # for runtime root
try:
    from agents.agent_base import AgentBase, RemoteMsgProtocol
    from agents.ride_state import RideState
    from common.tcp_server import TcpServer
    from common.dialog import ModelessDialog

    from platform_config import cfg
except Exception as e:
    print(e, os.getcwd())
    print(traceback.format_exc())

import logging
log = logging.getLogger(__name__)

class SC_State:  # these are space coaster specific states
    disconnected, initializing, waiting, ready, running, completed = list(range(-1,5))

class ConnectionException(Exception):
    pass

class SimInterface(AgentBase): # todo  rename to AgentInterface ??

    def __init__(self, instance_id, event_addr, event_sender):
        super(SimInterface, self).__init__(instance_id, event_addr, event_sender)
        self.sleep_func = time.sleep # todo - replace with function that checks  kbhit
        self.name = "Space Coaster"
        log.debug("initializing %s with id %s", self.name, self.instance_id)
        self.log = None
        self.is_normalized = True
        self.expect_degrees = False # convert to radians if True
        self.max_values = [80, 80, 80, 0.4, 0.4, 0.4]
        self.telemetry = []
        self.frame_number = 0
        self.frame_interval = 0.05  # secs between frames
        self.coaster_status_str = "Waiting to complete initial run!orange"
        self.sim_connection_state_str = 'waiting sim connection!orange'

        self.sc_state_str = ("Initializing", "Waiting", "Ready", "Running", "Completed")
        self.sc_state = -1 # this is the internal space coaster state
        self.state = RideState.DISABLED  # this is the generic ride state used by all agents
        self.is_paused = False
        self.actions = {'pause': self.pause, 'dispatch': self.dispatch, 'reset': self.reset_vr}

    def set_focus(self, window_class=None, window_title=None):
        try:
            guiHwnd = win32gui.FindWindow(window_class,window_title)
            log.debug("window name=%s, class=%s, Hwnd= %d", window_title, window_class, guiHwnd)
            ctypes.windll.user32.SetForegroundWindow(guiHwnd)
            # win32gui.SetForegroundWindow(guiHwnd)
        except Exception as e:
            print(e, traceback.format_exc())

    def left_mouse_click(self):
        #print "left mouse click"
        ctypes.windll.user32.SetCursorPos(100, 20)
        #self.set_focus("UnityWndClass")
        ctypes.windll.user32.mouse_event(2, 0, 0, 0,0) # left down
        ctypes.windll.user32.mouse_event(4, 0, 0, 0,0) # left up
        #self.set_focus("TkTopLevel")

    def right_mouse_click(self):
        ctypes.windll.user32.SetCursorPos(100, 20)
        ctypes.windll.user32.mouse_event(8, 0, 0, 0,0) # right down
        ctypes.windll.user32.mouse_event(16, 0, 0, 0,0) # right up

    def get_ride_state(self):
        return self.state

    def pause(self):
        log.debug("in pause, ride state is %s, Is_paused=%s", RideState.str(self.state), self.is_paused)
        if self.state == RideState.PAUSED:
            log.debug("Unpausing coaster")
            self.set_focus("UnityWndClass") # or could use window title:'Coaster MSU'
            self.is_paused = False
            self.state = RideState.RUNNING
            self.coaster_status_str = "Coaster running!green"
        elif self.state == RideState.RUNNING:
            log.debug("Pausing coaster")
            log.warning("if pause does not work, check space coaster local agent MainWindow name")
            self.set_focus("Qt5QWindowIcon", "MainWindow")
            self.is_paused = True
            self.state = RideState.PAUSED
            self.coaster_status_str = "Coaster paused!orange"

    def reset_vr(self):
        log.info("resetting Rift")
        self.right_mouse_click()

    def dispatch(self):
        self.left_mouse_click()
        log.debug("dispatched")

    def remote_info(self):
        log.warning("remote request for info not supported")

    def begin(self):
        self.read_telemetry()
        self.xyzrpyQ = Queue()
        self.cmdQ = Queue()
        # space coaster must be run on same pc running this agent
        t = Thread(target=self.listener_thread, args= ('', cfg.SPACE_COASTER_PORT))
        t.daemon = True
        t.start()
        self.connect()
        try:
            log.debug("attempting to set focus")
            self.set_focus("UnityWndClass","Coaster MSU")
            log.info("found space coaster window")
            self.left_mouse_click()
            # break
        except Exception as e:
            print("Space_coaster.begin:" + str(e) )
            print(traceback.format_exc())
        log.info("space coaster agent started")


    def fin(self):
        # client exit code goes here
        pass

    def connect(self):
        self.is_coaster_connected = False
        log.info("Connecting to space coaster sim")
        self.sim_connection_state_str = 'waiting sim connection!orange'
        while not self.is_coaster_connected:
            self.sim_connection_state_str = 'waiting sim connection!orange'
            log.debug("waiting for connection")
            self.service()
            self.sleep_func(.25) # proxy heartbeat expects < 1 sec between msgs            
        self.sim_connection_state_str = 'sim connected!green'
        # self.dialog.close()
        log.info("Connected to space coaster sim")

    def handle_command(self, command):
        if command[0] in self.actions:
            self.actions[command[0]]()
        else:
            log.warning("unhandled command (%s)", command)

    def service(self):
        msg = None
        try:
            while  self.cmdQ.qsize() > 0:
                sc_state = self.cmdQ.get()
                if sc_state == SC_State.disconnected:
                    self.sim_connection_state_str = 'sim connected!green'
                else:
                    self.is_coaster_connected = True
                    self.process_state(sc_state)

            if self.xyzrpyQ.qsize() == 0:               
                status = "Stopped at telemetry frame %d" % (self.frame_number)
                self.coaster_status_str = status + "!orange"
                if not self.is_paused:
                    log.warning("in service, setting is_paused True because coaster q is empty")
                    self.is_paused = True
            else:
                self.is_coaster_connected = True
                if self.state == RideState.RUNNING:
                    try:
                        self.set_transform(self.telemetry[self.frame_number])
                    except IndexError:
                        log.warning("telemetry frame error, reset frame to 0")
                        self.frame_number = 0
                    #  print "coaster running", self.frame_number, [ '%.2f' % elem for elem in self.transform]
                    if False:  # set true to only update status every 20 frames
                        if self.frame_number % 20 == 0:
                            status = format("Running frame %d, time %d" % (self.frame_number, self.frame_number/20))
                    else:
                        status = format("Running frame %d, time %.1f" % (self.frame_number, self.frame_number/20.0))
                    self.coaster_status_str = status +  "!green"
                    self.frame_number += 1
                    if self.frame_number >= len(self.telemetry):
                        log.warning("Invalid telemetry frame, reset frame to 0")
                        print(self.frame_number, len(self.telemetry))
                        self.frame_number = 0
                        
                    x = self.xyzrpyQ.get()
                    while self.xyzrpyQ.qsize() > 2:
                        x1 = self.xyzrpyQ.get()
                        ##  print x
                        x=x1 
                    self.xyzrpyQ.queue.clear()

            event = RemoteMsgProtocol.encode(self.instance_id, self.frame_interval*self.frame_number, self.frame_number, self.state, self.is_paused,
                                    self.get_transform(), self.coaster_status_str, self.sim_connection_state_str)
            self.event_sender.send(event.encode('utf-8'), self.event_address)

        except Exception as e:
            s = traceback.format_exc()
            log.error("SC service error %s, %s, frame=%d", e, s, self.frame_number)

    def process_state(self, new_sc_state):
        if self.sc_state == new_sc_state:  return

        if self.sc_state == -1 and new_sc_state == SC_State.initializing:
            log.info("SC state transition to initial message from coaster")
            self.coaster_status_str = "Starting software!orange"
            self.state = RideState.NON_SIM_MODE
        elif self.sc_state == SC_State.initializing and new_sc_state == SC_State.waiting:
            log.info("SC state transition from startup to waiting in lobby")
            self.coaster_status_str = "Loading coaster!orange"
            self.sleep_func(2)
            self.left_mouse_click()
            self.state = RideState.NON_SIM_MODE
        elif self.sc_state == SC_State.waiting and new_sc_state == SC_State.ready:
            log.info("coaster is ready for dispatch")
            self.coaster_status_str = "Ready for dispatch!green"
            self.state = RideState.READY_FOR_DISPATCH
        elif self.sc_state == SC_State.ready and new_sc_state == SC_State.running :
            log.info("Coaster is starting run")
            self.coaster_status_str = "Running!green"
            self.frame_number = 0
            self.state = RideState.RUNNING
        elif self.sc_state == SC_State.running and new_sc_state == SC_State.completed:
            self.coaster_status_str = "Entering hyperspace!green"
            self.sleep_func(6)
            log.info("ready to reset")
            self.left_mouse_click()
            self.state = RideState.NON_SIM_MODE
        elif self.sc_state == SC_State.completed and new_sc_state == SC_State.waiting:
            log.info("SC state transition from completed to waiting in lobby")
            self.coaster_status_str = "Getting ready!orange"
            self.sleep_func(2)
            self.left_mouse_click()
            self.state = RideState.NON_SIM_MODE
        elif self.sc_state == SC_State.running and new_sc_state == SC_State.waiting:
            # this event happens if coaster sends running state after completed
            log.info("SC state transition from running to waiting in lobby")
            self.coaster_status_str = "Waiting!orange"
            self.sleep_func(2)
            self.left_mouse_click()
            self.state = RideState.NON_SIM_MODE
        elif self.sc_state == SC_State.completed and new_sc_state == SC_State.running:
            # anomaly to be ignored
            self.sc_state = SC_State.completed
        elif self.sc_state == SC_State.running and new_sc_state == SC_State.initializing:
            # this happens because of a brief running state after completion
            pass
        else:
            log.warning("Ignoring out of sequence transition from state %s to %s", self.sc_state_str[self.sc_state], self.sc_state_str[new_sc_state])

        self.sc_state = new_sc_state
        # self.coaster_status_str = "Coaster state is: " + self.sc_state_str[self.state], "green"

    def listener_thread(self, HOST, PORT, ):
        try:
            MAX_MSG_LEN = 512
            sc_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sc_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sc_sock.bind((HOST, PORT))
            log.info("opening space coaster socket on port %s:%d", HOST, PORT)
            while True:
                try:
                    msg = sc_sock.recv(MAX_MSG_LEN).decode('utf-8')
                    if msg == '':
                       self.cmdQ.put(SC_State.disconnected)
                    else:
                        if msg is not None:
                            msg = msg.rstrip()
                            # print(msg)
                            if msg.find("xyzrpy") == 0:
                                now = time.time()
                                self.xyzrpyQ.put([now,msg])
                            elif msg.find("command") == 0:
                                self.cmdQ.put(msg)
                            elif msg.find("config") == 0:
                                self.cmdQ.put(msg) # config messages go onto command queue
                            elif msg.find("state") == 0:
                                 s = msg.split(',')
                                 self.cmdQ.put(int(s[1])) # state messages go onto command queue

                except Exception as e:
                    s = traceback.format_exc()
                    if msg:
                        log.error("listener err %s,%s, msg(%s)", e, s, msg)
                    else:
                        log.error("listener err %s,%s", e, s)
                    self.cmdQ.put(SC_State.disconnected)
        except Exception as e:
            s = traceback.format_exc()
            log.fatal("Space coaster connection thread init err %s,%s", e, s)
            self.cmdQ.put(SC_State.disconnected)

    def read_telemetry(self):
        try:
            path = os.path.abspath('agents/space_coaster/chairGen_telemetry.csv')
            if not os.path.isfile(path): path = 'chairGen_telemetry.csv'
            with open(path, 'r') as csvfile:
                log.info("opened space coaster telemetry file: chairGen_telemetry.csv")
                rows = csv.reader(csvfile, delimiter=',')
                for row in rows:
                    #  print row
                    if row is not None:
                        if len(row) >=6:
                            data = [float(f) for f in row[:6]]
                            # normalize
                            for idx, level in enumerate(data):
                                data[idx] = 0.7 * self.scale( data[idx], [-self.max_values[idx], self.max_values[idx], -1, 1] )
                            # print data
                            self.telemetry.append(data)
                log.info("Read %d frames into telemetry frame list",  (len(self.telemetry)))
                
        except Exception as e:
            s = traceback.format_exc()
            log.error("Error reading telemetry file %s %s", e,s)

    #function to scale a value, range is a list containing: (from_min, from_max, to_min, to_max)
    def scale(self, value, range):
        if value > range[1]:  # limit max
            return range[3]
        if value < range[0]:  # limit min
            return range[2]
        if range[1] == range[0]:
            return range[2] #avoid div by zero error
        else:
            return ( (value - range[0]) / (range[1] - range[0]) ) * (range[3] - range[2]) + range[2]
