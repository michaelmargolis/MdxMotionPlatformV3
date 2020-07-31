""" Platform Controller connects a selected client to motion platform.

Copyright Michael Margolis, Middlesex University 2019; see LICENSE for software rights.

note actuator lengths now expressed as muscle compression in mm (prev was total muscle length)
"""
import logging
import traceback
import argparse
import sys
import os
import time
import socket
import numpy as np


from main_gui import *
from client_select_dialog import ClientSelect
from ride_state import RideState

import common.gui_utils as gutil
from common.dynamics import Dynamics
from common.encoders import EncoderClient
from common.streaming_moving_average import StreamingMovingAverage as MA
from common.dialog import ModelessDialog
from common.tcp_client import TcpClient

# Importlib used to load configurations for client and platform as selected in platform_config.py
import importlib
from  platform_config import platform_selection, cfg
pfm = importlib.import_module(platform_selection).PlatformConfig()

from RemoteControls.RemoteControl import RemoteControl

from output.kinematicsV2 import Kinematics
from output.muscle_output import MuscleOutput
import output.output_gui as output_gui
import output.d_to_p as d_to_p

log = logging.getLogger(__name__)

class Controller(QtWidgets.QMainWindow):

    def __init__(self, festo_ip):
        try:
            self.FRAME_RATE_ms = 50
            self.prev_service = None
            if festo_ip == '':
                # use ip from config file of not overridden on cmd line
                festo_ip = cfg.Festo_IP_ADDR
            self.init_gui()
            self.init_kinematics()
            self.platform = MuscleOutput(self.DtoP.distance_to_pressure, festo_ip, pfm.MAX_ACTUATOR_RANGE)
            self.platform_status = None
            self.is_active = True  # set False to terminate
            self.is_output_enabled = False
            self.init_platform_parms()
            self.encoder_server = None
            self.connect_encoder()
            self.dynam = Dynamics()
            self.dynam.init_gui(self.ui.frm_dynamics)
            self.dynam.begin(pfm.limits_1dof, "gains.cfg")
            log.warning("Dynamics module has washout disabled, test if this is acceptable")
            self.set_intensity(10)  # default intensity at max
            self.ma = MA(10)  # moving average for processing time diagnostics
            self.init_remote_controls()
            self.init_echo()
            self.service()
            log.info("Platform controller initializations complete")
        except:
            raise
            
    def init_remote_controls(self):
        self.RemoteControl = RemoteControl(self, self.client.set_rc_label)
        self.local_control = None
        if os.name == 'posix':
            if os.uname()[1] == 'raspberrypi':
                try:
                    import RPi.GPIO as GPIO 
                    import RemoteControls.local_control_itf as local_control_itf
                    if cfg.USE_PI_SWITCHES:
                        self.local_control = local_control_itf.LocalControlItf(self.RemoteControl.actions)
                        log.info("using local hardware switch control")
                        if self.local_control.is_activated():
                            self.dialog.setWindowTitle('Emergency Stop must be down')
                            self.dialog.txt_info.setText("Flip Emergency Stop Switch down and press Ok to proceed")
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

    def init_kinematics(self):
        self.k = Kinematics()
        pfm.calculate_coords()
        log.info("Starting %s as %s", pfm.PLATFORM_NAME, pfm.PLATFORM_TYPE)
        self.k.set_geometry(pfm.BASE_POS, pfm.PLATFORM_POS)

        if pfm.PLATFORM_TYPE == "SLIDER":
            self.k.set_slider_params(pfm.joint_min_offset, pfm.joint_max_offset, pfm.strut_length,
                                     pfm.slider_angles)
            self.actuator_lengths = [0] * 6   # muscles fully relaxed
            d_to_p_file = 'output/DtoP.csv'
        else:
            self.k.set_platform_params(pfm.MIN_ACTUATOR_LEN, pfm.MAX_ACTUATOR_LEN, pfm.FIXED_LEN)
            self.actuator_lengths = [pfm.PROPPING_LEN] * 6 # position for moving prop
            d_to_p_file = 'output/DtoP_v3.csv'

        assert pfm.MAX_ACTUATOR_RANGE == 200 # d to p files assume max range is 200
        log.info("Actuator range=%d mm", pfm.MAX_ACTUATOR_RANGE)
        self.DtoP = d_to_p.D_to_P(pfm.MAX_ACTUATOR_RANGE) # argument is max distance
        if self.DtoP.load(d_to_p_file):
            assert self.DtoP.d_to_p_up.shape[1] == self.DtoP.d_to_p_down.shape[1]
            log.info("Loaded %d rows of distance to pressure files ", self.DtoP.rows)
        else:
            log.error("Failed to loaded %s file", d_to_p_file)

    def init_platform_parms(self):
        # self.platform.begin(pfm.MIN_ACTUATOR_LEN, pfm.MAX_ACTUATOR_LEN, pfm.DISABLED_LEN, pfm.PROPPING_LEN, pfm.FIXED_LEN)
        self.platform_disabled_pos = np.empty(6)   # position when platform is disabled
        self.platform_propping_pos = np.empty(6)  # position for attaching stairs
        self.platform_disabled_pos.fill(pfm.DISABLED_LEN)  # position when platform is disabled (propped)
        self.platform_propping_pos.fill(pfm.PROPPING_LEN)  # position for attaching stairs or moving prop

    def init_gui(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QtGui.QIcon('platform_icon.png'))
        self.ui.tabWidget.currentChanged.connect(self.tab_changed)
        self.ui_tab = 0
        self.select_client()
        try:
            self.client.init_gui(self.ui.frm_input)
            self.output_gui = output_gui.OutputGui()
            self.output_gui.init_gui(self.ui.frm_output, pfm.MIN_ACTUATOR_LEN, pfm.MAX_ACTUATOR_RANGE)
            self.ui.lbl_platform.setText("Platform: " + pfm.PLATFORM_NAME)
            self.ui.lbl_client.setText("Client: " + self.client.name)
            self.ui.btn_exit.clicked.connect(self.quit)
            self.ui.chk_festo_wait.stateChanged.connect(self.festo_check) 
            self.ui.btn_activate.clicked.connect(self.enable_platform)
            self.ui.btn_deactivate.clicked.connect(self.disable_platform)
            self.output_gui.encoder_change_callback(self.encoder_select_event)
            self.output_gui.encoder_reset_callback(self.encoder_reset)

            self.dialog = ModelessDialog(self)
            return True
        except Exception as e:
            log.error("error in init gui %s, %s", e, traceback.format_exc())
        return False

    def select_client(self):
        dialog =  ClientSelect(self, cfg.SIM_IP_ADDR)
        if dialog.exec_():
            startup_msg = format("STARTUP,%s,%s" % (dialog.client_name, dialog.local_client_itf))
            self.start_remote_pcs(dialog.pc_addresses, startup_msg)
            self.client = importlib.import_module(dialog.remote_client).InputInterface()
            self.client.begin(self.cmd_func, pfm.limits_1dof, dialog.pc_addresses)
        else:
            sys.exit() 

    def start_remote_pcs(self, addresses, startup_msg):
        for addr in addresses:
            log.info("remote startup to %s: %s", addr, startup_msg)
            client = TcpClient(addr, cfg.STARTUP_SERVER_PORT)
            while not client.status.is_connected:
                if client.connect():
                    log.info("Connected to PC at %s", addr)
                    if addr == addresses[0]:
                        log.info("Requesting encoder startup on %s", addr)
                        client.send("STARTUP,NONE,common/encoders\n")
                    log.info("sending startup msg: %s", startup_msg)
                    client.send(startup_msg + '\n') 
                else:
                    app.processEvents()
                    print "not connected"


    def set_activation_buttons(self, isEnabled): 
        if isEnabled:
            gutil.set_button_style(self.ui.btn_activate, True, True, "Activated", checked_color='green')  # enabled, checked
            gutil.set_button_style(self.ui.btn_deactivate, True, False, "Deactivate")  # enabled, checked
        else:
            gutil.set_button_style(self.ui.btn_activate, True, False, "Activate")  # enabled, not checked
            gutil.set_button_style(self.ui.btn_deactivate, True, True, "Deactivated")  # enabled, checked

    def festo_check(self, state):
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
           print("todo change to manual mode")

    def encoder_reset(self):
        if self.encoder_server:
            self.encoder_server.reset()

    def connect_encoder(self):
        if pfm.PLATFORM_TYPE == "SLIDER":
            # encoders connected to pc running sim, see platform_config for addr
            if self.encoder_server == None:
                self.encoder_server = EncoderClient(cfg.ENCODER_IP_ADDR, cfg.ENCODER_SERVER_PORT)
            try:
                addr_str = format("%s:%d" % (cfg.SIM_IP_ADDR[0], cfg.ENCODER_SERVER_PORT))
                if self.encoder_server.connect():
                    log.info("Encoders on %s", addr_str)
                else:
                    self.ui.tabWidget.setCurrentIndex(2)
                    QtWidgets.QMessageBox.warning(self, 'Encoder Connection Error!',
                        "Unable to connect to encoders on " + addr_str + 
                        "\nSelect Encoders in GUI to try again", QtWidgets.QMessageBox.Ok)
                    self.output_gui.encoders_set_enabled(False)
                    self.encoder_server = None
            except Exception as e:
                log.error("Error connecting to encoders %s", e)

    def init_echo(self):
        # todo - replace this with tcp_server ??? 
        self.echo_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.echo_addr = (cfg.ECHO_IP_ADDR, cfg.PLATFORM_ECHO_PORT)
        log.info("Echo will send UDP msgs to %s:%d",  self.echo_addr[0], self.echo_addr[1] )

    def echo_output(self, transform, distances, percents,):
       if self.echo_sock:
            #print transform, percents, distances
            trans_str = ",".join("{0:0.3f}".format(f) for f in transform)
            dist_str = ",".join("{0}".format(i) for i in distances)
            percent_str = ",".join("{0}".format(i) for i in percents)
            msg = format("transform=%s;distances=%s;percents=%s;\n" % (trans_str, dist_str, percent_str))
            self.echo_sock.sendto(msg.encode("utf-8"), self.echo_addr)

    def tab_changed(self, tab_index):
        self.ui_tab = tab_index

    def pause(self):
        if self.client.get_ride_state() == RideState.RUNNING or self.client.get_ride_state() == RideState.PAUSED:
            self.client.pause()
        else:
            self.swell_for_access()

    def dispatch(self):
        if self.is_output_enabled:
            log.debug('preparing to dispatch')
            self.move_to_ready()
            self.park_platform(False)
            self.client.dispatch()
        else:
            log.warning("Unable to dispatch because platform not enabled")

    def reset_vr(self):
       log.info("request to reset vr")
       self.client.reset_vr()

    def emergency_stop(self):
       print("estop here")

    def cmd_func(self, cmd):  # command handler function called from client
        log.debug("controller received cmd function: %s", cmd)
        if cmd == "exit": self.is_active = False
        elif cmd == "dispatch": self.dispatch()
        elif cmd == "pause": self.pause()
        elif cmd == "enable": self.enable_platform()
        elif cmd == "disable": self.disable_platform()
        elif cmd == "idle": self.move_to_idle()
        elif cmd == "ready": self.move_to_ready()
        elif cmd == "swellForStairs": self.swell_for_access()
        elif cmd == "parkPlatform": self.park_platform(True)
        elif cmd == "unparkPlatform": self.park_platform(False)
        elif cmd == "quit": self.quit()
        elif 'intensity' in cmd:
            m, intensity = cmd.split('=', 2)
            self.set_intensity(int(intensity))

    def activate(self):
        """remote controls call this method"""
        self.enable_platform()

    def deactivate(self):
        """remote controls call this method"""
        self.disable_platform()
        
    def enable_platform(self):
        # request = self.process_request(self.client.get_transform())
        # actuator_lengths = self.k.actuator_lengths(request)
        # self.platform.set_enable(True, self.actuator_lengths)
        if not self.is_output_enabled:
            self.is_output_enabled = True
            log.debug("Platform Enabled")
        self.set_activation_buttons(True)
        self.client.activate()

    def disable_platform(self):
        request = self.process_request(self.client.get_transform())
        actuator_lengths = self.k.actuator_lengths(request)
        # self.platform.set_enable(False, self.actuator_lengths)
        if self.is_output_enabled:
            self.is_output_enabled = False
            self.platform.set_pistion_flag(False)
            log.debug("in disable, lengths=%s", ','.join('%d' % l for l in actuator_lengths))
            self.platform.slow_move(actuator_lengths, self.platform_disabled_pos, 1000)
        self.set_activation_buttons(False)
        self.client.deactivate()

    def move_to_idle(self):
        log.debug("move to idle")
        # request = self.process_request(self.client.get_transform())
        # actuator_lengths  = self.k.actuator_lengths(request)
        actuator_lengths = self.platform.prev_distances
        ##pos = self.client.get_transform() # was used to get z pos (pos[2])
        self.park_platform(True)  # backstop to prop when coaster state goes idle
        self.platform.slow_move(actuator_lengths, self.platform_disabled_pos, 10) # rate is cm per sec

    def move_to_ready(self):
        #  request = self.process_request(self.client.get_transform())
        #  actuator_lengths  = self.k.actuator_lengths(request)
        ##pos = self.client.get_transform() # was used to get z pos
        log.debug("move to ready")
        if pfm.PLATFORM_TYPE == "SLIDER":
            if self.output_gui.encoders_is_enabled():
                self.run_lookup()

    def swell_for_access(self):
        if pfm.PROPPING_LEN > 0:
            #Briefly raises platform high enough to insert access stairs and activate piston
            log.debug("Start swelling for access")
            self.platform.slow_move(self.platform_disabled_pos, self.platform_propping_pos, 10)
            gutil.sleep_qt(3) # time in seconds in up pos
            self.platform.slow_move(self.platform_propping_pos, self.platform_disabled_pos, 10)
            log.debug("Finished swelling for access")

    def park_platform(self, do_park):
        if do_park:
            if pfm.HAS_PISTON:
                self.platform.set_pistion_flag(False)
                log.debug("Setting flag to activate piston to 0")
                log.debug("TODO check if festo msg sent before delay")
                gutil.sleep_qt(0.5)
            if pfm.HAS_BRAKE:
                print("todo, set brake")
        else:  #  unpark
            if pfm.HAS_PISTON:
                self.platform.set_pistion_flag(True)
                log.debug("setting flag to activate piston to 1")
            if pfm.HAS_BRAKE:
                print("todo, release brake")
        log.debug("Platform park state changed to %s", "parked" if do_park else "unparked")

    def set_intensity(self, intensity):
        # argument is either string as: "intensity=n"  where n is 0-10 or an int 0-10
        # if called while waiting-for-dispatch and if encoders are not enabled, scales and sets d to P index:
        # otherwise sets value in dynamics module to scale output values
        # payload weight passed to platform for deprecated method only used in old platform code
        
        if type(intensity) == str and "intensity=" in intensity:
            m, intensity = intensity.split('=', 2)
        intensity = float(intensity) * 0.1
        lower_payload_weight = int(pfm.LOAD_RANGE[0])
        upper_payload_weight = int(pfm.LOAD_RANGE[1])
        payload = self.scale((intensity), (0, 10), (lower_payload_weight, upper_payload_weight))
        self.platform.set_payload(payload)
        if self.output_gui.encoders_is_enabled() or self.client.get_ride_state() != RideState.READY_FOR_DISPATCH :
            self.dynam.set_intensity(intensity)
            status = format("%d percent Intensity, (Weight %d kg)" % (self.dynam.get_overall_intensity() * 100, payload))
        else:
            if self.client.get_ride_state() == RideState.READY_FOR_DISPATCH:
                index = intensity * self.DtoP.rows
                self.d_to_p.up_curve_idx = [index]*6
                self.d_to_p.down_curve_idx = [index]*6
                status = format("Intensity = %d, index = %.1f" % (intensity*10, index))
        self.client.intensity_status_changed((status, "green"))

    def run_lookup(self):
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
        if self.client.is_normalized:
            transform = self.dynam.regulate(transform)
        return transform

    def do_transform(self, transform): 
        """ method to move platform to position corresponding to client transform"""
        try:
            start = time.time()
            processed_xform = self.process_request(transform)
            self.actuator_lengths = self.k.actuator_lengths(np.array(processed_xform))
            self.platform.move_distance(self.actuator_lengths)
            processing_dur = int(round((time.time() - start) * 1000))
            self.echo_output(list(processed_xform), self.actuator_lengths, self.platform.percents)
            if processing_dur > 9: # anything less than 20 is acceptable but should average under 9 on raspberry pi
                log.warning("Longer than expected transform processing duration: %d ms", processing_dur)
            if self.ui_tab == 2: # the output tab
                processing_dur = self.ma.next(processing_dur)
                self.output_gui.show_muscles(processed_xform, self.actuator_lengths, processing_dur)
                if self.encoder_server:
                    encoder_data = self.encoder_server.read()
                    if encoder_data:
                        self.output_gui.show_encoders(encoder_data)
            self.prev_start = start
        except Exception as e:
            log.error("error in move function %s", e)
            print(traceback.format_exc()) 

    def service(self):
        if self.is_active:
            now = time.time()
            if  self.prev_service != None:
                try:
                    t =  (now - self.prev_service) * 1000
                    delta = t-self.FRAME_RATE_ms
                    if delta > -1:
                        self.prev_service = now
                        #  self.f.write(format("%f, %f\n" % (t, delta)))
                        self.RemoteControl.service()
                        if self.local_control:
                            self.local_control.service()
                        self.client.service()
                        self.do_transform(self.client.get_transform())
                        if self.platform_status != self.platform.get_output_status():
                            self.platform_status = self.platform.get_output_status()
                            gutil.set_text(self.ui.lbl_festo_status, self.platform_status[0], self.platform_status[1])
                except Exception as e:
                    log.warning("timing test exception %s", e)
                    print(traceback.format_exc())
            else:
                self.prev_service = time.time()
                # self.f = open("timer_test.csv", "w")
                log.warning("starting service timing latency capture to file: timer_test.csv")
            QtCore.QTimer.singleShot(1, self.service)
        else:
            self.client.fin()
            # self.platform.fin()
            sys.exit()

    def quit(self):
        qm = QtWidgets.QMessageBox
        result = qm.question(self, 'Exit?', "Are You Sure you want to quit?", qm.Yes | qm.No)
        if result != qm.Yes:
            return
        self.is_active = False # this will trigger exit in the service routine


app = QtWidgets.QApplication(sys.argv) 

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
    app .exit()
    sys.exit()
    log.info("Exiting Platform Controller\n")
    log.shutdown()

if __name__ == "__main__":
    main()
