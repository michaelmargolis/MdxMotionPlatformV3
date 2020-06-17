""" Platform Controller connects a selected client to chair.

Copyright Michael Margolis, Middlesex University 2019; see LICENSE for software rights.

This version requires NoLimits attraction license and NL ver 2.5.3.4 or later
note actuator lengths now expressed as muscle compression in mm (prev was total muscle length)
"""
import logging
import traceback
import argparse
import sys
import os
import time
import numpy as np
# from math import degrees

import importlib
from main_gui import *

sys.path.insert(0, './common')
import gui_sleep
from serialSensors import Encoder, ServoModel
import serial_defaults
import gui_utils as gutil

sys.path.insert(0, './output')
from kinematicsV2 import Kinematics
from dynamics import Dynamics
from muscle_output import MuscleOutput
import output_gui
import d_to_p
from  platform_config import *

log = logging.getLogger(__name__)
# default handler can be overridden in main 
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%H:%M:%S')

class Controller(QtGui.QMainWindow):

    def __init__(self, festo_ip):
        try:
            self.FRAME_RATE = 0.05
            # self.prevT = 0 # for debug
            self.platform = MuscleOutput(festo_ip)
            self.platform_status = None
            self.is_active = True  # set False to terminate
            self.is_output_enabled = False
            self.init_platform_parms()
            self.init_gui()
            self.init_kinematics()
            client.begin(self.cmd_func, self.move_func, cfg.limits_1dof)
            self.init_serial()
            self.dynam = Dynamics()
            self.dynam.init_gui(self.ui.frm_dynamics)
            self.dynam.begin(cfg.limits_1dof, "gains.cfg")
            self.set_intensity(10)  # default intensity at max
            log.warning("Dynamics module has washout disabled, test if this is acceptable")
            self.service_timer = QtCore.QTimer(self) # timer for telemetry data
            self.service_timer.timeout.connect(self.service)
            self.service_timer.start(int(self.FRAME_RATE*1000))
            log.info("Service timer started with interval of %d ms", int(self.FRAME_RATE*1000))
            log.info("Platform controller initializations complete")
        except:
            raise

    def init_kinematics(self):
        self.k = Kinematics()
        # cfg = PlatformConfig()
        cfg.calculate_coords()
        log.info("Starting %s as %s", cfg.PLATFORM_NAME, cfg.PLATFORM_TYPE)
        # self.telemetry = Telemetry(self.telemetry_cb, cfg.limits_1dof)
        self.k.set_geometry(cfg.BASE_POS, cfg.PLATFORM_POS)

        if cfg.PLATFORM_TYPE == "SLIDER":
            self.is_slider = True
            self.k.set_slider_params(cfg.joint_min_offset, cfg.joint_max_offset, cfg.strut_length,
                                     cfg.slider_angles)
            self.actuator_lengths = [0] * 6   # muscles fully relaxed
            d_to_p_file = 'output/DtoP.csv'
        else:
            self.is_slider = False
            self.k.set_platform_params(cfg.MIN_ACTUATOR_LEN, cfg.MAX_ACTUATOR_LEN, cfg.FIXED_LEN)
            self.platform.set_platform_params(cfg.MIN_ACTUATOR_LEN, cfg.MAX_ACTUATOR_LEN, cfg.FIXED_LEN) ### temp only for testing
            self.actuator_lengths = [cfg.PROPPING_LEN] * 6 # position for moving prop
            d_to_p_file = 'output/DtoP_v3.csv'

        assert cfg.MAX_ACTUATOR_RANGE == 200 # d to p files assume max range is 200
        log.info("Actuator range=%d mm", cfg.MAX_ACTUATOR_RANGE)
        self.DtoP = d_to_p.D_to_P(cfg.MAX_ACTUATOR_RANGE) # argument is max distance
        if self.DtoP.load_DtoP(d_to_p_file):
            assert self.DtoP.d_to_p_up.shape[1] == self.DtoP.d_to_p_down.shape[1]
            log.info("Loaded %d rows of distance to pressure files ", self.DtoP.rows)
            self.platform.set_d_to_p_curves(self.DtoP.d_to_p_up, self.DtoP.d_to_p_down) # pass curves to platform module
        else:
            log.error("Failed to loaded %s file", d_to_p_file)

    def init_platform_parms(self):
        # self.platform.begin(cfg.MIN_ACTUATOR_LEN, cfg.MAX_ACTUATOR_LEN, cfg.DISABLED_LEN, cfg.PROPPING_LEN, cfg.FIXED_LEN)
        self.platform_disabled_pos = np.empty(6)   # position when platform is disabled
        self.platform_winddown_pos = np.empty(6)  # position for attaching stairs
        self.platform_disabled_pos.fill(cfg.DISABLED_LEN)   # position when platform is disabled (propped)
        self.platform_winddown_pos.fill(cfg.PROPPING_LEN)      # position for attaching stairs or moving prop

    def init_gui(self):
        QtGui.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.tabWidget.currentChanged.connect(self.tab_changed)
        self.ui_tab = 0
        try:
            client.init_gui(self.ui.frm_input)
            self.output_gui = output_gui.OutputGui()
            self.output_gui.init_gui(self.ui.frm_output, cfg.MIN_ACTUATOR_LEN, cfg.MAX_ACTUATOR_RANGE)
            self.ui.lbl_platform.setText("Platform: " + cfg.PLATFORM_NAME)
            self.ui.lbl_client.setText("Client: " + client.name)
            self.ui.btn_exit.clicked.connect(self.quit)
            self.ui.chk_festo_wait.stateChanged.connect(self.festo_check) 
            self.ui.btn_activate.clicked.connect(self.enable_platform)
            self.ui.btn_deactivate.clicked.connect(self.disable_platform)
            # self.output_gui.show_muscles([0,0,30,0,0,.5], [800,850,900,950, 800, 1000]) # testing
            return True
        except:
            e = sys.exc_info()[0]  # report error
            log.error("error in init gui %s, %s", e, traceback.format_exc())
        return False

    def festo_check(self, state):
        if state == QtCore.Qt.Checked:
            log.info("System will wait for Festo msg confirmations")
            self.platform.set_wait(True)
        else:
            log.info("System will ignore Festo msg confirmations")
            self.platform.set_wait(False)

    def init_serial(self):
        if self.is_slider:
            self.encoder = Encoder()
            if 'encoder' in serial_defaults.dict:
                port = serial_defaults.dict['encoder']
                log.info("Attempting connect to encoders on port %s", port)
                if self.encoder.open_port(port, 115200):
                    log.info("Encoders connected on %s", port)
        self.servo_model = ServoModel() # 57600 baud
        if 'model' in serial_defaults.dict:
            port = serial_defaults.dict['model']
            log.info("Attempting connect to servo model on port %s", port)
            if self.servo_model.open_port(port, 57600):
                log.info("Servo model connected on %s", port)

    def tab_changed(self, tab_index):
        self.ui_tab = tab_index

    def enable_platform(self):
        """
        enable sets flag to for output

        
        disable resets flag for output
        calls client to reset
        engages piston
        drops platform to disabled pos
        """
        # request = self.process_request(client.get_current_pos())
        # actuator_lengths = self.k.actuator_lengths(request)
        # self.platform.set_enable(True, self.actuator_lengths)
        if not self.is_output_enabled:
            self.is_output_enabled = True
            log.debug("Platform Enabled")
        self.set_activation_buttons(True)

    def disable_platform(self):
        request = self.process_request(client.get_current_pos())
        actuator_lengths = self.k.actuator_lengths(request)
        # self.platform.set_enable(False, self.actuator_lengths)
        if self.is_output_enabled:
            self.is_output_enabled = False
            self.platform.set_pistion_flag(False)
            log.debug("in disable, lengths=%s", ','.join('%d' % l for l in actuator_lengths))
            self.platform.slow_move(actuator_lengths, self.platform_disabled_pos, 1000)
        self.set_activation_buttons(False)

    def set_activation_buttons(self, isEnabled): 
        if isEnabled:
            gutil.set_button_style(self.ui.btn_activate, True, True, "Activated", checked_color='green')  # enabled, checked
            gutil.set_button_style(self.ui.btn_deactivate, True, False, "Deactivate")  # enabled, checked
        else:
            gutil.set_button_style(self.ui.btn_activate, True, False, "Activate")  # enabled, not checked
            gutil.set_button_style(self.ui.btn_deactivate, True, True, "Deactivated")  # enabled, checked

    def move_to_idle(self):
        log.debug("move to idle")
        # request = self.process_request(client.get_current_pos())
        # actuator_lengths  = self.k.actuator_lengths(request)
        actuator_lengths = self.platform.prev_distances
        ##pos = client.get_current_pos() # was used to get z pos (pos[2])
        self.park_platform(True)  # added 25 Sep as backstop to prop when coaster state goes idle
        self.platform.slow_move(actuator_lengths, self.platform_disabled_pos, 10) # rate is cm per sec

    def move_to_ready(self):
        #  request = self.process_request(client.get_current_pos())
        #  actuator_lengths  = self.k.actuator_lengths(request)
        ##pos = client.get_current_pos() # was used to get z pos
        log.warning("move to ready - TODO, pressure curves are hard coded!")
        log.debug("move to ready")
        self.run_lookup()

    def swell_for_access(self):
        if not self.is_slider:
            #Briefly raises platform high enough to insert access stairs and activate piston
            log.debug("Start swelling for access")
            self.platform.slow_move(self.platform_disabled_pos, self.platform_winddown_pos, 10)
            gui_sleep.sleep(3) # time in seconds in up pos
            self.platform.slow_move(self.platform_winddown_pos, self.platform_disabled_pos, 10)
            log.debug("Finished swelling for access")

    def park_platform(self, state):
        if state:
            self.platform.set_pistion_flag(False)
            log.debug("Setting flag to activate piston to 0")
        else:
            self.platform.set_pistion_flag(True)
            log.debug("setting flag to activate piston to 1")
        log.debug("Sending last requested pressure with new piston state")
        # self._send(self.requested_pressures[:6])  # current prop state will be appended in _send
        if state:
            gui_sleep.sleep(0.5)
        # Todo check if more delay is needed

        log.debug("Platform park state changed to %s", "parked" if state else "unparked")

    def set_intensity(self, intensity):
        lower_payload_weight = 20  # todo - move these or replace with real time load cell readings
        upper_payload_weight = 90
        payload = self.scale((intensity), (0, 10), (lower_payload_weight, upper_payload_weight))
        #  print "payload = ", payload
        self.platform.set_payload(payload)
        intensity = intensity * 0.1
        self.dynam.set_intensity(intensity)
        status = format("%d percent Intensity, (Weight %d kg)" % (self.dynam.get_overall_intensity() * 100, payload))
        client.intensity_status_changed((status, "green"))

    def run_lookup(self):
        # find closest curves for each muscle at the current load
        up_pressure = 3000
        down_pressure = 2000
        dur = 2

        self.platform.slow_pressure_move(0, up_pressure, dur)
        time.sleep(.5)
        encoder_data, timestamp = self.encoder.read()
        log.warning("TODO, using hard coded encoder data!")
        encoder_data = np.array([123, 125, 127, 129, 133, 136])
        self.DtoP.set_DtoP_index(up_pressure, encoder_data, 'up')
        # self.ui.txt_up_index.setText(str(self.DtoP.up_curve_idx))

        self.platform.slow_pressure_move(up_pressure, down_pressure, dur/2)
        time.sleep(.5)
        encoder_data, timestamp = self.encoder.read()
        encoder_data = np.array([98, 100, 102, 104, 98, 106])
        self.DtoP.set_DtoP_index(down_pressure, encoder_data, 'down')
        # self.ui.txt_down_index.setText(str(self.DtoP.down_curve_idx))
        self.platform.set_d_to_p_indices(self.DtoP.up_curve_idx, self.DtoP.down_curve_idx)


    def scale(self, val, src, dst): # the Arduino 'map' function written in python
        return (val - src[0]) * (dst[1] - dst[0]) / (src[1] - src[0])  + dst[0]

    def process_request(self, request):
        #  print "in process", request
        if client.is_normalized:
            # print "pre regulate", request,
            # request = shape.shape(request)  # adjust gain & washout and convert from norm to real
            request = self.dynam.regulate(request)
            #  print "post",request
        return request

    def move(self, position_request):
        #  position_requests are in mm and radians (not normalized)
        #start = time.time()
        # print "req= " + " ".join('%0.2f' % item for item in position_request)
        self.actuator_lengths = self.k.actuator_lengths(position_request)
        if self.ui_tab == 2: # the output tab
            self.output_gui.show_muscles(position_request, self.actuator_lengths)
        ## if client.USE_UDP_MONITOR and client.USE_UDP_MONITOR == True:
        ## self.platform.echo_requests_to_udp(position_request)
        self.platform.move_distance(self.actuator_lengths)

        #  print "dur =",  time.time() - start, "interval= ",  time.time() - self.prevT
        #  self.prevT =  time.time()

    def cmd_func(self, cmd):  # command handler function called from Platform input
        if cmd == "exit": self.is_active = False
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

    def move_func(self, request): # move handler to position platform
        #  print "request is translation/rotation list:", request
        try:
            start = time.time()
            r = self.process_request(np.array(request))

            self.move(r)
            """
            if client.log:
                r[3] = r[3]* 57.3  # convert to degrees
                r[4] = r[4]* 57.3
                r[5] = r[5]* 57.3
                # client.log(r)
            """
            log.debug("processing duration = %d", time.time() - start)
        except:
            e = sys.exc_info()[0]  # report error
            log.error("error in move function %s", e)

    def service(self):
        if self.is_active:
            client.service()
            if self.platform_status != self.platform.get_output_status():
                self.platform_status = self.platform.get_output_status()
                gutil.set_text(self.ui.lbl_festo_status, self.platform_status[0], self.platform_status[1])
        else:
            client.fin()
            # self.platform.fin()
            sys.exit()

    def quit(self):
        qm = QtGui.QMessageBox
        result = qm.question(self, 'Exit?', "Are You Sure you want to quit?", qm.Yes | qm.No)
        if result != qm.Yes:
            return
        self.is_active = False # this will trigger exit in the service routine


# qt app is defined in gui sleep so it can be imported into files needing non-blocking sleep
gui_sleep._gui__app = QtGui.QApplication(sys.argv)

cfg = importlib.import_module(platform_selection).PlatformConfig()
client = importlib.import_module(client_selection).InputInterface(gui_sleep.sleep)

def man():
    parser = argparse.ArgumentParser(description='Platform Controller\nAMDX motion platform control application')
    parser.add_argument("-l", "--log",
                        dest="logLevel",
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")
    parser.add_argument("-f", "--festo_ip",
                        dest="festoIP",
                        help="Set IP address of Festo controller")
    return parser


def main():
    args = man().parse_args()
    if args.logLevel:
        logging.basicConfig(level=args.logLevel, format='%(asctime)s %(levelname)-8s %(message)s',
                            datefmt='%H:%M:%S')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s',
                            datefmt='%H:%M:%S')

    log.info("Python: %s", sys.version[0:5])
    log.info("Starting Platform Controller")
    try:
        if args.festoIP:
            controller = Controller(args.festoIP)
        else:
            controller = Controller('')
        controller.show()
        gui_sleep._gui__app.exec_()

    except:
        e = sys.exc_info()[0]  # report error
        log.error("error in main %s, %s", e, traceback.format_exc())

    controller.close()
    gui_sleep._gui__app .exit()
    sys.exit()
    log.info("Exiting Platform Controller\n")
    log.shutdown()

if __name__ == "__main__":
    main()
