
""" 
SimInterface.py

Code to drive  platform from various sims using a simple protocol

protocol: "xyzrpy,x,y,z,roll,pitch,yaw\n"
where parameters are float values ranging between -1 and 1
"""

from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox
import sys
import os
import time
import logging as log
import logging.handlers
import argparse
import operator  # for map sub
import importlib
import socket
import traceback
import math # for conversion of radians to degrees

RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(RUNTIME_DIR))

import common.gui_utils as gutil # for sleep QT func
from kinematics.dynamics import Dynamics
from kinematics.kinematicsV2 import Kinematics
from kinematics.cfg_SlidingActuators import *
from  system_config import  cfg
#  from kinematics.cfg_SuspendedChair import *

import output.d_to_p as d_to_p
from output.muscle_output import MuscleOutput

import SimpleSims.available_sims  as sims  # sims to be loaded are defined in this module
#available_sims = [[ "Microsoft fs2020", "fs2020"],["X-Plane 11", "xplane"],
#              ["Space Coaster", "spacecoaster"],["NoLimits2 Coaster", "nolimits2"]]

LATENCY = 0
DATA_PERIOD =  50 - LATENCY  # ms between samples

ECHO_UDP_IP = "127.0.0.1"
echo_address = ((ECHO_UDP_IP, 10020),(ECHO_UDP_IP, 10021))

slider_config_module = "cfg_SlidingActuators"
chair_config_module = "cfg_SuspendedChair"

qtcreator_file  = "SimpleSims/SimInterface.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons
        
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, festo_ip):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.echo_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP

        self.timer_data_update = None
        self.estopped = False
        self.is_ready = False # True when platform config is loaded
        self.sn_avail = False  # space mouse
        self.sim = None
        self.time_interval = DATA_PERIOD / 1000.0
        self.slider_values = [0]*6  # the actual slider percents (-100 to 100)
        self.lagged_slider_values = [0]*6  # values used for calculating pressures

        self.target_pressures = [] # pressures sent to festo

        self.csv_outfile = None
        
        self.festo_ip = festo_ip
        self.ui.txt_festo_ip.setText(festo_ip)
        # configures
        self.configure_timers()
        self.configure_signals()
        self.configure_defaults()
        self.configure_buttons()        

    def closeEvent(self, event):
        log.info("User exit")
        if self.sim:
            self.sim = None
        event.accept()
        
    def configure_timers(self):
        self.timer_data_update = QtCore.QTimer(self) # timer services muscle pressures and data
        self.timer_data_update.timeout.connect(self.data_update)
        self.timer_data_update.setTimerType(QtCore.Qt.PreciseTimer)

    def configure_signals(self):
        self.ui.btn_estop.clicked.connect(self.estop)
        self.ui.btn_load_config.clicked.connect(self.load_config)
        self.ui.btn_centre.clicked.connect(self.centre_pos)
        self.ui.btn_load_pos.clicked.connect(self.load_pos)
        self.ui.btn_load_sim.clicked.connect(self.load_sim)
        self.ui.btn_connect_sim.clicked.connect(self.connect_sim)
        self.ui.btn_park.clicked.connect(self.button_clicked)
        self.ui.btn_run.clicked.connect(self.button_clicked)
        self.ui.btn_pause.clicked.connect(self.button_clicked)
        self.ui.chk_capture_csv.stateChanged.connect(self.capture)
        self.ui.rb_chair.clicked.connect(self.chair_selected)
        self.ui.rb_slider.clicked.connect(self.slider_selected)
        self.ui.cmb_sim_select.activated.connect(self.sim_combo_changed)
        self.ui.tabWidget.currentChanged.connect(self.tab_changed)

    def configure_defaults(self):
        self.ui.grp_platform_control.hide()
        self.ui.lbl_connecting_status.setText("Choose desired platform above and click 'Load Config'")
        self.slider_selected() # default platform
        print('Available Sims:')
        for i in range(len(sims.available_sims)):
            print('\t' + sims.available_sims[i][0])
            self.ui.cmb_sim_select.addItem(sims.available_sims[i][0])
        self.ui.cmb_sim_select.setCurrentIndex(sims.default_sim)
        self.sim_combo_changed() # init to default values
        self.d_to_p_fname = "output\\DtoP.csv"

    def configure_buttons(self):        
        self.ui.tab_platform.setEnabled(False)
        self.ui.grp_sim.setEnabled(False) 
        #  button groups 
        self.gain = [self.ui.sld_gain_0, self.ui.sld_gain_1, self.ui.sld_gain_2, self.ui.sld_gain_3, self.ui.sld_gain_4, self.ui.sld_gain_5  ]        
        self.transfrm_levels = [self.ui.sld_xform_0, self.ui.sld_xform_1, self.ui.sld_xform_2, self.ui.sld_xform_3, self.ui.sld_xform_4, self.ui.sld_xform_5  ]

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

    def button_clicked(self, sender):
        source = self.sender()
        if source == self.ui.btn_park:
            print('park')
            self.ui.btn_run.setChecked(False)
            self.ui.btn_pause.setChecked(False)
        elif source == self.ui.btn_run:
            print('run')
            self.ui.btn_park.setChecked(False)
            self.ui.btn_pause.setChecked(False)
            self.run()
        elif source == self.ui.btn_pause:
            print('pause') 
            self.ui.btn_park.setChecked(False)
            self.ui.btn_run.setChecked(False)
            self.pause() 
   
    def tab_changed(self, tab_index):
        if tab_index == 0:
            self.ui.grp_platform_control.hide()
        else:
            self.ui.grp_platform_control.show()
    
    def data_update(self):
        #  todo if self.estopped then call loadpos and return

        if not self.is_ready:
            print("ignoring update because not ready")
            return # don't output if distance to pressure file has not been loaded

        elif self.sim:
            transform = self.sim.read()
            if not self.sim.is_connected:
                self.report_state("not connected, is it running")
            if transform:
                self.move(transform)

    def move(self, transform):
        transform = [inv * axis for inv, axis in zip(self.invert_axis, transform)]           
        master_gain = self.ui.sld_gain_master.value() *.01     
        for idx in range(6): 
            gain = self.gain[idx].value() * master_gain      
            percent =  round(transform[idx]*gain)  
            self.transfrm_levels[idx].setValue(percent) # set the UI transform indicators
        request = self.dynam.regulate(transform) # convert normalized to real values
        if self.swap_roll_pitch:
            # swap roll, pitch and x,y if set in config
            request[0],request[1], request[3],request[4] =  request[1],request[0],request[4], request[3] 
        
        percents = self.k.actuator_percents(request)
       
        #percents = remap_valves(percents)
  
        self.muscle_output.move_percent(percents)
        distances = self.k.actuator_lengths(request)
        self.echo( request.tolist(), distances)

    def sim_combo_changed(self):       
        idx = self.ui.cmb_sim_select.currentIndex()
        self.selected_sim_name = sims.available_sims[idx][0]
        self.selected_sim_class =  sims.available_sims[idx][1]
        self.sim_loader = sims.available_sims[idx][2]
        img = "images/" + self.selected_sim_class + ".jpg"
        self.ui.lbl_sim_image.setPixmap(QtGui.QPixmap(img))
        
    def load_sim(self): 
        if not self.sim:
            # here if sim was not loaded by connect method
            sim_path = "SimpleSims." + self.selected_sim_class
            log.info("loading %s", sim_path)
            try:
                sim_module = importlib.import_module(sim_path)
                self.sim = sim_module.Sim(gutil.sleep_qt, self.ui.tab_sim)
                log.info("Imported sim: " + self.sim.name)
                self.sim.set_state_callback(self.report_state )

            except Exception as e:
                print(e)
                print(traceback.format_exc())
        try:
            err = self.sim.load(self.sim_loader)            
            self.report_state("Connected") 
            self.ui.lbl_connecting_status.setText(err)   
        except Exception as e:
            print(e)
            print(traceback.format_exc())

            
    def connect_sim(self):
        if not self.sim:
            print("selected sim is " + self.selected_sim_class)
            sim_path = "SimpleSims." + self.selected_sim_class
            try:
                sim_module = importlib.import_module(sim_path)
                self.sim = sim_module.Sim(gutil.sleep_qt, self.ui.tab_sim)
                log.info("imported sim " + self.sim.name) 
            except Exception as e:
                print(e)
                print(traceback.format_exc())
            
        if self.sim:
            self.ui.lbl_connecting_status.setText("Connecting...")
            self.sim.set_state_callback(self.report_state )  
            err = self.sim.connect()
            if err:
                self.ui.lbl_connecting_status.setText(err)
                log.error("connect err: " +  err)
            else:
                self.ui.lbl_connecting_status.setText("Connected")
                self.ui.tab_platform.setEnabled(True)
                self.ui.tabWidget.setCurrentIndex(1)
                self.ui.tab_load.setEnabled(False)
                self.is_ready = True;
                self.sim.run()
                self.timer_data_update.start(DATA_PERIOD) 
                log.info("Started {}ms data update timer".format(DATA_PERIOD) )               
             

    def report_state(self, state_info):
        self.ui.lbl_sim_status.setText(self.selected_sim_name + ": " + state_info)         

    def run(self):
        self.sim.run()

    def pause(self):
        self.sim.pause()
 
    def centre_pos(self):
        self.move((0,0,0,0,0,0))

    def load_pos(self):
        self.move((0,0,-1,0,0,0))

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
        for i in range(len(echo_address)):
            # print("sending",  echo_address[i], msg)
            self.echo_sock.sendto(bytes(msg, "utf-8"), echo_address[i])
  
        if self.csv_outfile:
            self.csv_outfile.write(msg)

    def capture(self):
        if self.ui.chk_capture_csv.isChecked():
            fname = self.ui.txt_csv_fname.text()
            self.open_file(fname)
        else:
            if self.csv_outfile:
                self.csv_outfile.close()
                self.csv_outfile = None

    def open_file(self, fname):
            if os.path.isfile(fname):
                reply = QMessageBox.question(self, 'Opening exisitng file', "Delete old data before adding new messages?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
                if reply == QMessageBox.Yes:
                    self.csv_outfile = open(fname, 'w')
                elif reply == QMessageBox.No:
                    self.csv_outfile = open(fname, 'a')
                elif reply == QMessageBox.Cancel:
                    return
            else:
                # here if file doesnt exist
                self.csv_outfile = open(fname, 'w')

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
            #self.ui.tab_load.setEnabled(False)
            self.ui.grp_sim.setEnabled(True) 
            self.ui.lbl_connecting_status.setText("Click 'Load Sim' if not already running, click 'Connect' when sim is loaded") 

        except Exception as e:
            print(str(e) + "\nunable to import cfg from:", cfg_path)
            print(traceback.format_exc())

            
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
    log.info("Starting SimInterface")

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
