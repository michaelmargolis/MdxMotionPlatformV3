"""
  remote client for V3 software
  
  This version controls one or more local clients running on remote pc
  The gui can display up to eight clients

"""

import sys
import socket
from math import radians, degrees
import threading
import time
import traceback
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from PyQt5 import QtCore, QtGui, QtWidgets

import logging
log = logging.getLogger(__name__)

from clients.client_api import ClientApi, RemoteMsgProtocol
from clients.ride_state import RideState
from clients.remote_client.remote_client_gui_defs import Ui_Frame
from common.tcp_client import TcpClient
import common.gui_utils as gutil
from platform_config import cfg


class RemoteInputInterface(ClientApi):

    def __init__(self):
        super(RemoteInputInterface, self).__init__()
        self.sleep_func = gutil.sleep_qt
        self.name = "Remote Client"
        self.is_normalized = True
        self.expect_degrees = False # convert to radians if True

        self.max_values = [80, 80, 80, 0.4, 0.4, 0.4]
        self.normalized = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.telemetry = []

        self.clients = []

        self.state = RideState.UNKNOWN # state not yet set
        self.client_state = []
        self.state_mismatch = 0  # valaue is number of frames that clients have mismatched states
        self.client_frame = []
        self.frame_mismatch = 0  # valaue is max difference in client frame numbers
        self.client_is_paused = []

        self.is_activated = False

    def init_gui(self, frame):
        self.ui = Ui_Frame()
        self.ui.setupUi(frame)
        self.frame = frame

        #control arrays
        self.lbl_coaster_connection = []  # [self.ui.lbl_coaster_connection_1, self.ui.lbl_coaster_connection_2]
        # self.lbl_coaster_status = [self.ui.lbl_coaster_status_1, self.ui.lbl_coaster_status_2]

        # self.lbl_temperature_status = [self.ui.lbl_temperature_status_1,self.ui.lbl_temperature_status_1]

        # configure signals
        self.ui.btn_dispatch.clicked.connect(self.dispatch_pressed)
        self.ui.btn_pause.clicked.connect(self.pause_pressed)
        
        # self.ui.btn_reset_rift_1.clicked.connect(self.reset1)
        # self.ui.btn_reset_rift_2.clicked.connect(self.reset2)

        # Create custom buttons
        self.custom_btn_dispatch = gutil.CustomButton( self.ui.btn_dispatch, ('white','darkgreen'), ('black', 'lightgreen'), 10, 0) 
        self.custom_btn_pause = gutil.CustomButton( self.ui.btn_pause, ('black','orange'), ('black', 'yellow'), 10, 0) 

        self.ui.cmb_select_ride.currentIndexChanged.connect(self.ride_selection_changed)
        gutil.set_text(self.ui.lbl_coaster_status, "Connecting", 'orange')
        
    def init_connection_status(self, remote_addresses):
        font = QtGui.QFont()
        font.setPointSize(12)
        for idx, ip_addr in enumerate(remote_addresses):
            if idx >= 6:
                log.warning("Connection status only shown for up to 6 addresses")
                return
            else:
               label = QtWidgets.QLabel(self.ui.frm_input)
               x = 20 + (idx % 2) * (self.ui.frm_input.width()/2)
               y = 15 + (idx / 2) * 30
               label.setGeometry(QtCore.QRect(x, y, 222, 19))
               label.setFont(font)               
               self.lbl_coaster_connection.append(label)

    def show_ride_selector(self, state):
        if state:
            self.ui.lbl_item_select.show()
            self.ui.cmb_select_ride.show()
        else:
            self.ui.lbl_item_select.hide()
            self.ui.cmb_select_ride.hide()

    def load_ride_selector(self, ride_list):
        self.ui.cmb_select_ride.addItems(ride_list)

    def ride_selection_changed(self, index):
        log.info("ride selector changed to index %d", index)

    def set_rc_label(self, info):
        gutil.set_text(self.ui.lbl_remote_status, info[0], info[1])

    def dispatch_pressed(self):
        self.command("dispatch")

    def pause_pressed(self):
        self.command("pause")

    def get_ride_state(self):
        # first client provides state and transform
        log.debug("remote client state is %s", RideState.str(self.client_state[0]))
        return self.client_state[0]

    def quit(self):
        self.command("quit")

    def pause(self):
        log.debug("pause in remote client, state is %s", RideState.str(self.state))
        if self.state == RideState.RUNNING or self.state == RideState.PAUSED:
            for client in self.clients:
                client.send('pause\n')

    def reset_vr(self):
        log.info("reset all rifts")
        for client in self.clients:
            client.send('reset\n')

    def reset1(self):
        log.info("reset rift 1")
        self.clients[0].send('reset\n')
        
    def reset2(self):
        log.info("reset rift 2")
        self.clients[1].send('reset\n')

    def command(self, cmd):
        if self.cmd_func is not None:
            log.info("Requesting command: %s", cmd)
            self.cmd_func(cmd)
    
    def dispatch(self):
        for client in self.clients:
            client.send('dispatch\n')
        log.debug("dispatched")

    def intensity_status_changed(self, intensity):
       gutil.set_text(self.ui.lbl_intensity_status, intensity[0], intensity[1])

    def activate(self):
        log.info("Remote client activated")
        self.is_activated = True
        self.show_state_change(self.state, self.is_activated)

    def deactivate(self):
        log.info("Remote client deactivated")
        self.is_activated = False
        self.show_state_change(self.state, self.is_activated)

    def begin(self, cmd_func, limits, remote_addresses):
        for ip_addr in remote_addresses:
            self.clients.append(TcpClient(ip_addr, cfg.REMOTE_CLIENT_PORT))
            self.client_state.append(RideState.UNKNOWN) # state not yet set
            self.client_frame.append(0)
            self.client_is_paused.append(False)
        self.set_address((remote_addresses, cfg.REMOTE_CLIENT_PORT))
        self.init_connection_status(remote_addresses)
        # print(self.get_address(), self.get_address()[0][0]) 
        self.cmd_func = cmd_func
        self.limits = limits  # note limits are in mm and radians
        if self.is_normalized:
            log.info('Platform Input is Remote Client with normalized parms, %d client(s) connected', len(self.clients))
        else:
            log.info('Platform Input is Remote Client with real world parms, %d client(s) connected', len(self.clients))
        for i in range(len(self.lbl_coaster_connection)):
            gutil.set_text(self.lbl_coaster_connection[i], "Connecting to " + self.clients[i].ip_addr,"orange") 
        #for i in range(len(self.clients)):
        #    gutil.set_text(self.lbl_coaster_status[i], " ","green") # not used in this version            

    def connect(self):
        """returns true if all clients are connected"""
        all_connected = True 
        try:
            for client in self.clients:
                if not client.status.is_connected:
                    if not client.connect():
                        return False
        except:
            all_connected = False
        return all_connected

    def fin(self):
        # client exit code goes here
        pass

    def show_state_change(self, new_state, isActivated):
        # print("Remote client state changed to ", str(RideState.str(new_state)), str(isActivated))
        log.debug("Remote client state changed to: %s (%s)", RideState.str(new_state), "Activated" if isActivated else "Deactivated")
        if new_state == RideState.READY_FOR_DISPATCH:
            if isActivated:
                log.debug("Ready for Dispatch")
                self.custom_btn_dispatch.set_attributes(True, False, 'Dispatch')  # enabled, not checked
                self.custom_btn_pause.set_attributes(True, False, 'Pause')  # enabled, not checked
                gutil.set_text(self.ui.lbl_coaster_status, "Coaster is Ready for Dispatch", "green")
            else:
                log.debug("At Start but deactivated")
                self.custom_btn_dispatch.set_attributes(False, False, 'Dispatch')  # not enabled, not checked
                self.custom_btn_pause.set_attributes(True, False, "Prop Platform")  # enabled, not checked
                gutil.set_text(self.ui.lbl_coaster_status, "Coaster at Station but deactivated", "orange")

        elif new_state == RideState.RUNNING:
            self.custom_btn_dispatch.set_attributes(False, True, 'Dispatched')  # not enabled, checked
            self.custom_btn_pause.set_attributes(True, False, "Pause")  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Coaster is Running", "green")
            
        elif new_state == RideState.PAUSED:
            self.custom_btn_dispatch.set_attributes(False, True)  # not enabled, checked
            self.custom_btn_pause.set_attributes(True, True, "Continue")  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Coaster is Paused", "orange")
        elif new_state == RideState.EMERGENCY_STOPPED:
            self.custom_btn_dispatch.set_attributes(False, True)  # not enabled, checked
            self.custom_btn_pause.set_attributes(False, True)  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Emergency Stop", "red")
        elif new_state == RideState.RESETTING:
            self.custom_btn_dispatch.set_attributes(False, True)  # not enabled, checked
            self.custom_btn_pause.set_attributes(False, False)  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Coaster is resetting", "blue")

    def process_client_states(self):
        alert_color = 'green'
         
        if self.client_state[1:] == self.client_state[:-1]:
            # here of all client states are the same
            self.state_mismatch = 0
            if self.state != self.client_state[0]:  # track state of first client
                log.info("state changed to %s",  RideState.str(self.client_state[0])) 
                self.show_state_change(self.client_state[0], self.is_activated)
                self.state = self.client_state[0]            
            if len(self.clients) == 1: # single client
                    gutil.set_text(self.ui.lbl_state_delta, " ", alert_color)
                    return
            gutil.set_text(self.ui.lbl_state_delta, "Client States are synced", alert_color)                    
        else:
            self.state_mismatch += 1 # count of frames with mismatched state
            log.warning("state mismatched over %d frame(s)",self.state_mismatch)
            if self.state_mismatch < 3:
                alert_color = 'orange'
                gutil.set_text(self.ui.lbl_state_delta, "Client States not synced", alert_color)
            else:
                alert_color = 'red'
                if self.state_mismatch == 3:
                    log.error("State mismatched over too many frames")
            mismatch_states = ""
            for i in range(clients):
                mismatch_states += format("PC %d: %s" % (i,self.client_state[i].str()))
                if i < len(self.clients)-1:
                    mismatch_states += "     " 
            gutil.set_text(self.ui.lbl_coaster_status, mismatch_states, alert_color)
            gutil.set_text(self.ui.lbl_frame_delta, format("Client State lost sync %d frames ago" % self.state_mismatch), alert_color)


        self.frame_mismatch = max(self.client_frame) - min(self.client_frame)
        if self.frame_mismatch > 5:
            log.warning("Excessive frame mismatch: %d", self.frame_mismatch)
            gutil.set_text(self.ui.lbl_frame_delta, format("Client frame delta: %d" % self.frame_mismatch), "orange")
        else:
            self.frame = int(sum( self.client_frame) / len( self.client_frame))
            gutil.set_text(self.ui.lbl_frame_delta, format("Frame: %d, delta: %d" % (self.frame,self.frame_mismatch)), "green")

        if self.client_is_paused[1:] == self.client_is_paused[:-1]:
            # here of all client are in same pause state
            self.is_paused = self.client_is_paused[0]
        else:
            log.error("Client pause states not matched")
            self.is_paused = None # raise error?

    def service(self):
        if self.connect():
            is_state_changed = False
            for idx, client in enumerate(self.clients):
                # print("sending telemetry request for client", idx)
                client.send('telemetry\n')
                while client.available() > 0:
                    event = client.receive()
                    # print("in service", event)
                    msg = event
                    try:
                        m = RemoteMsgProtocol()
                        m.decode(msg) 
                        if idx == 0:
                            self.set_transform(m.transform)
                        if self.client_state[idx] != m.state:
                            is_state_changed = True
                            self.client_state[idx] = m.state
                        self.client_frame[idx] = m.frame
                        self.client_is_paused[idx] = m.is_paused
                        if client.status.is_connected:
                            gutil.set_text(self.lbl_coaster_connection[idx], format("Connected to %s" % (self.clients[idx].ip_addr)), 'green')
                        else:
                            gutil.set_text(self.lbl_coaster_connection[idx], format("Not Connected to %s" % (self.clients[idx].ip_addr)), 'red')
                    except Exception as e:
                        log.error("error parsing %s: %s", msg, e)
                        print(traceback.format_exc())
            self.process_client_states()

        else:
            print("not connected")
        msg = None


######### code for remote client run from main ############

class RemoteClient(QtWidgets.QMainWindow):
    """
    on state or status change local client will pass:
        current coaster state, current connection state, coaster status string, color
    every frame client will pass:
        frame number, xyzrpy
        
    commands:
        reset, dispatch, pause 
    
    """
    def __init__(self):
        try:
            QtWidgets.QMainWindow.__init__(self)
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)
            self.client = RemoteInputInterface() 
            limits = pfm.limits_1dof
            self.client.init_gui(self.ui.frame)
            self.client.begin(self.cmd_func,  limits, ('192.168.1.16',))
            service_timer = QtCore.QTimer(self)
            service_timer.timeout.connect(self.client.service)
            log.info("Starting client service timer")
            service_timer.start(50) 
        except Exception as e:
            log.error("error starting remote client %s, %s", e, traceback.format_exc())

    def cmd_func(self, cmd):  # command handler function called from Platform input
        if cmd == "quit": 
            self.quit()

    def move_func(self, request):  # move handler to position platform as requested by Platform input
        pass
        # print("in move func", request)

    def quit(self):
        for client in self.client.clients:
            client.disconnect()
        log.info("Executing quit command")
        sys.exit()
 
if __name__ == "__main__":

    from clients.local_client_gui_defs import Ui_MainWindow
    import traceback
    import importlib  
    sys.path.insert(0, '..\..\output')  # for platform config
    sys.path.insert(0, 'output')  # for platform config
    
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%H:%M:%S')
    log.info("Starting remote client")

    # platform_selection = 'ConfigV3'
    platform_selection = 'configNextgen'
    pfm = importlib.import_module(platform_selection).PlatformConfig()

    app = QtWidgets.QApplication(sys.argv) 
    
    try:       
        remote_client = RemoteClient()
        remote_client.show()
        app.exec_()
        app.exit()
        log.info("Exiting Remote client\n")
    except Exception as e:
        log.error("in main, error starting remote client %s", e)
