"""
 coaster_client control module for NoLimits2.
Copyright Michael Margolis, Middlesex University 2019; see LICENSE for software rights.
 
 module coordinates chair activity with logical coaster state 
This version requires NoLimits attraction license and NL ver 2.5.3.5 or later
"""

import sys
import socket
import time
import ctypes
import tkMessageBox

#from coaster_interface import CoasterInterface
from nl2_interface import CoasterInterface

from coaster_gui import CoasterGui
from coaster_state import RideState,RideStateStr
from serial_remote import SerialRemote
import os

import logging
log = logging.getLogger(__name__)

import platform_config as cfg

IS_RASPBERRYPI = False # this will be set True if software is running on pi
if os.name == 'posix' :
    if os.uname()[1] == 'raspberrypi':
        # for now assumes running on raspberry pi
        import local_control_itf 
        IS_RASPBERRYPI = True


from telemetry_logger import TelemetryLogger
telemetry_log = TelemetryLogger(False)

from pc_monitor import pc_monitor_client
# see pc_monitor.py for information on heartbeat server


class CoasterEvent:
    ACTIVATED, DISABLED, PAUSED, UNPAUSED, DISPATCHED, ESTOPPED, STOPPED, RESETEVENT = range(8)

CoasterEventStr = ("ACTIVATED", "DISABLED", "PAUSED", "UNPAUSED", "DISPATCHED", "ESTOPPED", "STOPPED", "RESETEVENT")

#  this state machine determines current coaster state from button and telemetry events
class State(object):

    def __init__(self, position_requestCB):
        self._state = None
        self._state = RideState.DISABLED
        self.position_requestCB = position_requestCB
        self.is_chair_active = False
        self.prev_event = None  # only used for debug

    @property
    def state(self):
        """the 'state' property."""
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    def set_is_chair_active(self, isActive):
        self.is_chair_active = isActive

    def __str__(self):
        return self.string(self._state)

    @staticmethod
    def string(state):
        # return RideStateStr[state]
        return ("Disabled", "ReadyForDispatch", "Running", "Paused",
                "EmergencyStopped", "Resetting")[state]

    def coaster_event(self, event):
        if event != self.prev_event:
            self.prev_event = event
            log.debug("> coaster event is %s,  active state is %s", CoasterEventStr[event], self.is_chair_active)
        if self.is_chair_active:
            if event == CoasterEvent.STOPPED and self._state != RideState.READY_FOR_DISPATCH:
                #  here if stopped at station
                self._state = RideState.READY_FOR_DISPATCH
                log.debug("* state changed to ready for dispatch (stopped at station)")
                self._state_change()
            elif event == CoasterEvent.DISPATCHED and self._state != RideState.RUNNING:
                log.debug("* state changed to running after dispatch")
                self._state = RideState.RUNNING
                self._state_change()
            elif event == CoasterEvent.PAUSED and self._state != RideState.PAUSED:
                self._state = RideState.PAUSED
                log.debug("* state changed to paused")
                self._state_change()
            elif event == CoasterEvent.UNPAUSED and self._state == RideState.PAUSED:
                self._state = RideState.RUNNING
                log.debug("* state changed to running after pause")
                self._state_change()
            elif event == CoasterEvent.DISABLED and self._state != EMERGENCY_STOPPED:
                log.debug("* emergency stop")
                self._state = RideState.EMERGENCY_STOPPED
                self._state_change()

        else:
            #  things to do if chair has been disabled:
            if event == CoasterEvent.RESETEVENT and self._state != RideState.RESETTING:
                #  print "resetevent, state  = ", self._state
                if self._state == RideState.DISABLED:
                    log.debug("coaster moving at startup in reset event")
                self._state = RideState.RESETTING
                #  print "got reset event"
                self._state_change()
            elif event == CoasterEvent.ESTOPPED and self._state != RideState.EMERGENCY_STOPPED:
                self._state = RideState.EMERGENCY_STOPPED
                self._state_change()
            if event == CoasterEvent.STOPPED and self._state != RideState.READY_FOR_DISPATCH:
                #  here if stopped at station
                
                log.debug("stopped at station while deactivated, state = %s", str(self))
                self._state = RideState.READY_FOR_DISPATCH
                self._state_change()
                #  print "state=", self.state

    def _state_change(self):
        if self.position_requestCB is not None:
            self.position_requestCB(self._state)  # tell user interface that state has changed
            log.debug("--STATE CHANGE %s", str(self))

colors = ["green","orange","red"] # for warning level text

class InputInterface(object):
    USE_GUI = True

    def __init__(self, sleep_func):
        self.sleep_func = sleep_func
        self.cmd_func = None
        self.is_normalized = True
        self.current_pos = [0.0,0.0,0.0,0.0,0.0,0.0]
        self.is_chair_activated = False
        self.temp_is_preparing_to_run = False  # set True while unparking and checking load
        self.coaster = CoasterInterface()
        self.gui = CoasterGui(self.dispatch, self.pause, self.reset, self.set_activate_state, self.quit)
        actions = {'detected remote': self.detected_remote, 'activate': self.activate,
                   'deactivate': self.deactivate, 'pause': self.pause, 'dispatch': self.dispatch,
                   'reset': self.reset, 'emergency_stop': self.emergency_stop, 'intensity' : self.set_intensity,
                   'show_parks' : self.show_parks,'scroll_parks' : self.scroll_parks}
        self.RemoteControl = SerialRemote(actions)
        self.prev_movement_time = 0  # holds the time of last reported movement from NoLimits
        #self.isNl2Paused = False
        self.seat = 0
        self.speed = 0
        self.isLeavingStation = False  # set true on dispatch, false when no longer in station
        self.coasterState = State(self.process_state_change)
        self.rootTitle = "NL2 Coaster Ride Controller"  # the display name in tkinter
        self.heartbeat = pc_monitor_client((40,60),(75,90))
        self.prev_heartbeat = 0
        self.server_address = None # set on receipt of hearbeat from server
        if IS_RASPBERRYPI and cfg.USE_PI_SWITCHES:
            self.local_control = local_control_itf.LocalControlItf(actions)
        else:
            self.local_control = None
        self.USE_UDP_MONITOR = True

    def init_gui(self, frame):
        if self.local_control != None:
            if self.local_control.is_activated():
               while  self.local_control.is_activated():
                   tkMessageBox.showinfo("EStop must be Down",  "Flip Emergency Stop Switch down and press Ok to proceed")
        self.gui.init_gui(frame)

    def connection_msgbox(self, msg):
        result = tkMessageBox.askquestion(msg, icon='warning')
        return result != 'no'

    def command(self, cmd):
        if self.cmd_func is not None:
            log.debug("Requesting command: %s", cmd)
            self.cmd_func(cmd)

    def prepare_to_dispatch(self):
        pass

    def dispatch(self):
        log.debug("->Dispatch command")
        if self.is_chair_activated and self.coasterState.state == RideState.READY_FOR_DISPATCH:
            # print "preparing to dispatch"
            self.temp_is_preparing_to_run = True
            self.coasterState.coaster_event(CoasterEvent.DISPATCHED)
            while not self.coaster.prepare_for_dispatch():
                 self.sleep_func(1)
            self.command("ready")  # slow rise of platform
            self.command("unparkPlatform")
            self.sleep_func(.2)
            #  self.sleep_func(1)
            self.temp_is_preparing_to_run = False
            self.coaster.dispatch(0,0)
            log.debug("dispatched")
            self.prev_movement_time = time.time()  # set time that train started to move
            self.isLeavingStation = True
            while self.coaster.is_train_in_station():
                #  print "Leaving station"
                self.sleep_func(.05)
            """
            while self.coaster.train_in_station:
                self.coaster.get_station_state()
                print "sent get station state"
                print "todo - exit and handle if not ready to dispatch"
                self.service()
            """
            self.isLeavingStation = False
            #  print "left station, state is", State.string(self.coasterState.state)
            self.start_time = time.time()
            telemetry_log.start()
            
        else:
            log.warning("dispatch request ignored, state is %s", State.string(self.coasterState.state)

    def pause(self):
        # print "Pause cmd, ride state =", State.string(self.coasterState.state)
        if self.coasterState.state  == RideState.RUNNING:
            self.coaster.set_pause(True)
            self.command("parkPlatform")
        elif self.coasterState.state == RideState.PAUSED:
            self.command("unparkPlatform")
            self.coaster.set_pause(False)
        elif self.coasterState.state == RideState.READY_FOR_DISPATCH:
            self.command("swellForStairs")

    def reset(self):
        self.coaster.reset_vr()

    def set_intensity(self, intensity_msg):
        self.command(intensity_msg)

    def show_parks(self, isPressed):
        self.gui.show_parks(isPressed)

    def scroll_parks(self, msg):
        if msg == '1':
            self.gui.scroll_parks('<Down>')
        elif msg == '-1':
            self.gui.scroll_parks('<Up>')
        else:
           log.warning("in scroll_parks, got unexpected msg: %s", msg)

    def emergency_stop(self):
        log.warning("legacy emergency stop callback")
        self.deactivate()

    def set_activate_state(self, state):
        #  print "in setActivatedState", state
        if state:
            self.activate()
        else:
            self.deactivate()

    def activate(self):
        #  only activate if coaster is ready for dispatch
        #  print "in activate state= ", self.coasterState.state
        log.debug("In activate, resetting park in manual mode")
        self.coaster.reset_park(False)
        self.coaster.system_status.is_in_play_mode = False
        self.sleep_func(0.1)
        while self.coaster.system_status.is_in_play_mode == False:
            log.debug("waiting for play mode")
            self.sleep_func(0.5)
            self.service()
        log.debug("selecting seat %d", self.seat)
        self.coaster.select_seat(self.seat)
        self.coasterState.coaster_event(CoasterEvent.RESETEVENT)
        ####if self.coasterState.state == RideState.READY_FOR_DISPATCH:
        #  print "in activate "
        self.is_chair_activated = True
        self.coasterState.set_is_chair_active(True)
        self.command("enable")
        self.gui.set_activation(True)
        self.gui.process_state_change(self.coasterState.state, True)
        #  print "in activate", str(RideState.READY_FOR_DISPATCH), RideState.READY_FOR_DISPATCH
        self.RemoteControl.send(str(RideState.READY_FOR_DISPATCH))

    def deactivate(self):
        log.debug("In deactivate, state=%s", str(self.coasterState))
        if self.coasterState.state == RideState.READY_FOR_DISPATCH:
            self.RemoteControl.send(str(RideState.DISABLED))
        self.command("disable")
        self.gui.set_activation(False)
        self.is_chair_activated = False
        self.coasterState.set_is_chair_active(False)
        if self.coasterState.state == RideState.RUNNING or self.coasterState.state == RideState.PAUSED:
            if self.coasterState.state != RideState.PAUSED:
                self.pause()
            log.info('emergency stop')
            self.coasterState.coaster_event(CoasterEvent.ESTOPPED)
        else:
            self.coasterState.coaster_event(CoasterEvent.DISABLED)
        self.gui.process_state_change(self.coasterState.state, False)

    def quit(self):
        self.command("quit")

    def detected_remote(self, info):
        if "Detected Remote" in info:
            self.set_remote_status_label((info, "green"))
        elif "Looking for Remote" in info:
            self.set_remote_status_label((info, "orange"))
        else:
            self.set_remote_status_label((info, "red"))

    def set_coaster_connection_label(self, label):
        self.gui.set_coaster_connection_label(label)

    #  def chair_status_changed(self, status):
    ##    self.gui.chair_status_changed(status)

    def temperature_status_changed(self, status):
        self.gui.temperature_status_changed(status)

    def intensity_status_changed(self, status):
        self.gui.intensity_status_changed(status)

    def set_remote_status_label(self, label):
        self.gui.set_remote_status_label(label)

    def process_state_change(self, new_state):
        #  print "in process state change", new_state, self.is_chair_activated
        if new_state == RideState.READY_FOR_DISPATCH:
            if self.is_chair_activated:
                #  here at the end of a ride
                self.command("idle")  # slow drop of platform
                self.RemoteControl.send(str(RideState.READY_FOR_DISPATCH))
            else:
                self.RemoteControl.send(str(RideState.DISABLED)) # at station but deactivated
        else: 
            self.RemoteControl.send(str(new_state))

        self.gui.process_state_change(new_state, self.is_chair_activated)

    def load_park(self, isPaused, park, seat):
        log.info("load park: %s, seat %s", park, seat)
        self.seat = int(seat)
        self.coasterState.coaster_event(CoasterEvent.RESETEVENT) 
        self.gui.set_coaster_connection_label(("loading: " + park, "orange"))
        self.sleep_func(2)
        self.coaster.load_park(isPaused, park)
        while self.coaster.system_status.is_in_play_mode == False:
            self.service()
            self.gui.set_coaster_status_label(["Waiting for Coaster play mode", "orange"])
        log.debug("selecting seat %s", seat)
        self.coaster.select_seat(int(seat))
        self.coasterState.coaster_event(CoasterEvent.STOPPED)

    def fin(self):
        # client exit code goes here
        self.heartbeat.fin()

    def get_current_pos(self):
        return self.current_pos

    def begin(self, cmd_func, move_func, limits):
        log.info("Starting coaster client")
        self.cmd_func = cmd_func
        self.move_func = move_func
        #self.limits = limits
        self.heartbeat.begin()
        self.coaster.begin()
        self.gui.set_park_callback(self.load_park)
        self.coaster.reset_park(False)
        """
        while not self.check_heartbeat():
             self.sleep_func(0.5)
        print("heartbeat detected, trying to connecto to NoLimits")

        while not self.connect():
             self.sleep_func(0.5)
        """  
        # return code removed, service func now used to exit if problems 

    def check_heartbeat(self):
        addr, heartbeat_status, warning = self.heartbeat.read()
        if len(addr) > 6:
            self.prev_heartbeat = time.time()
            if self.server_address != addr:
                self.server_address = addr
                log.info("First time connection to server @ %s", self.server_address)
                self.gui.set_coaster_status_label(("Attempting to connect to No Limits", "red"))
            # print format("heartbeat {%s} {%s} {%s}" % (addr, heartbeat_status, warning))
            self.temperature_status_changed((heartbeat_status, colors[warning]))
            #self.coaster.system_status.is_pc_connected = True
            self.coaster.system_status.is_pc_connected = True
        duration = time.time() - self.prev_heartbeat
        #if duration > 1.2:
        #    print "heartbeat dur:", duration
        if duration > 3.2: # if no heartbeat after three seconds
            #self.coaster.system_status.is_pc_connected = False
            self.coaster.system_status.is_pc_connected = False
            self.temperature_status_changed(("Lost heartbeat with server", "red"))
            # print "Lost heartbeat with server"
            return False
        elif duration > 2.2: # if no heartbeat after two seconds
            self.temperature_status_changed(("Missed Heartbeat from Server", "orange"))
            self.gui.set_coaster_connection_label(("Attempting to connect to PC", "red"))
            # self.gui.set_coaster_status_label(("Lost connection with PC", "red"))
        return True

    def connect(self):
        if not self.check_heartbeat():
            #self.gui.set_coaster_status_label(["Waiting for Heartbeat, is PC connected", "red"])
            self.temperature_status_changed(("Waiting for Heartbeat, is PC connected", "red"))
            # print "no heartbeat"
            return False
        elif not self.coaster.system_status.is_nl2_connected:
            # print("in client connect, calling coaster connect")
            self.gui.set_coaster_status_label(["Waiting for Coaster status", "red"])
            if not self.coaster.connect_to_coaster(self.server_address):
                log.error("addr: %s coaster connect returned false, nl2 not connected!", self.server_address)
                self.gui.set_coaster_connection_label(("No connection to NoLimits, is it running?", "red"))
                self.sleep_func(1)
                return False
            if self.coaster.system_status.is_nl2_connected:
                self.gui.set_coaster_status_label(["Coaster connected but not activated", "orange"])
            return self.coaster.system_status.is_nl2_connected
            
        else:
            #  print "All connections ok"
            # self.coasterState.coaster_event(CoasterEvent.STOPPED)
            return True


    def check_is_stationary(self, speed):
        if speed < .5:
            if self.coaster.is_train_in_station():
                # print "in station check, leaving flag is", self.isLeavingStation, speed
                if self.isLeavingStation == False:
                   # print "in station check, state is ",  self.coasterState
                   if self.coasterState.state == RideState.RUNNING:
                       log.debug("train arrived in station")
                       telemetry_log.stop()
                       self.command("parkPlatform")
                       return True
                ##print "CAN DISPATCH"
            else:
                if self.isLeavingStation == True:
                   # print "in station check, setting leaving flag to false"  
                   self.isLeavingStation = False

            if time.time() - self.prev_movement_time > 3:
                #  print "speed", speed
                return True
        else:
            self.prev_movement_time = time.time()
            self.gui.set_coaster_status_label([format("Coaster is Running %2.1fm/s" % speed), "green"])
        return False

    def show_coaster_status(self):
        if not self.coaster.system_status.is_pc_connected:
            self.gui.set_coaster_connection_label(("Not connected to VR server", "red"))
        if not  self.coaster.system_status.is_nl2_connected:
            self.gui.set_coaster_connection_label( ("Not connected to NoLimits server", "red"))
        if not self.coaster.system_status.is_in_play_mode:
            self.gui.set_coaster_connection_label(("NoLimits is not in play mode", "red"))
        else:
           self.gui.set_coaster_connection_label(("Receiving NoLimits Telemetry", "green"))

    def log(self, data):
        if telemetry_log.is_enabled:
            t = time.time() - self.start_time
            xyzrpy = ",".join('%0.2f' % item for item in data)
            log_entry = format("%.2f,%s,%s\n" % (t, xyzrpy,self.coaster.quat))
            telemetry_log.write(log_entry)

    def log_both(self, raw_data, processed_data):
        if telemetry_log.is_enabled:
            t = time.time() - self.start_time
            xyzrpy = ",".join('%0.2f' % item for item in raw_data)
            processed = ",".join('%0.2f' % item for item in processed_data)
            log_entry = format("%.2f,%s,%s\n" % (t, xyzrpy, processed))
            telemetry_log.write(log_entry)

    def service(self):
        self.check_heartbeat()
        if self.local_control:
            self.local_control.service()
        self.RemoteControl.service()
        if self.connect():
            self.coaster.service()
            self.show_coaster_status()
            if self.temp_is_preparing_to_run:
                self.gui.set_coaster_status_label(("Preparing to dispatch", "orange"))
            else:
                self.coaster.is_train_in_station()
                bit_train_in_station = 0x800
                bit_current_train_in_station = 0x1000

                input_field = self.coaster.get_telemetry(.1)
                if input_field and len(input_field) == 2:
                    if self.coaster.system_status.is_in_play_mode:
                        self.gui.set_coaster_connection_label(("Receiving Coaster Telemetry", "green"))
                        self.speed = input_field[0]
                        if self.coaster.system_status.is_paused == False: 
                            if self.check_is_stationary(self.speed):
                                #  print "is stopped??"
                                self.coasterState.coaster_event(CoasterEvent.STOPPED)
                                #  here if coaster not moving and not paused
                                #  print "Auto Reset"
                            else:
                                if self.coasterState.state == RideState.DISABLED:
                                    # coaster is moving at startup
                                    self.coasterState.coaster_event(CoasterEvent.RESETEVENT)
                                else:                                
                                    self.coasterState.coaster_event(CoasterEvent.UNPAUSED)

                        else:
                            self.coasterState.coaster_event(CoasterEvent.PAUSED)
                        #  print isRunning, speed
                    else:
                        self.gui.set_coaster_connection_label(("Coaster not in play mode", "red"))

                    if  input_field[1] and len(input_field[1]) == 6:  # check if we have data for all 6 DOF
                            self.current_pos = input_field[1]
                    if self.is_chair_activated and self.coasterState.state != RideState.READY_FOR_DISPATCH:
                            # only send if activated and not waiting in station
                            if self.move_func is not None:
                                self.move_func(self.current_pos)
                else:
                    if self.coaster.system_status.is_nl2_connected:
                        errMsg = format("Telemetry error: %s" % self.coaster.get_telemetry_err_str())
                        #  print errMsg
                        self.gui.set_coaster_connection_label((errMsg, "red"))
                    else:
                        self.gui.set_coaster_connection_label(("No connection to NoLimits, is it running?", "red"))

