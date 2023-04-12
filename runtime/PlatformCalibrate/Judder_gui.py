import sys
import numpy as np
import time 
import traceback
from collections import deque
from queue import Queue
import pyqtgraph as pg
from PyQt5 import QtWidgets, uic, QtCore, QtGui

from pyqtgraph import PlotWidget, ViewBox
from PyQt5.QtGui import QKeySequence

from scipy.signal import butter, filtfilt
import numpy as np

from Judder import Judder, Calibrate

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons

qtcreator_file  = "PlatformCalibrate/judder.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)

from PyQt5 import QtWidgets, uic
import sys

comport = "COM6"

def butter_highpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def butter_highpass_filter(data, cutoff, fs, order=5):
    b, a = butter_highpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data)
    return y
    
class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(qtcreator_file, self)
        self.judder = judder  
        self.config_signals()
        self.config_buffers()
        self.config_plot() 
        self.is_estopped = False
        judder.set_accel_mode('World')
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.service_judder)
        self.is_calibrating = False
        self.is_capturing = False
        self.timer.start(10) # show data at startup

        self.show()

    def config_plot(self):
        self.trace_names = ['X','Y','Z','Pulse start','Y1','Z1']
        self.trace_colors = ['r', 'g', 'y', 'b', 'm', 'c', 'w' ] # last color not used  

        self.minmax = [-1.4, 1.4]
        self.plotWidget.setTitle('Acceleration', **{'color': '#FFF', 'size': '14pt'})
        self.plotWidget.showGrid(x=True, y=True)
        self.plotWidget.setBackground((16,16,16))
        self.plotWidget.addLegend()
        if self.minmax  == None or self.minmax == 'A':
           self. plotWidget.enableAutoRange(axis=ViewBox.YAxis)
        else:    
            self.plotWidget.setYRange(self.minmax[0], self.minmax[1])
        self.curves = []    
        for i in range(self.nbr_traces):
            self.curves.append(self.plotWidget.plot(self.x, self.y, pen=(self.trace_colors[i]), name=self.trace_names[i]))        

    
    def config_signals(self):
        self.btn_start.clicked.connect(self.start) 
        self.btn_calibrate.clicked.connect(self.calibrate) 
        self.btn_save.clicked.connect(self.save)
        self.btn_save.setEnabled(False)
        self.btn_estop.clicked.connect(self.estop)
        self.btn_load_pos.clicked.connect(self.judder.load_pos)
        self.btn_centre.clicked.connect(self.judder.centre_pos)
    
    def config_buffers(self):
        self.x_size = 1200 # the max number of plot points to be displayed
        self.trace_data = [] # data displayed as plot traces
        self.nbr_traces = 4 # 3 plus state info
        self.out_data = []
        for i in range(self.nbr_traces):
           self.out_data.append([])  # data to be saved to csv file
        self.state_info = []
        for i in range( self.nbr_traces):       
            self.trace_data.append(deque([0.0] * self.x_size, self.x_size))
        self.x = np.linspace(-self.x_size/20, 0.0, self.x_size)
        self.y = np.zeros(self.x_size, dtype=float) 
    
    
    def service_judder(self):
        data = self.judder.get_data()
        if data:
            if self.is_capturing or not self.chk_pause.isChecked(): 
                #data = data[:-1]
                # print(data, len(data), self.nbr_traces)
                if len(data) == self.nbr_traces:
                  
                    out_data = []
                    for idx, t in enumerate(data):                  
                        val = float(data[idx])
                        self.trace_data[idx].append(val)
                        out_data.append(val)
                        if self.chk_filter.isChecked():                   
                             conditioned_signal = butter_highpass_filter(self.trace_data[idx], 2, 40, 5)
                             self.curves[idx].setData(self.x,  conditioned_signal) 
                        else:     
                            self.curves[idx].setData(self.x,  self.trace_data[idx])    
                        if self.is_capturing:    
                            self.out_data[idx].append(val)
 
        if self.is_capturing and not self.is_estopped:
            status = self.judder.service_state()
            if status:
                self.txt_info.setText(status)
                if status == 'COMPLETED':
                    self.done()
                
    def start(self):
        self.btn_save.setEnabled(False)
        self.chk_pause.setChecked(False)
        self.chk_pause.setEnabled(False)
        print('start Button Pressed')
        self.config_buffers()
        self.judder.start_capture()
        self.is_capturing = True
        self.plotWidget.setTitle('Recording Acceleration', **{'color': '#F00', 'size': '14pt'})
        self.timer.start(10)
    
    def done(self):
        # self.timer.stop()
        self.is_capturing = False
        self.plotWidget.setTitle('Acceleration', **{'color': '#FFF', 'size': '14pt'})
        self.btn_save.setEnabled(True)
        self.chk_pause.setEnabled(True)  
        self.chk_pause.setChecked(True)        
        
    def calibrate(self):
        if self.is_calibrating:
            self.btn_calibrate.setText("Calibrate")
            self.is_calibrating = False
            judder.set_accel_mode('World')
        else:
            self.btn_calibrate.setText("End Calibrate")
            self.is_calibrating = True
            judder.set_accel_mode('Calibrate')

    def save(self):
        try:
            data_len = len(self.out_data[0])
            # print(self.out_data[0])
            out_data = np.array(self.out_data)    
            # print(out_data.shape)
            """
            for idx, vals in enumerate(self.out_data):
                filtered = butter_highpass_filter(vals, 2, 40, 5)
                out_data = np.concatenate( (out_data, filtered)) 
            """                
            out = np.reshape(out_data, (self.nbr_traces, data_len))
            np.savetxt(self.txt_fname.text()+'.csv', out, fmt='%.4f', delimiter=",")
            """
            state_info =  np.array( self.state_info)
            print("shape", state_info.shape, out.shape)
            np.savetxt(self.txt_fname.text() + '_state.csv',state_info.flatten(), fmt='%.1f', delimiter=",")
            """
            self.btn_save.setEnabled(False)  
        except Exception as e:
            print(traceback.format_exc())
            print("Error saving data file, is it already open?", e)
            
            
    def estop(self):
        print('estop Button Pressed')
        self.judder.load_pos()
        self.is_capturing  = False
        self.is_estopped = True


if len(sys.argv) == 2:
   comport = sys.argv[1]
   
judder = Judder()
if not judder.connect_coms(comport):
    sys.exit()   
calibrate = Calibrate()         

app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()