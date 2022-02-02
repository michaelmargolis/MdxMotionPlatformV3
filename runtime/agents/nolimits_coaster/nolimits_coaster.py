"""
nolimits_coaster agent module for V3 software. (was named coaster_client)
Copyright Michael Margolis, Middlesex University 2019; see LICENSE for software rights.

module coordinates chair activity with logical coaster state
This version requires NoLimits attraction license and NL ver 2.5.3.5 or later
"""

import sys
import socket
import time
import ctypes
import os
import traceback


import logging
log = logging.getLogger(__name__)


sys.path.insert(0, os.getcwd())  # for runtime root

try:
    from agents.agent_base import AgentBase, RemoteMsgProtocol
    from agents.ride_state import RideState, RideEvent, ConnectionState
    from agents.nolimits_coaster.nl2_messenger import Nl2Messenger, ConnState
    from common.dialog import ModelessDialog
    from common.kb_sleep import kb_sleep
    from platform_config import cfg
except Exception as e:
    print(e, os.getcwd())
    print(traceback.format_exc())

from agents.nolimits_coaster.telemetry_logger import TelemetryLogger
telemetry_log = TelemetryLogger(False)

#  this state machine determines current coaster state from button and telemetry events
class CoasterState(object):

    def __init__(self, position_requestCB):
        self._state = None
        self._state = RideState.DISABLED
        self.position_requestCB = position_requestCB
        self._is_platform_active = False
        self.prev_event = None  # only used for debug

    @property
    def state(self):
        """the 'state' property."""
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    def set_is_platform_active(self, isActive):
        self._is_platform_active = isActive

    def is_platform_active(self):
        return self._is_platform_active

    def __str__(self):
        return self.string(self._state)

    @staticmethod
    def string(state):
        return RideState.str(state)

    def process_ride_event(self, event):
        if event != self.prev_event:
            self.prev_event = event
            log.debug("> coaster event is %s,  active state is %s", RideEvent.str(event), self._is_platform_active)
        if self._is_platform_active:
            if event == RideEvent.AT_STATION and self._state != RideState.READY_FOR_DISPATCH:
                #  here if stopped at station
                self._state = RideState.READY_FOR_DISPATCH
                self.ridetime_end = time.time()
                log.debug("* state changed to ready for dispatch (stopped at station)")
                self._state_change()
            elif event == RideEvent.DISPATCHED and self._state != RideState.RUNNING:
                log.debug("* state changed to running after dispatch")
                self._state = RideState.RUNNING
                self._state_change()
            elif event == RideEvent.PAUSED and self._state != RideState.PAUSED:
                self._state = RideState.PAUSED
                log.debug("* state changed to paused")
                self._state_change()
            elif event == RideEvent.UNPAUSED and self._state == RideState.PAUSED:
                self._state = RideState.RUNNING
                log.debug("* state changed to running after pause")
                self._state_change()
            elif event == RideEvent.DISABLED and self._state != RideState.EMERGENCY_STOPPED:
                log.debug("* emergency stop")
                self._state = RideState.EMERGENCY_STOPPED
                self._state_change()

        else:
            #  things to do if chair has been disabled:
            if event == RideEvent.NON_SIM_MODE and self._state != RideState.NON_SIM_MODE:
                #  print "NON SIM MODE  event, state  = ", self._state
                #if self._state == RideState.DISABLED:
                #    log.debug("coaster moving at startup in reset event")
                self._state = RideState.NON_SIM_MODE
                #  print "got NON_SIM_MODE event"
                self._state_change()
            elif event == RideEvent.ESTOPPED and self._state != RideState.EMERGENCY_STOPPED:
                self._state = RideState.EMERGENCY_STOPPED
                self._state_change()
            if event == RideEvent.AT_STATION and self._state != RideState.READY_FOR_DISPATCH:
                #  here if stopped at station

                log.debug("stopped at station while deactivated, state = %s", str(self))
                self._state = RideState.READY_FOR_DISPATCH
                self._state_change()
                #  print "state=", self.state

    def _state_change(self):
        if self.position_requestCB is not None:
            self.position_requestCB(self._state)  # tell local user interface that state has changed
            log.debug("--STATE CHANGE %s", str(self))

colors = ["green", "orange", "red"] # for warning level text

class InputInterface(AgentBase):

    def __init__(self, event_addr, event_sender):
        super(InputInterface, self).__init__(event_addr, event_sender)
        self.sleep_func = kb_sleep
        self.name = "NoLimitss Coaster"
        self.cmd_func = None
        self.is_normalized = True
        self.is_chair_activated = False
        self.temp_is_preparing_to_run = False  # set True while unparking and checking load
        self.nl2 = Nl2Messenger()
        # self.gui = CoasterGui(self.dispatch_pressed, self.pause_pressed, self.reset_vr)
        self.prev_movement_time = 0  # holds the time of last reported movement from NoLimits
        self.seat = 0
        self.isLeavingStation = False  # set true on dispatch, false when no longer in station
        self.coasterState = CoasterState(self.show_state_change) # form state msgs 
        self.coaster_status_str = "Initializing!orange"
        self.sim_connection_state_str = 'waiting sim connection'
        self.ridetime_start = 0 # time ride dispatched
        self.ridetime_end = 0
        self.pausetime = 0 # time in seconds that ride is paused
        
        self.actions = {'activate': self.activate, 'deactivate': self.deactivate, 'pause': self.pause,
                   'dispatch': self.dispatch, 'reset': self.reset_vr}
        
    """
    def command(self, cmd):
        if self.cmd_func is not None:
            log.debug("Requesting command: %s", cmd)
            self.cmd_func(cmd)

    def get_ride_state(self):
        return self.coasterState.state

    def prepare_to_dispatch(self):
        pass

    def dispatch_pressed(self):
        self.command("dispatch")

    def pause_pressed(self):
        self.command("pause")
    """

    def activate(self):
        self.coasterState.set_is_platform_active(True)
        log.info("platform activated")
        self.nl2.reset_park(False)
        # self.coaster.system_status.is_in_play_mode = False
        self.wait_park_ready()
       
        #set_is_platform_active

    def deactivate(self):
        self.coasterState.set_is_platform_active(False)
        log.info("platform deactivated")

    def dispatch(self):
        log.debug("->Dispatch command")
        if self.coasterState.state == RideState.READY_FOR_DISPATCH:
            # print "preparing to dispatch"
            self.temp_is_preparing_to_run = True
            self.coasterState.process_ride_event(RideEvent.DISPATCHED)
            log.warning("auto dispatch disabled!")
            # while not self.nl2.prepare_for_dispatch():
            #     self.sleep_func(.5)
            self.temp_is_preparing_to_run = False
            self.nl2.dispatch(0, 0)
            log.debug("coaster dispatched")
            self.prev_movement_time = time.time()  # set time that train started to move
            self.isLeavingStation = True
            while self.nl2.is_train_in_station():
                self.sleep_func(.05)
            self.isLeavingStation = False
            self.ridetime_start = time.time()
            self.pausetime = 0
            telemetry_log.start()
        else:
            log.warning("dispatch request ignored, state: %s", CoasterState.string(self.coasterState.state))

    def pause(self):
        print("Pause cmd, ride state =", CoasterState.string(self.coasterState.state))
        if self.coasterState.state == RideState.RUNNING:
            self.nl2.set_pause(True)
            self.pause_start_time = time.time()
            # self.command("parkPlatform")
        elif self.coasterState.state == RideState.PAUSED:
            # self.command("unparkPlatform")
            self.nl2.set_pause(False)
            self.pausetime += time.time() - self.pause_start_time

    def get_ridetime(self):
        return self.ridetime_end - self.ridetime_start - self.pausetime

    def reset_vr(self):
        self.nl2.reset_vr()

    def set_intensity(self, intensity_msg):
        self.command(intensity_msg)

    def select_ride(self, ride_select_msg):
        try:
            header, park, seat = ride_select_msg
            id_paused = True
            self.load_park(True, park, int(seat))
        except Exception as e:
            log.error("error handling ride select msg: %s", str(e))

    '''
    def show_parks(self, isPressed):
        self.gui.show_parks(isPressed)

    def scroll_parks(self, msg):
        if msg == '1':
            self.gui.scroll_parks('<Down>')
        elif msg == '-1':
            self.gui.scroll_parks('<Up>')
        else:
            log.warning("in scroll_parks, got unexpected msg: %s", msg)
    '''
    

    def show_state_change(self, new_state):
        # self.RemoteControl.send(str(new_state))
        if new_state == RideState.READY_FOR_DISPATCH:
            if self.coasterState.is_platform_active():
                self.coaster_status_str = "Coaster is Ready for Dispatch!green3"
            else:
                self.coaster_status_str = "Coaster at Station but deactivated!orange"
        elif new_state == RideState.RUNNING:
            self.coaster_status_str = "Coaster is Running!green3"
            
        elif new_state == RideState.PAUSED:
            self.coaster_status_str = "Coaster is Paused!orange"
        elif new_state == RideState.EMERGENCY_STOPPED:
            self.coaster_status_str = "Emergency Stop!red"
        elif new_state == RideState.NON_SIM_MODE:
            self.coaster_status_str = "Coaster is resetting!blue"
        print("in process state change", new_state,  RideEvent.str(new_state), self.coasterState.is_platform_active(), self.coaster_status_str )
  
    def load_park(self, isPaused, park, seat):
        log.info("load park: %s, seat %s", park, seat)
        self.seat = int(seat)
        self.coaster_status_str = "loading: " + park + "!orange"
        self.nl2.load_park(isPaused, park)
        self.wait_park_ready()

    def wait_park_ready(self):
        log.debug("waiting for sim mode after reset")
        self.coasterState.process_ride_event(RideEvent.NON_SIM_MODE)
        while self.nl2.connection_state != ConnState.READY:
            self.service()
            self.sleep_func(1)
        log.debug("park is now ready, setting manual mode")
        self.nl2.set_manual_mode(True)
        if self.nl2.is_paused():
            log.debug("unpausing coaster")
            self.nl2.set_pause(False)
        log.debug("selecting seat %s", self.seat)
        self.nl2.select_seat(self.seat)
        self.coasterState.process_ride_event(RideEvent.AT_STATION)

        
    def fin(self):
        # exit code goes here
        pass

    def begin(self):
        log.info("Starting NoLimits coaster agent")
        # self.cmd_func = cmd_func
        self.nl2.begin()
        # self.gui.set_park_callback(self.load_park)
        self.debug_start_time = time.time()
        self.wait_park_ready() # attempt connection and return when ready

    def connect(self):
        if self.nl2.connection_state == ConnState.DISCONNECTED:
            self.coaster_status_str = "Waiting for coaster connection!red"
            if self.nl2.connect():
                self.nl2.set_manual_mode(True)
                version = self.nl2.get_nl2_version()
                # self.ui.lbl_version.setText("Nl2 Version: " + self.nl2.get_nl2_version())
                log.info("Connected to Nl2 coaster")
                return True
            else:
                log.debug("coaster connect returned false, nl2 not connected!")
                # self.gui.set_coaster_connection_label(("No connection to NoLimits, is it running on " + self.get_address(), "red"))
                self.sleep_func(.5)
                return False
        else:
            # already connected
            return True

    def log(self, data):
        if telemetry_log.is_enabled:
            t = time.time() - self.start_time
            xyzrpy = ",".join('%0.2f' % item for item in data)
            log_entry = format("%.2f, %s, %s\n" % (t, xyzrpy,self.nl2.quat))
            telemetry_log.write(log_entry)

    def log_both(self, raw_data, processed_data):
        if telemetry_log.is_enabled:
            t = time.time() - self.start_time
            xyzrpy = ",".join('%0.2f' % item for item in raw_data)
            processed = ",".join('%0.2f' % item for item in processed_data)
            log_entry = format("%.2f,%s,%s\n" % (t, xyzrpy, processed))
            telemetry_log.write(log_entry)

    def handle_command(self, command):
        log.debug("got command: %s", command)
        if 'ride_select' in command[0] and len(command) == 3:
            self.select_ride(command)
        elif command[0] in self.actions:
            self.actions[command[0]]()
        else:
            log.warning("unhandled command (%s)", command)

    def service(self):
        prev_conn_state = self.nl2.connection_state
        self.nl2.service() # update telemetry
        if self.nl2.connection_state != prev_conn_state:
            log.debug("Nl2 conn state changed from %s to %s", ConnState.text(prev_conn_state), ConnState.text(self.nl2.connection_state))
       	if self.nl2.connection_state == ConnState.DISCONNECTED:
            self.sim_connection_state_str = 'Nl2 not connected!red'
            self.connect()
        elif self.nl2.connection_state == ConnState.NOT_IN_SIM_MODE:
            self.sim_connection_state_str = "Nl2 not in sim mode!orange"
        else:
            self.sim_connection_state_str = 'Nl2 connected!green'
            telemetry = self.nl2.telemetry_msg # this was updated in call to nl2.service()
            if telemetry:
                if self.nl2.is_paused() and self.coasterState.state != RideState.PAUSED:
                    self.coasterState.process_ride_event(RideEvent.PAUSED)
                if not self.nl2.is_paused():
                    if self.coasterState.state == RideState.PAUSED:
                          self.coasterState.process_ride_event(RideEvent.UNPAUSED)
                if telemetry.speed == 0:
                    if self.nl2. is_train_in_station():
                        self.coasterState.process_ride_event(RideEvent.AT_STATION)
                if self.coasterState.state == RideState.RUNNING:
                    self.coaster_status_str = format("Coaster is Running %2.1fm/s!green3" % telemetry.speed)
                self.set_transform(self.nl2.get_transform())

        dummy_frame =  time.time()-self.debug_start_time
        event = RemoteMsgProtocol.encode(self.get_ridetime(), dummy_frame, self.coasterState.state, self.nl2.is_paused(),
                                self.get_transform(), self.coaster_status_str, self.sim_connection_state_str)
        self.event_sender.send(event.encode('utf-8'), self.event_address)

    """  
    def old_service(self):
        if self.connect():
            self.nl2.service_nl2Q()
            if self.temp_is_preparing_to_run:
               self.coaster_status_str = "Preparing to dispatch!orange"
               print("wha 1")
            else:
                self.nl2.is_train_in_station()
                bit_train_in_station = 0x800
                bit_current_train_in_station = 0x1000
                if self.nl2.system_status.is_in_play_mode:
                    speed, transform = self.nl2.get_telemetry(.1)
                    if speed:
                        print("wha 2a speed not none")
                        #  here if valid telemetry data
                        self.speed = speed
                        self.sim_connection_state_str = 'sim connected'
                        
                        code below triggers paused event if nl2 is paused
                        else 
                           stopped event if at station
                           reset event if nl2 state is resetting (or disabled ??)
                           
                           if nl2.is_paused() self._state != RideState.PAUSED:
                           
                        if self.nl2.system_status.is_paused == False:
                            if self.check_is_stationary(self.speed):
                                self.coasterState.process_ride_event(RideEvent.STOPPED)
                                #  here if coaster not moving and not paused
                                #  print "Auto Reset"
                            else:
                                if self.coasterState.state == RideState.DISABLED:
                                    # coaster is moving at startup
                                    self.coasterState.process_ride_event(RideEvent.RESETEVENT)
                                else:
                                    self.coasterState.process_ride_event(RideEvent.UNPAUSED)
                            print("wha 3 not paused")
                        else:
                            self.coasterState.process_ride_event(RideEvent.PAUSED)
                        #  print isRunning, speed
                            print("wha 4 paused")

                        if transform and len(transform) == 6:  # check if we have data for all 6 DOF
                            self.set_transform(transform)
                            print("wha 5 got transform")
                    else:
                         print("wha 5a speed none")
                else:
                    log.error("Coaster not in play mode")
                    if self.nl2.system_status.is_nl2_connected:
                        errMsg = format("Telemetry err: %s" % self.nl2.get_telemetry_err_str())
                        log.error(errMsg)
                    print("wha 6 nl2 not in play")
        else:
            log.error("No connection to NoLimits, is it running?")
            self.sim_connection_state_str = 'sim not connected'
            print("wha 7 nl2 not connected")
        dummy_frame =  time.time()-self.debug_start_time
        print("wha 8", self.sim_connection_state_str)
        event = RemoteMsgProtocol.encode(self.get_ridetime(), dummy_frame, self.coasterState.state, self.nl2.system_status.is_paused,
                                self.get_transform(), self.coaster_status_str, self.sim_connection_state_str)
        self.event_sender.send(event.encode('utf-8'), self.event_address)
    """

def man():
    parser = argparse.ArgumentParser(description='Platform Controller\nAMDX motion platform control application')
    parser.add_argument("-l", "--log",
                        dest="logLevel",
                        choices=['DEBUG', 'INFO', 'WARNING'],
                        help="Set the logging level")
    return parser


if __name__ == '__main__':
    import argparse
    from nolimits_coaster import InputInterface
    
    args = man().parse_args()
    if args.logLevel == 'DEBUG':
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(module)s: %(message)s',
                            datefmt='%H:%M:%S')
    elif args.logLevel == 'WARNING':
        logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)-8s  %(module)s: %(message)s',
                            datefmt='%H:%M:%S')                            
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s  %(module)s: %(message)s',
                            datefmt='%H:%M:%S')

    log.info("Python: %s", sys.version[0:5])
    log.debug("logging using debug mode")
    

    event_address = ('192.168.1.9', 10000) # addr udp socket will send events to
    print(event_address)
    agent  = InputInterface(event_address)
    agent.begin()
    while  True:
        agent.service()