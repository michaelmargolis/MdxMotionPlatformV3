# Test Sim 

import sys
import os

from multiprocessing import Process, Queue
import traceback

from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox

try:
    import SimpleSims.spacenavigator as sn # 6 dof mouse
except:
    import spacenavigator as sn # 6 dof mouse


DATA_PERIOD = 50  # ms between updates

slider_increments = (5)*6  # todo for slow moves

qtcreator_file  = "SimpleSims\TestSim.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons

global_queue = Queue()

class Sim():
    def __init__(self, sleep_func, interval_ms = 40):
        
        self.is_connected = False
        self.name = "Test Sim"
        global global_queue
        self.data_Q = global_queue
    
    def __del__(self):
        self.win.close()
        self.app.exit()  
    
    def set_norm_factors(self, norm_factors):
        # values for each element that when multiplied will normalize data to a range of +- 1 
        self.norm_factors = norm_factors
    
    def set_state_callback(self, callback):
        self.state_callback = callback

    def load(self, loader):
        # ignore loader arg, create QT window
        self.app = QtWidgets.QApplication(sys.argv)
        self.win = MainWindow()        
        self.win.show()
        self.app.exec_()
        self.connect()
  
    def connect(self):
        self.is_connected = True

    def is_connected(self):
        return self.is_connected         

    def run(self):
        print("run")  

    def pause(self):
        print("pause")  
        
    def read(self):
        while self.data_Q.qsize() > 1:
            ignored = self.data_Q.get()
            if ignored == 'exit':
                sys.exit()
        if self.data_Q.qsize() > 0:
            transform = self.data_Q.get()
            if transform == 'exit':
                sys.exit()
            print("debg in read", transform)
            if transform is not None:
                return transform 
        return (0,0,0,0,0,0)
            
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        global global_queue
        self.data_Q = global_queue
        self.timer_data_update = None
        self.is_ready = False # True when platform config is loaded
        self.sn_avail = False  # space mouse
        self.time_interval = DATA_PERIOD / 1000.0
        self.slider_values = [0]*6  # the actual slider percents (-100 to 100)
        self.lagged_slider_values = [0]*6  # values used for sending to festo

        # configures
        self.configure_timers()
        self.configure_signals()
        self.configure_defaults()
        self.configure_buttons()
    
    def closeEvent(self, event):
       self.data_Q.put("exit")
    
    def configure_timers(self):
        self.timer_data_update = QtCore.QTimer(self) # timer services muscle pressures and data
        self.timer_data_update.timeout.connect(self.data_update)
        self.timer_data_update.start(int(DATA_PERIOD / 2)) # run faster than update period

    def configure_signals(self):
        self.ui.btn_centre.clicked.connect(self.centre_pos)
        self.ui.btn_load_pos.clicked.connect(self.load_pos)

    def configure_defaults(self):
        if len(sn.list_devices()) > 0:
            self.ui.txt_spacemouse.setText(sn.list_devices()[0])
        else:
            self.ui.txt_spacemouse.setText("Not found")
        self.sn_avail = sn.open()

    def configure_buttons(self):  
        #  button groups
        self.mouse_rbuttons = [self.ui.rb_m_off, self.ui.rb_m_inc, self.ui.rb_m_abs]
        self.mouse_btn_group = QtWidgets.QButtonGroup()
        for i in range(len(self.mouse_rbuttons)):
           self.mouse_btn_group.addButton(self.mouse_rbuttons[i], i)
           
        self.transfrm_sliders = [self.ui.sld_0, self.ui.sld_1, self.ui.sld_2, self.ui.sld_3, self.ui.sld_4, self.ui.sld_5  ]
        self.lag_indicators = [self.ui.pg_0, self.ui.pg_1, self.ui.pg_2, self.ui.pg_3, self.ui.pg_4, self.ui.pg_5]
       
    def data_update(self):
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
        transform = [x * .01 for x in self.lagged_slider_values]
        if self.data_Q:
            self.data_Q.put(transform)
  
    def get_mouse_transform(self):
        # returns list of normalized floats
        state = sn.read()
        transform = [state.x, state.y, state.z, state.roll, state.pitch, state.yaw]
        return transform
  
    def centre_pos(self):
        for slider in self.transfrm_sliders:
            slider.setValue(0)

    def load_pos(self):
        for idx, slider in enumerate(self.transfrm_sliders):
            if( idx == 2):
                slider.setValue(-100)
            else:
                slider.setValue(0)

if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()        
    win.show()
    app.exec_() #mm added underscore

    win.close()
    app.exit()  
    sys.exit()
