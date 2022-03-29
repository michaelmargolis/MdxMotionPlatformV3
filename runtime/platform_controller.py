""" Platform Controller gets telemetry from a selected agent and drives the motion platform.

Copyright Michael Margolis, Middlesex University 2020-22, see LICENSE for software rights.

note actuator lengths now expressed as muscle compression in mm (prev was total muscle length)
"""
import logging
import traceback
import argparse
import sys
import os
import time
import socket
import math # for pi in echo
import numpy as np


# from main_gui import *
from PyQt5 import QtWidgets, uic, QtCore, QtGui
logging.getLogger("PyQt5").setLevel(logging.WARNING) # suppress debug logs

from agents.agent_select_dialog import AgentSelect
from agents.agent_config import AgentCfg
from agents.ride_state import RideState

import common.gui_utils as gutil
from common.encoders import EncoderClient
from common.streaming_moving_average import StreamingMovingAverage as MA
from common.dialog import ModelessDialog
from common.udp_tx_rx import UdpReceive
from agents.agent_mux import AgentMux

# Importlib used to load configurations for platform as selected in system_config.py
import importlib
from  system_config import platform_selection, cfg
pfm = importlib.import_module(platform_selection).PlatformConfig()

from RemoteControls.RemoteControl import RemoteControl

from kinematics.kinematicsV2 import Kinematics
from kinematics.dynamics import Dynamics

from output.muscle_output import MuscleOutput
import output.output_gui as output_gui
import output.d_to_p as d_to_p

log = logging.getLogger(__name__)

qtcreator_file  = "main_gui.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons


class Controller(QtWidgets.QMainWindow):

    def __init__(self, festo_ip):
        try:        
            self.FRAME_RATE_ms = 50
            self.prev_service = None
            if festo_ip == '':
                # use ip from config file of not overridden on cmd line
                festo_ip = cfg.Festo_IP_ADDR
            self.is_alive = True  # set False to terminate
            self.dynam = Dynamics()
            self.init_kinematics()
            self.platform = MuscleOutput(self.DtoP.distance_to_pressure, festo_ip, pfm.MAX_ACTUATOR_RANGE)

            self.init_gui()
            self.platform_status_str = None
            self.is_output_enabled = False
            self.encoder_server = None
            self.connect_encoder()

            self.dynam.begin(pfm.limits_1dof, "gains.cfg")
            log.warning("Dynamics module has washout disabled, test if this is acceptable")
            self.payload = 100  # default payload in kg
            self.set_payload(str(self.payload))
            self.intensity = 100 
            self.set_intensity(str(self.intensity))  # default intensity in percent
            self.ma = MA(10)  # moving average for processing time diagnostics
            self.init_remote_controls()
            self.init_echo()
            self.service()
            log.info("Platform controller initializations complete")
        except:
            raise
                
    def init_remote_controls(self):
        self.actions = {'detected remote': self.detected_remote, 'activate': self.activate,
                   'deactivate': self.deactivate, 'pause': self.pause, 'dispatch': self.dispatch,
                   'reset': self.reset_vr, 'emergency_stop': self.emergency_stop, 
                   'intensity' : self.set_intensity,  'payload' : self.set_payload,
                   'show_parks' : self.agent_mux.show_parks, 'scroll_parks' : self.agent_mux.scroll_parks
                }
        self.RemoteControl = RemoteControl(self.actions)
        self.local_control = None
        if os.name == 'posix':
            if os.uname()[4].startswith("arm"):
                try:
                    import RPi.GPIO as GPIO 
                    import RemoteControls.local_control_itf as local_control_itf
                    pin_defines = cfg.PI_PIN_DEFINES
                    if pin_defines != 'None':
                        self.local_control = local_control_itf.LocalControlItf(self.RemoteControl.actions, pin_defines, pfm.INTENSITY_RANGE, pfm.LOAD_RANGE)
                        log.info("using local hardware switch control %s", pin_defines)
                        if self.local_control.is_activated():
                            self.dialog.setWindowTitle('Emergency Stop must be down')
                            self.dialog.txt_info.setText("Flip Emergency Stop Switch down to proceed")
                            self.dialog.show()
                            gutil.sleep_qt(5)
                            self.dialog.close()
                            while self.local_control.is_activated():
                                gutil.sleep_qt(.5)
                except ImportError:
                    qm = QtWidgets.QMessageBox
                    result = qm.question(self, 'Raspberry Pi GPIO problem', "Unable to access GPIO hardware control\nDo you want to to continue?", qm.Yes | qm.No)
                    if result != qm.Yes:
                        raise
                    else:
                        log.warning("local hardware switch control will not be used")

    def xform_diags(self, xform): 
        # for debug, shows the muscle distances for the given xform before and after gain adjustment
        unprocessed = self.k.actuator_lengths(np.array(xform))
        processed_xform = self.process_request(xform)
        processed  = self.k.actuator_lengths(np.array(processed_xform))
        print("xform:", xform, "Processed distances= ", processed, "unprocessed distances=", unprocessed)

    def init_kinematics(self):
        self.k = Kinematics()
        pfm.calculate_coords()
        log.info("Starting %s as %s", pfm.PLATFORM_NAME, pfm.PLATFORM_TYPE)
        self.k.set_geometry(pfm.BASE_POS, pfm.PLATFORM_POS)

        if pfm.PLATFORM_TYPE == "SLIDER":
            self.k.set_slider_params(pfm.joint_min_offset, pfm.joint_max_offset, pfm.strut_length,
                                     pfm.slider_angles)
            d_to_p_file = 'output/DtoP.csv'
        else:
            self.k.set_platform_params(pfm.MIN_ACTUATOR_LEN, pfm.MAX_ACTUATOR_LEN, pfm.FIXED_LEN)
            d_to_p_file = 'output/DtoP_v3.csv'
        self.actuator_distances = pfm.DISABLED_DISTANCES 

        assert pfm.MAX_ACTUATOR_RANGE == 200 # d to p files assume max range is 200
        log.info("Actuator range=%d mm", pfm.MAX_ACTUATOR_RANGE)
        self.DtoP = d_to_p.D_to_P(pfm.MAX_ACTUATOR_RANGE) # argument is max distance
        if self.DtoP.load(d_to_p_file):
            assert self.DtoP.d_to_p_up.shape[1] == self.DtoP.d_to_p_down.shape[1]
            log.info("Loaded %d rows of distance to pressure files ", self.DtoP.rows)
        else:
            log.error("Failed to loaded %s file", d_to_p_file)

    def init_gui(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QtGui.QIcon('platform_icon.png'))
        self.ui.tabWidget.currentChanged.connect(self.tab_changed)
        self.ui_tab = 0       
        self.select_agent()
        self.create_activation_toggle()
        try:     
   
            self.dynam.init_gui(self.ui.tab_2)
            self.ui.dynam_layout.addWidget(self.dynam.ui)
            self.output_gui = output_gui.OutputGui()
            self.output_gui.init_gui(self.ui.tab_3, pfm.MIN_ACTUATOR_LEN, pfm.MAX_ACTUATOR_RANGE)
            self.ui.output_layout.addWidget(self.output_gui.ui)  
            self.ui.lbl_platform.setText("Platform: " + pfm.PLATFORM_NAME)
            self.ui.btn_exit.clicked.connect(self.quit)
            # self.ui.chk_festo_wait.stateChanged.connect(self.festo_check) 
            self.chk_activate.clicked.connect(self.activation_clicked) 
            self.output_gui.encoder_change_callback(self.encoder_select_event)
            self.output_gui.encoder_reset_callback(self.encoder_reset)
            self.dialog = ModelessDialog(self)
            return True
        except Exception as e:
            log.error("error in init gui %s, %s", e, traceback.format_exc())
        return False

    def create_activation_toggle(self):
        self.chk_activate = gutil.ToggleSwitch(self.ui.frame_activate, "Activated", "Deactivated")
        self.chk_activate.setGeometry(QtCore.QRect(0, 0, 240, 38))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.chk_activate.setFont(font)
        self.chk_activate.setChecked(False)    

    def init_vr_reset(self, agent_addresses):
        self.ui.cmb_reset_vr.addItem("Reset all Vr headsets")
        model =  self.ui.cmb_reset_vr.model()
        colors = ('red', 'blue', 'green', 'cyan', 'magenta', 'yellow')
        for row in range(len(agent_addresses)):
            item = QtGui.QStandardItem("Reset @ " + agent_addresses[row])
            item.setForeground(QtGui.QColor(colors[row]))
            model.appendRow(item)
        self.ui.cmb_reset_vr.currentIndexChanged.connect(self.vr_reset_selection_changed)
        
    def vr_reset_selection_changed(self, index):
        colors = ('black', 'red', 'blue', 'green', 'cyan', 'magenta', 'yellow')
        self.ui.cmb_reset_vr.setStyleSheet("QComboBox:editable{{ color: {} }}".format(colors[index]))
    
    def select_agent(self):
        agent_cfg = AgentCfg()
        if len(cfg.SIM_IP_ADDR) > 6:
            log.error("More than SIX PCs were entered in system_config.py, fix this and restart")
            sys.exit() 
        dialog =  AgentSelect(self, cfg.SIM_IP_ADDR)
        if dialog.exec_(): 
            self.start_agent(dialog.agent_name, dialog.agent_module, dialog.agent_gui, dialog.selected_pc_addresses())
            self.ui.lbl_client.setText("Agent: " + dialog.agent_name)
            self.init_vr_reset(dialog.selected_pc_addresses())   
        else:
            sys.exit() 

    def start_agent(self, agent_name, agent_module, agent_gui, addresses ):  
        for addr in addresses:
            addr = (addr, cfg.STARTUP_SERVER_PORT) # append port to addresses

        self.agent_mux = AgentMux(addresses, cfg.STARTUP_SERVER_PORT, cfg.AGENT_MUX_EVENT_PORT)    
        while self.agent_mux.connect() == False:
             app.processEvents()
        self.agent_mux.init_gui(agent_gui, self.ui.input_layout,  self.ui.tab_1) # was frm_input)
        self.agent_mux.send_startup(agent_name, agent_module)

    def set_activation_buttons(self, isEnabled): 
        self.chk_activate.setChecked(isEnabled)

    def festo_check(self, state):
        # fixme this code is not used in this version
        if state == QtCore.Qt.Checked:
            log.info("System will wait for Festo msg confirmations")
            self.platform.set_wait_ack(True)
        else:
            log.info("System will ignore Festo msg confirmations")
            self.platform.set_wait_ack(False)

    def encoder_select_event(self, btn):
        if btn.text() == 'Encoders' and btn.isChecked():
            self.connect_encoder()
        elif btn.text() == 'Manual' and btn.isChecked():
           log.warning("Manual encoder mode not yet implimented")

    def encoder_reset(self):
        if self.encoder_server:
            self.encoder_server.reset()

    def connect_encoder(self):
        if pfm.PLATFORM_TYPE == "SLIDER":
            # encoders connected to pc running sim, see system_config for addr
            if self.encoder_server == None:
                self.encoder_server = EncoderClient(cfg.ENCODER_IP_ADDR, cfg.ENCODER_SERVER_PORT)
            try:
                addr_str = format("%s:%d" % (cfg.SIM_IP_ADDR[0], cfg.ENCODER_SERVER_PORT))
                if self.encoder_server.connect():
                    log.info("Encoders on %s", addr_str)
                else:
                    # self.ui.tabWidget.setCurrentIndex(2)
                    log.warning("FIXME message box warning that encoders not connected has been bypassed")
                    """
                    QtWidgets.QMessageBox.warning(self, 'Encoder Connection Error!',
                        "Unable to connect to encoders on " + addr_str + 
                        "\nSelect Encoders in GUI to try again", QtWidgets.QMessageBox.Ok)
                    """
                    self.output_gui.encoders_set_enabled(False)
                    self.encoder_server = None
            except Exception as e:
                log.error("Error connecting to encoders %s", e)

    def init_echo(self):
        self.echo_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.echo_addr = (cfg.ECHO_IP_ADDR, cfg.PLATFORM_ECHO_PORT)
        log.info("Echo will send UDP msgs to %s:%d",  self.echo_addr[0], self.echo_addr[1] )

    def echo_output(self, transform, distances, percents,):
        if self.echo_sock:
            # print( transform, percents, distances)
            t = [""]*6
            for idx, val in enumerate(transform):
                if idx < 3:
                    t[idx] = str(round(val))
                else:
                    t[idx] = str(round(val*180/math.pi, 1))
                    
            req_str = "request," + ','.join(t)
            
            dist_str = ",distances," +  ",".join(str(int(d)) for d in distances)
            percent_str = ",percent," +  ",".join(str(int(p)) for p in percents)
            msg = req_str + dist_str + percent_str + "\n"
            self.echo_sock.sendto(bytes(msg, "utf-8"), self.echo_addr)
            # print(self.echo_addr, msg)

    def tab_changed(self, tab_index):
        self.ui_tab = tab_index

    def pause(self):
        if self.agent_mux.get_ride_state() == RideState.RUNNING or self.agent_mux.get_ride_state() == RideState.PAUSED:
            self.agent_mux.pause_pressed()
        else:
            self.swell_for_access()

    def dispatch(self):
        if self.is_output_enabled:
            self.agent_mux.dispatch_pressed()
            """
            log.debug('preparing to dispatch')
            self.move_to_ready()
            self.park_platform(False)
            self.agent_mux.dispatch()
            """
        else:
            log.warning("Unable to dispatch because platform not enabled")

    def reset_vr(self):
       log.info("request to reset vr")
       self.agent_mux.reset_vr()

    def emergency_stop(self):
       print("estop here")

    def activation_clicked(self):
        if self.sender().isChecked():
            self.enable_platform()
        else:
            self.disable_platform()

    def activate(self):
        """remote controls call this method"""
        self.enable_platform()

    def deactivate(self):
        """remote controls call this method"""
        self.agent_mux.deactivate()

    def enable_platform(self):
        self.park_platform(False)
        xform = self.process_request(self.agent_mux.get_transform())
        actuator_distances = self.k.actuator_lengths(xform)
        self.slow_move(pfm.DISABLED_DISTANCES, actuator_distances, pfm.DISABLED_XFORM, xform, 100)
        ###self.platform.set_enable(True, pfm.DISABLED_DISTANCES, self.actuator_distances)
        # todo check sensor distance reading here to auto calibrate load ???
        if not self.is_output_enabled:
            self.is_output_enabled = True
            log.debug("Platform Enabled")
        self.set_activation_buttons(True)
        self.agent_mux.activate()

    def disable_platform(self):
        if self.is_output_enabled:
            self.is_output_enabled = False
            log.debug("Platform Disabled")
        self.set_activation_buttons(False)
        self.agent_mux.deactivate()
        xform = self.process_request(self.agent_mux.get_transform())
        actuator_distances = self.k.actuator_lengths(xform)
        self.slow_move(actuator_distances, pfm.DISABLED_DISTANCES, xform, pfm.DISABLED_XFORM,100)
        self.park_platform(True)
        self.agent_mux.parked()
        ### self.platform.set_enable(False,  self.actuator_distances, pfm.DISABLED_DISTANCES)


    def detected_remote(self, info):
        if "Detected Remote" in info:
            self.agent_mux.gui.set_rc_label((info, "green"))
        elif "Looking for Remote" in info:
            self.agent_mux.gui.set_rc_label((info, "orange"))
        else:
            self.agent_mux.gui.set_rc_label((info, "red"))
         
    def slow_move(self, begin_dist, end_dist, begin_xform, end_xform, rate_mm_per_sec):
        # moves from the given begin to end distances at the given duration
        #  caution, this moves even if disabled
        interval = .05  # ms between steps
        distance = max([abs(j-i) for i,j in zip(begin_dist, end_dist)])
        dur = abs(distance) / rate_mm_per_sec
        steps = int(dur / interval)
        xform_steps = [(j-i)/steps for i,j in zip(begin_xform, end_xform)]
        if steps < 1:
            self.platform.move_distance(end_dist)
        else:
            current_dist = begin_dist
            current_xform = begin_xform
            # print("moving from", begin_dist, "to", end_dist, "steps", steps)
            # print("xform from", begin_xform, "to", end_xform)
            # print "percent", (end[0]/start[0]) * 100
            delta = [float(e - s)/steps for s, e in zip(begin_dist, end_dist)]
            for step in range(steps):
                current_dist = [x + y for x, y in zip(current_dist, delta)]
                current_dist = np.clip(current_dist, 0, 6000)
                self.platform.move_distance(current_dist)
                current_xform = [ i+j for i, j in zip(current_xform, xform_steps)]
                self.echo_output(current_xform, current_dist,[0,0,0,0,0,0])
                # print("echoing", [round(x,1) for x in current_xform],  current_dist)
                gutil.sleep_qt(interval)
                
    def swell_for_access(self):
        if pfm.HAS_PISTON and not self.is_output_enabled:
            #Briefly raises platform high enough to insert access stairs and activate piston
            log.debug("Start swelling for access")
            self.slow_move(pfm.DISABLED_DISTANCES, pfm.PROPPING_DISTANCES,  pfm.DISABLED_XFORM, pfm.PROPPING_XFORM, 100)
            gutil.sleep_qt(3) # time in seconds in up pos
            self.slow_move(pfm.PROPPING_DISTANCES, pfm.DISABLED_DISTANCES,  pfm.PROPPING_XFORM, pfm.DISABLED_XFORM, 100)
            log.debug("Finished swelling for access")
   
        
    def park_platform(self, do_park):
        if do_park:
            if pfm.HAS_PISTON:
                self.platform.set_pistion_flag(False)
                log.debug("Setting flag to activate piston to 0")
                log.debug("TODO check if festo msg sent before delay")
                gutil.sleep_qt(0.5)
            if pfm.HAS_BRAKE:
               self.platform.set_brake(True)
            self.ui.lbl_parked.setText("Parked")
        else:  #  unpark
            if pfm.HAS_PISTON:
                self.platform.set_pistion_flag(True)
                log.debug("setting flag to activate piston to 1")
            if pfm.HAS_BRAKE:
                self.platform.set_brake(False)
            self.ui.lbl_parked.setText("")
        log.debug("Platform park state changed to %s", "parked" if do_park else "unparked")

    def set_intensity(self, intensity):
        # argument is either string as: "intensity=n"  or just 'n' where n ranges is '50'-'150'
        # if called while waiting-for-dispatch and if encoders are not enabled, scales and sets d to P index:
        # otherwise sets value in dynamics module to scale output values
        # payload weight passed to platform for deprecated method only used in old platform code
        
        if type(intensity) == str and "intensity=" in intensity:
            header, intensity = intensity.split('=', 2)
        self.intensity = int(intensity) 

        if True: # self.output_gui.encoders_is_enabled() or self.agent_mux.get_ride_state() != RideState.READY_FOR_DISPATCH :
            self.dynam.set_intensity(self.intensity)
            self.show_intensity_payload()

    def set_payload(self, payload):
        # sets parms in the output module to adjust for muscle non-linearity under load
        # slider platform uses this value to set the distance to pressure index
        # chair uses value to adjust mm to pressure coeficient
        # argument is either string as: "payload=n"  or just 'n' where n ranges is from platform cfg file
        
        if "payload=" in payload:
            header, payload = payload.split('=', 2)
        self.payload = float(payload)

        print("todo, set payload for", payload)
        lower_payload_weight = int(pfm.LOAD_RANGE[0])
        upper_payload_weight = int(pfm.LOAD_RANGE[1])
        scaled_payload = self.scale((self.payload), (0, 10), (lower_payload_weight, upper_payload_weight))
        self.platform.set_payload(payload) #  fixme not implimented (also change 0-10 to another range??)
        self.show_intensity_payload()      
      
        """ fix and move this  
            if self.agent_mux.get_ride_state() == RideState.READY_FOR_DISPATCH:
                index = intensity * self.DtoP.rows
                self.d_to_p.up_curve_idx = [index]*6
                self.d_to_p.down_curve_idx = [index]*6
                status = format("Intensity = %d, index = %.1f" % (intensity*10, index))
        """
                
    def show_intensity_payload(self):
        status = format("%d percent Intensity, (payload %d kg)" % (self.dynam.get_intensity() * 100, self.payload))
        self.agent_mux.gui.intensity_status_changed((status, "green"))   
    
    def calibrate_load(self):
        # find closest curves for each muscle at the current load
        log.warning("todo - set pressures for lookup in config files")
        up_pressure = 3000
        down_pressure = 2000
        dur = 2

        self.platform.slow_pressure_move(0, up_pressure, dur)
        gutil.sleep_qt(.5)
        encoder_data, timestamp = self.encoder_server.read()
        #  encoder_data = np.array([123, 125, 127, 129, 133, 136]) hard coded data only for testing 
        self.DtoP.set_index(up_pressure, encoder_data, 'up')

        self.platform.slow_pressure_move(up_pressure, down_pressure, dur/2)
        gutil.sleep_qt(.5)
        encoder_data, timestamp = self.encoder_server.read()
        #  encoder_data = np.array([98, 100, 102, 104, 98, 106]) 
        self.DtoP.set_index(down_pressure, encoder_data, 'down')

    def scale(self, val, src, dst): # the Arduino 'map' function written in python
        return (val - src[0]) * (dst[1] - dst[0]) / (src[1] - src[0])  + dst[0]

    def process_request(self, transform):
        """ converts request to real world values if normalized"""
        if self.agent_mux.is_normalized:
            transform = self.dynam.regulate(transform)
        return transform

    def orient_transform(self, transform):
        """ adjusts transform for rotation of top as defined in system_config"""
        transform = [inv * axis for inv, axis in zip(pfm.INVERT_AXIS, transform)]
        if pfm.SWAP_ROLL_PITCH:
            # swap roll, pitch and x,y
            transform[0],transform[1], transform[3],transform[4] =  transform[1],transform[0],transform[4], transform[3]
        return transform

    def do_transform(self, transform): 
        """ method to move platform to position corresponding to agent transform"""
        if self.is_output_enabled:
            try:
                start = time.perf_counter()
                transform = self.orient_transform(transform)
                processed_xform = self.process_request(transform)
                self.actuator_distances = self.k.actuator_lengths(np.array(processed_xform))
                self.platform.move_distance(self.actuator_distances)
                processing_dur = int(round((time.perf_counter() - start) * 1000))
                self.echo_output(list(processed_xform), self.actuator_distances, self.platform.percents)
                if processing_dur > 15: # anything less than 20 is acceptable but should remain under 15 on raspberry pi
                    log.warning("Longer than expected transform processing duration: %d ms", processing_dur)
                self.ui.lbl_processing_dur.setText(format("%d ms" % (processing_dur)))
                if self.ui_tab == 2: # the output tab
                    # processing_dur = self.ma.next(processing_dur)
                    processing_percent = round((100 * processing_dur) / self.FRAME_RATE_ms)
                    self.output_gui.show_muscles(processed_xform, self.actuator_distances, processing_percent)
                    if self.encoder_server:
                        encoder_data = self.encoder_server.read()
                        if encoder_data:
                            self.output_gui.show_encoders(encoder_data)
                self.prev_start = start
            except Exception as e:
                log.error("error in move function %s", e)
                print(traceback.format_exc()) 

    def service(self):
        if self.is_alive:
            now = time.time()
            if self.prev_service != None:
                try:
                    t =  (now - self.prev_service) * 1000
                    delta = t-self.FRAME_RATE_ms
                    if delta > -1:
                        self.prev_service = now
                        #  self.f.write(format("%f, %f\n" % (t, delta)))
                        self.RemoteControl.service()
                        if self.local_control:
                            self.local_control.service()
                        self.agent_mux.service()
                        transform = np.asarray(self.agent_mux.get_transform())
                        self.do_transform(transform)
                        if self.platform_status_str != self.platform.get_output_status():
                            self.platform_status_str = self.platform.get_output_status()
                            # gutil.set_text(self.ui.lbl_festo_status, self.platform_status_str[0], self.platform_status_str[1])
                        if self.dynam.get_intensity() != int(self.intensity * 100):
                            self.intensity = int(self.dynam.get_intensity() * 100)
                            self.show_intensity_payload()
                except Exception as e:
                    log.warning("timing test exception %s", e)
                    print(traceback.format_exc())
            else:
                self.prev_service = time.time()
                # self.f = open("timer_test.csv", "w")
                # log.warning("starting service timing latency capture to file: timer_test.csv")
            QtCore.QTimer.singleShot(1, self.service)
        else:
            self.agent_mux.fin()
            # self.platform.fin()
            sys.exit()

    def quit(self):
        qm = QtWidgets.QMessageBox
        result = qm.question(self, 'Exit?', "Are You Sure you want to quit?", qm.Yes | qm.No)
        if result != qm.Yes:
            return
        self.is_alive = False # this will trigger exit in the service routine


app = QtWidgets.QApplication(sys.argv)
app.setStyle('Fusion') # fusion is default on the pi ?

def man():
    parser = argparse.ArgumentParser(description='Platform Controller\nAMDX motion platform control application')
    parser.add_argument("-l", "--log",
                        dest="logLevel",
                        choices=['DEBUG', 'INFO', 'WARNING'],
                        help="Set the logging level")
    parser.add_argument("-f", "--festo_ip",
                        dest="festoIP",
                        help="Set IP address of Festo controller")
    return parser


def main():
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

    log.info("Python: %s, qt version %s", sys.version[0:5], QtCore.QT_VERSION_STR)
    log.info("Starting Platform Controller")
    log.debug("logging using debug mode")
    controller = None
    try:
        if args.festoIP:
            controller = Controller(args.festoIP)
        else:
            controller = Controller('')
        controller.show()
        app.exec_()

    except SystemExit:
        log.error("user abort")
    except Exception as e:
        log.error("error in main %s, %s", e, traceback.format_exc())

    if controller:
        controller.close()
    app.exit()
    sys.exit()
    log.info("Exiting Platform Controller\n")
    log.shutdown()

if __name__ == "__main__":
    main()
