# calibration_graph.py

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

LVL = 64
HLVL = int(LVL* 1.5)
 
wipe_colors = (QtGui.QColor(HLVL, LVL, LVL), QtGui.QColor(LVL, HLVL, LVL), 
               QtGui.QColor(LVL, LVL, HLVL),QtGui.QColor(HLVL, HLVL, LVL))

class CalibrationGraph:
    def __init__(self, title):
        #window.setGeometry(100, 100, 600, 500)
        self.title = title
        #window.setWindowTitle(title)
        
    def begin(self, title,  nbr_cycles, steps_per_dir, nbr_columns, step_size):
        # pg.setConfigOption('background', 'w')
        # pg.setConfigOption('foreground', 'k')
        self.nbr_cycles = nbr_cycles
        self.steps_per_dir = steps_per_dir
        self.nbr_columns = nbr_columns
        self.step_size = int(step_size)
        self.data =  np.empty([2, nbr_cycles, steps_per_dir, nbr_columns])
        self.plt = pg.plot()
        self.plt.setWindowTitle(title)
        self.max_pressure = int((steps_per_dir-1)*step_size)
        self.plt.setXRange(0,self.max_pressure )
        self.plt.setYRange(0, 200)
        self.prev_cycle = 0
 
        # self.dummy_up, self.dummy_down = load_test_data(title)
        # print(self.dummy_up)
        
    def update(self, updown, cycle, step, values):
        """
        if updown == 0:
           values = self.dummy_up[cycle, step]
        else:
            values = self.dummy_down[cycle, step]
        """
        self.data[updown, cycle, int(step),:] = np.asarray(values, dtype = "int")

        # print("wha", step, self.data[updown, cycle, : step+1])
        x = []
        if updown == 0: # x increases
            for s in range(step+1):
                x.append(s * self.step_size)
        else:
            for s in range(step+1):
                x.append(self.max_pressure - (s * self.step_size))   
                
        colors = ['r','g', 'b', 'y', 'm', 'c']   
        for i in range(len(values)): 
            if cycle > 0:
                # dim previous plot
                self.plt.plot(x, self.data[updown, cycle-1, : step+1, i], pen = wipe_colors[(cycle-1) % 4])
            self.plt.plot(x, self.data[updown, cycle, : step+1, i], pen = colors[i])
            # print(i, colors[i], self.data[updown, cycle, :, i])
 
 
def load_test_data(fname):
    fname = 'PlatformCalibrate/PtoD_44.csv'
    import d_to_p_prep
    DtoP_prep = d_to_p_prep.D_to_P_prep(200) # argument is max distance
    up,down, weight, pressure_step = DtoP_prep.munge_file(fname)
    nbr_cycles, steps_per_dir, nbr_columns = np.shape(up)
    return up, down

import time 
def test(infname):
    # DtoP = d_to_p.D_to_P(200) # argument is max distance 
    DtoP_prep = d_to_p_prep.D_to_P_prep(200) # argument is max distance
    up,down, weight, pressure_step = DtoP_prep.munge_file(infname)
    # d_to_p = DtoP_prep.process_p_to_d(up, down, weight, pressure_step)
    graph = CalibrationGraph("test")
    nbr_cycles, steps_per_dir, nbr_columns = np.shape(up)
    graph.begin(infname,  nbr_cycles, steps_per_dir, nbr_columns, pressure_step)
    for cycle in range( nbr_cycles):
        for step in range(steps_per_dir):
            graph.update(0, cycle, step, up[cycle, step] )
            time.sleep(1)
    

if __name__ == '__main__':
    import d_to_p_prep
    import os
    
    path = os.getcwd()
    if os.path.basename(path) != 'PlatformCalibrate':
        print("run this from the PlatformCalibrate directory")
    else:
        path = '.' # location of csv input files
        files = [x for x in os.listdir(path) if x.startswith('PtoD_') and x.endswith('.csv') and not 'old' in x]
        inp = input("enter file index  to process " + str(files) + " return to exit ") 
        if inp != '':
            idx = int(inp)
            test(files[idx])

