# fs_gui_frame.py
# PYQT5 class to create GUI for flight sim control panel

import os, sys
import time
import logging as log
import traceback

from fs_panel import Panel

from PyQt5 import QtWidgets, uic, QtCore

RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(RUNTIME_DIR))

from common.serialSensors import SerialProcess

# pot_map_vars is the list of possible variables to be associated with potentiometers
pot_map_vars = ('Throttle', 'Propeller', 'Mixture', 'Spoilers')

qtcreator_file  = "SimpleSims/fs_gui_frame.ui"
ui, base = uic.loadUiType(qtcreator_file)


DATA_PERIOD =  20
BAUD = 115200
DEFAULT_PORT = 'COM34' 
GEAR_TEXT = ('Gear Up', 'Gear Down')

class frame_gui(QtWidgets.QFrame, ui):
    def __init__(self, parent=None):
        super(frame_gui, self).__init__(parent)
        self.setupUi(self)
        

""" this is the GUI for a flight sim interface """
class SimUI(object):  
    def __init__(self, sim, sleep_func, frame_rate=0.05):
        self.sleep_func = sleep_func
        self.frame_rate = frame_rate
        self.sim = sim # this is the SimConnect interface class
        self.panel = Panel(self.sim) 

    def init_ui(self, frame):
        self.ui = frame_gui(frame)
        self.set_ser_combo_default(self.panel, DEFAULT_PORT, self.ui.cmb_panel_port)
        self.pots = (self.ui.pot_0, self.ui.pot_1, self.ui.pot_2)
        self.pot_combos = (self.ui.cmb_pot_0, self.ui.cmb_pot_1, self.ui.cmb_pot_2)
        self.set_pot_mapping()
        # configures
        self.set_timer(frame, DATA_PERIOD)
        self.configure_signals()
        
    def set_ser_combo_default(self, ser, default, combo):
        ports = self.panel.get_ports()    
        combo.clear()
        combo.addItems(ports)
        log.debug("default port: %s", default)
        
        if default:
            index = combo.findText(default, QtCore.Qt.MatchFixedString)
            if index >= 0:
                combo.setCurrentIndex(index)
                self.connect()
            else:
                combo.setCurrentIndex(combo.count() - 1)
        else:
            combo.setCurrentIndex(combo.count() - 1)
            
    def set_pot_mapping(self):      
        for idx, potmap in enumerate(self.pot_combos):
            potmap.addItems(pot_map_vars)
            potmap.setCurrentIndex(idx)  # this sets default values
            potmap.addItem("Not Used")  
            potmap.setCurrentIndex(idx) 
        self.pot_combo_changed()  # create initial pot mappings
    
    def configure_signals(self):
        self.ui.btn_serial_connect.clicked.connect(self.connect)
        for pot_combo in self.pot_combos:
            pot_combo.currentTextChanged.connect(self.pot_combo_changed)            

    def set_timer(self, frame, interval):
        self.timer_data_update = QtCore.QTimer(frame) 
        self.timer_data_update.timeout.connect(self.data_update)
        self.timer_data_update.start(interval)
        log.debug("timer set to %d ms", interval)

    
    def pot_combo_changed(self):
        self.pot_simvar = []
        for combo in self.pot_combos:
           self.pot_simvar.append(combo.currentText())
        log.debug("pot assignments set to: %s",  self.pot_simvar)
        self.panel.pot_simvar = self.pot_simvar
        
    def connect(self):
        if self.panel.is_open():
            self.panel.close_port() 
            self.ui.btn_serial_connect.setText("    Connect    ")
        else:
            port = str(self.ui.cmb_panel_port.currentText())
            if 0 < len(port) and port != "Ignore":
                if self.panel.open_port(port, BAUD):
                    log.info("opened %s", port)
                    self.ui.btn_serial_connect.setText("  Disconnect  ")
                else:
                    log.warning("%s port is not available", port)
            else:
                log.error("%s port was not opened",  port)
                
    def data_update(self):
        if(self.sim.is_connected):
            self.ui.txt_SimConnect_status.setText("Connected")
            # xyzrpy = fs.read_transform()
            # csv = ['%.3f' %  elem for elem in xyzrpy]
            # print(','.join(csv))
            self.sim.read_panel_status()
            self.panel.set_gear_indicator(self.sim.gear_info)
            self.panel.set_brake_indicator(self.sim.parking_brake_info)
            self.panel.set_flaps_indicator(self.sim.flaps_angle, 60) 
        else:
            self.ui.txt_SimConnect_status.setText("Disconnected")
            self.sim.connect()
       
        if self.panel.is_open():
            self.panel.read()
            self.show_panel()

    def show_panel(self):
        if self.panel.flaps_1_sw != None:        
            self.ui.rb_flaps_1.setChecked(self.panel.flaps_1_sw == 1)
            self.ui.rb_flaps_2.setChecked(self.panel.flaps_2_sw == 1)
            self.ui.txt_gear.setText(GEAR_TEXT[self.panel.gear_sw])
            self.ui.chk_brake.setChecked(self.panel.brake_sw)
            for idx, pot in enumerate(self.pots):
                pot.setValue(int(self.panel.pots[idx]))
        else:
            print("switches not yet instantiated")
            self.sleep_func(.1)

        