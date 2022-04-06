""" 
PlatformMover.py

Code to move the platform in 6 DoF
"""

import sys, os
import time

import logging as log
import logging.handlers
import argparse
import operator  # for map sub
import importlib
import socket
import traceback
import math # for conversion of radians to degrees

from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox

RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(RUNTIME_DIR))

from kinematics.dynamics import Dynamics

from kinematics.kinematicsV2 import Kinematics
from kinematics.cfg_SlidingActuators import *
from  system_config import  cfg
#  from kinematics.cfg_SuspendedChair import *
import output.plot_config as plot_config   # for show_geometry

import output.d_to_p as d_to_p
from output.muscle_output import MuscleOutput

import PlatformCalibrate.spacenavigator as sn # 6 dof mouse


DATA_PERIOD = 50  # ms between samples

ECHO_UDP_IP = "127.0.0.1"
ECHO_UDP_PORT = 10020
echo_address = (ECHO_UDP_IP, ECHO_UDP_PORT )

slider_config_module = "cfg_SlidingActuators"
chair_config_module = "cfg_SuspendedChair"

slider_increments = (5)*6  # todo for slow moves

qtcreator_file  = "PlatformCalibrate/PlatformMover.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, festo_ip):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.echo_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP


        self.timer_data_update = None
        self.estopped = False
        self.is_ready = False # True when platform config is loaded
        self.sn_avail = False  # space mouse
        self.time_interval = DATA_PERIOD / 1000.0
        self.slider_values = [0]*6  # the actual slider percents (-100 to 100)
        self.lagged_slider_values = [0]*6  # values used for sending to festo

        self.target_pressures = [] # pressures sent to festo
        self.pressure_deltas = []  # dif between commanded and actual pressure        
        
        self.ui.txt_festo_ip.setText(festo_ip)

        # configures
        self.configure_timers()
        self.configure_signals()
        self.configure_defaults()
        self.configure_buttons()
        self.configure_festo_info(festo_ip)

    def festo_sequence_test(self):
        percents = [0]*6
        for i in range(6):
            percents[i] = 20
            self.muscle_output.move_percent(percents)
            print("output percents: ", percents)
            time.sleep(1)
    
    def configure_timers(self):
        self.timer_data_update = QtCore.QTimer(self) # timer services muscle pressures and data
        self.timer_data_update.timeout.connect(self.data_update)
        self.timer_data_update.start(DATA_PERIOD)

    def configure_signals(self):
        self.ui.btn_estop.clicked.connect(self.estop)
        self.ui.btn_load_config.clicked.connect(self.load_config)
        self.ui.btn_centre.clicked.connect(self.centre_pos)
        self.ui.btn_load_pos.clicked.connect(self.load_pos)
        self.ui.btn_show_geometry_2d.clicked.connect(self.show_geometry_2d)
        self.ui.btn_show_geometry_3d.clicked.connect(self.show_geometry_3d)
        self.ui.rb_chair.clicked.connect(self.chair_selected)
        self.ui.rb_slider.clicked.connect(self.slider_selected)
        
    def configure_festo_info(self, festo_ip):
        self.festo_ip = festo_ip
        self.ui.txt_festo_ip.setText(festo_ip)
        self.pressure_bars = [self.ui.muscle_0,self.ui.muscle_1,self.ui.muscle_2,self.ui.muscle_3,self.ui.muscle_4,self.ui.muscle_5]
        self.actual_bars = [self.ui.actual_0,self.ui.actual_1,self.ui.actual_2,self.ui.actual_3,self.ui.actual_4,self.ui.actual_5]
        self.txt_muscles = [self.ui.txt_muscle_0,self.ui.txt_muscle_1,self.ui.txt_muscle_2,self.ui.txt_muscle_3,self.ui.txt_muscle_4,self.ui.txt_muscle_5]
        for t in self.txt_muscles:
             t.setText('?')
        self.ui.chk_festo_actuals.stateChanged.connect(self.festo_check)

    def configure_defaults(self):
        self.ui.txt_config_fname.setText(slider_config_module)
        self.d_to_p_fname = "output\\DtoP.csv"
        if len(sn.list_devices()) > 0:
            self.ui.txt_spacemouse.setText(sn.list_devices()[0])
        else:
            self.ui.txt_spacemouse.setText("Not found")
        self.sn_avail = sn.open()

    def configure_buttons(self):  
        self.ui.tab_info.setEnabled(False) # these set true after config loaded
        self.ui.tab_test.setEnabled(False)    

        #  button groups
        self.mouse_rbuttons = [self.ui.rb_m_off, self.ui.rb_m_inc, self.ui.rb_m_abs]
        self.mouse_btn_group = QtWidgets.QButtonGroup()
        for i in range(len(self.mouse_rbuttons)):
           self.mouse_btn_group.addButton(self.mouse_rbuttons[i], i)
           
        self.transfrm_sliders = [self.ui.sld_0, self.ui.sld_1, self.ui.sld_2, self.ui.sld_3, self.ui.sld_4, self.ui.sld_5  ]
        self.lag_indicators = [self.ui.pg_0, self.ui.pg_1, self.ui.pg_2, self.ui.pg_3, self.ui.pg_4, self.ui.pg_5]

    def configure_kinematics(self):
        # load_config() must be called before this method 
        self.k = Kinematics()
        self.cfg.calculate_coords()

        self.k.set_geometry(self.cfg.BASE_POS, self.cfg.PLATFORM_POS)
        if self.cfg.PLATFORM_TYPE == "SLIDER":
            self.k.set_slider_params(self.cfg.joint_min_offset, self.cfg.joint_max_offset, self.cfg.strut_length, self.cfg.slider_angles)
            self.is_slider = True
        else:
            self.k.set_platform_params(self.cfg.MIN_ACTUATOR_LEN, self.cfg.MAX_ACTUATOR_LEN, self.cfg.FIXED_LEN)
            self.is_slider = False
            
        self.invert_axis = self.cfg.INVERT_AXIS 
        self.swap_roll_pitch = self.cfg.SWAP_ROLL_PITCH
   
        self.DtoP = d_to_p.D_to_P(200) # argument is max distance 
        self.dynam = Dynamics()
        self.dynam.begin(self.cfg.limits_1dof,"shape.cfg")
        
    def show_geometry_2d(self):
         plot_config.plot( self.cfg.BASE_POS,  self.cfg.PLATFORM_POS, self.cfg.PLATFORM_MID_HEIGHT, self.cfg.PLATFORM_NAME )

    def show_geometry_3d(self):
         plot_config.plot3d(self.cfg, self.cfg.PLATFORM_POS)

    def data_update(self):
        #  todo if self.estopped then call loadpos and return
        if self.is_ready == False:
            return # don't output if platform config not loaded
        percent_delta = 100.0 / (self.ui.sld_lag.value() / DATA_PERIOD)  # max percent change for each update

        for idx, slider in enumerate(self.transfrm_sliders):
            self.slider_values[idx] = slider.value()
            if not self.ui.chk_instant_move.isChecked():  # moves deferred if checked (todo rename to chk_defer_move)
                if self.lagged_slider_values[idx] + percent_delta <= self.slider_values[idx]:
                    self.lagged_slider_values[idx] += percent_delta
                elif self.lagged_slider_values[idx] - percent_delta >=  self.slider_values[idx]:
                    self.lagged_slider_values[idx] -= percent_delta
                else:
                    self.lagged_slider_values[idx] = self.slider_values[idx]
            if self.lagged_slider_values[idx] ==  self.slider_values[idx]:
                self.lag_indicators[idx].setValue(1)
            else:
                self.lag_indicators[idx].setValue(0)
        # print("raw sliders", self.slider_values, "lagged:", self.lagged_slider_values )
        if self.ui.rb_m_inc.isChecked(): 
            self.get_mouse_transform()
            print("not implimented")
        elif self.ui.rb_m_abs.isChecked():
            mouse_xform = self.get_mouse_transform()
            for i in range(len(self.transfrm_sliders)):
                self.transfrm_sliders[i].setValue( int(mouse_xform[i] * 100))
        self.move()
        out_pressures = self.muscle_output.festo.out_pressures
        self.target_pressures.append(out_pressures)
        delta = map(operator.sub, self.muscle_output.in_pressures , out_pressures)
        self.pressure_deltas.append(delta)
        self.actual_pressures = self.muscle_output.get_pressures()
        self.show_pressures(self.actual_pressures)

    def get_mouse_transform(self):
        # returns list of normalized floats
        state = sn.read()
        transform = [state.x, state.y, state.z, state.roll, state.pitch, state.yaw]
        return transform

   
    def move(self):
        transform = [x * .01 for x in self.lagged_slider_values]
        
        transform = [inv * axis for inv, axis in zip(self.invert_axis, transform)]
        if self.swap_roll_pitch:
            # swap roll, pitch and x,y
            transform[0],transform[1], transform[3],transform[4] =  transform[1],transform[0],transform[4], transform[3]

        request = self.dynam.regulate(transform) # convert normalized to real values
        percents = self.k.actuator_percents(request)
        
        self.muscle_output.move_percent(percents)
        distances = self.k.actuator_lengths(request)
        self.echo( request.tolist(), distances)

    def centre_pos(self):
        for slider in self.transfrm_sliders:
            slider.setValue(0)

    def load_pos(self):
        for idx, slider in enumerate(self.transfrm_sliders):
            if( idx == 2):
                slider.setValue(-100)
            else:
                slider.setValue(0)
        self.move()

    def echo(self, transform, distances):
        # print(transform, distances)
        t = [""]*6
        for idx, val in enumerate(transform):
            if idx < 3:
                if idx == 2:
                    val = -val #  TODO invert z ?
                t[idx] = str(round(val))
            else:
                t[idx] = str(round(val*180/math.pi, 1))
        
        # req_msg = "request," + ','.join(str(round(t*180/math.pi, 1)) for t in transform)
        req_msg = "request," + ','.join(t)
        dist_msg = ",distances," +  ",".join(str(int(d)) for d in distances)
        msg = req_msg + dist_msg + "\n"
        # print(msg)
        self.echo_sock.sendto(bytes(msg, "utf-8"), echo_address)

    def estop(self):
        if self.estopped:
            self.estopped = False
            self.ui.btn_estop.setText("Emergency Stop")
        else:
            self.estopped = True
            self.muscle_output.is_slow_moving = False # stop any running ride TODO remove this?
            self.load_pos();
            self.ui.btn_estop.setText("Press to Clear")

    def chair_selected(self):
        self.ui.txt_config_fname.setText(chair_config_module)
        self.ui.lbl_platform_image.setPixmap(QtGui.QPixmap("images/chair_small.jpg"))

    def slider_selected(self):
        self.ui.txt_config_fname.setText(slider_config_module)
        self.ui.lbl_platform_image.setPixmap(QtGui.QPixmap("images/slider_small.jpg"))
            
    def load_config(self):
        cfg_path =  'kinematics.' + self.ui.txt_config_fname.text()
        try:        
            cfg = importlib.import_module(cfg_path)
            self.cfg = cfg.PlatformConfig()
            self.cfg.calculate_coords()
            self.configure_kinematics()
            self.muscle_output = MuscleOutput(self.DtoP.distance_to_pressure, self.festo_ip)
            # load distance to pressure curves from file
            if self.DtoP.load(self.d_to_p_fname): 
                print("todo: add option for polynomial instead of lookup?")
            self.ui.tab_load.setEnabled(False)
            self.ui.tab_info.setEnabled(True)
            self.ui.tab_test.setEnabled(True)
            self.show_cfg_info()
            self.ui.tabWidget.setCurrentIndex(1)
            if self.cfg.HAS_BRAKE == False: 
                self.ui.chk_brake.hide()
            self.is_ready = True
        except Exception as e:
            print(str(e) + "\nunable to import cfg from:", cfg_path)
            print(traceback.format_exc())

    def show_cfg_info(self):
        txt = "Platform Name:\t" + self.cfg.PLATFORM_NAME + "\n" + \
        "Platform Type:\t" + self.cfg.PLATFORM_TYPE + "\n"
        if self.cfg.PLATFORM_INVERTED:
            txt += "Platform Inverted\tTrue\n"
        txt += "Translation limits:\tx={}, y={}, z={} millimeters\n".format(self.cfg.limits_1dof[0], self.cfg.limits_1dof[1], self.cfg.limits_1dof[2])  
        txt += "Rotation limits:\troll={}, pitch={}, yaw={} degrees\n".format(round(math.degrees(self.cfg.limits_1dof[3])),
                                                      round(math.degrees(self.cfg.limits_1dof[4])),round(math.degrees(self.cfg.limits_1dof[5])))       
        if self.cfg.PLATFORM_TYPE == "SLIDER":
            txt+= "Muscle movement range:\t{} millimeters\n".format(self.cfg.slider_range)
        else:    
            txt+= "Muscle movement range:\t{} millimeters\n".format(self.cfg.MAX_ACTUATOR_RANGE) 
        if self.cfg.HAS_PISTON:
            txt+= "Has propping piston:\tTrue\n"
        if self.cfg.HAS_BRAKE:
            txt+= "Has electric brake:\tTrue\n"
        if self.cfg.SWAP_ROLL_PITCH:
            txt+= "Roll & pitch swapped:\tTrue\n"
        if -1 in self.cfg.INVERT_AXIS:
            txt+= "Axis invert list:\t" + str(self.cfg.INVERT_AXIS)+"\n"
        txt+= "\nFesto Ip address:\t{}".format(self.festo_ip)
        self.ui.txt_info.appendPlainText(txt)

    def show_pressures(self, pressures):
        for i in range(6):
            rect =  self.pressure_bars[i].rect()
            width = round(pressures[i] / 20)
            rect.setWidth(width)
            self.pressure_bars[i].setFrameRect(rect)
            self.txt_muscles[i].setText(format("%d mb" % pressures[i])) #may  be overwritten with actuals 
        if self.ui.chk_festo_actuals.isChecked():
            # actuals = pressures # [100,200,500,700, 2000, 5000]
            self.show_actual_pressures(self.actual_pressures)

    def show_actual_pressures(self, actuals):
        for i in range(6):
            rect =  self.actual_bars[i].rect()
            width = round(actuals[i] / 20)
            rect.setWidth(width)
            self.actual_bars[i].setFrameRect(rect)
            
    def festo_check(self, state):
        if state == QtCore.Qt.Checked:
            log.info("System will request Festo actual pressures")
            self.muscle_output.set_wait_ack(False)
            self.muscle_output.enable_poll_pressures(True)
        else:
            log.info("System will ignore Festo actual pressures")
            self.muscle_output.set_wait_ack(True)
            self.muscle_output.enable_poll_pressures(False)

def start_logging(level):
    log_format = log.Formatter('%(asctime)s,%(levelname)s: %(message)s')
    logger = log.getLogger()
    logger.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler("PlatformCalibration.log", maxBytes=(10240 * 5), backupCount=2)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    console_handler = log.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)


def man():
    parser = argparse.ArgumentParser(description='PlatformCalibration\nA real time testing application')
    parser.add_argument("-l", "--log",
                        dest="logLevel",
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")
    parser.add_argument("-f", "--festo_ip",
                        dest="festoIP",
                        help="Set IP address of Festo controller")                        
    return parser


if __name__ == '__main__':
    # multiprocessing.freeze_support()
    args = man().parse_args()
    if args.logLevel:
        start_logging(args.logLevel)
    else:
        start_logging(log.INFO)

    log.info("Python: %s, qt version %s", sys.version[0:5], QtCore.QT_VERSION_STR)
    log.info("Starting PlatformMover")

    app = QtWidgets.QApplication(sys.argv)
    if args.festoIP:
        win = MainWindow(args.festoIP)        
    else:
        win = MainWindow('192.168.0.10')
    win.show()
    app.exec_() #mm added underscore

    log.info("Exiting\n")
    log.shutdown()
    win.close()
    app.exit()  
    sys.exit()
