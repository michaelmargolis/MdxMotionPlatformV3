# dynamics (was shape)

import traceback
import numpy as np
from dynamics_gui_defs import *

import logging
log = logging.getLogger(__name__)

class Dynamics(object):
    def __init__(self, frame_rate=0.05):
        self.frame_rate = frame_rate
        self.intensity = 1.0 #  factor to adjust final gain from remote control
        self.use_gui = False

    def init_gui(self, frame):
        self.ui = Ui_Frame()
        self.ui.setupUi(frame)
        self.use_gui = True
        self.intensity_sliders = [self.ui.sld_x_0, self.ui.sld_y_1,self.ui.sld_z_2,self.ui.sld_roll_3,
                                  self.ui.sld_pitch_4,self.ui.sld_yaw_5,self.ui.sld_master_6]
        self.ui.sld_x_0.valueChanged.connect(lambda: self.move_slider_changed(0))
        self.ui.sld_y_1.valueChanged.connect(lambda: self.move_slider_changed(1))
        self.ui.sld_z_2.valueChanged.connect(lambda: self.move_slider_changed(2))
        self.ui.sld_roll_3.valueChanged.connect(lambda: self.move_slider_changed(3))
        self.ui.sld_pitch_4.valueChanged.connect(lambda: self.move_slider_changed(4))
        self.ui.sld_yaw_5.valueChanged.connect(lambda: self.move_slider_changed(5))
        self.ui.sld_master_6.valueChanged.connect(lambda: self.move_slider_changed(6))
        self.ui.btn_reload_dynam.clicked.connect(self.read_config)
        self.ui.btn_save_dynam.clicked.connect(self.save_config)
        self.ui.btn_default_dynam.clicked.connect(self.default_config)
        
    def default_config(self):
        # These default values are overwritten with values in config file
        self.gains = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0])  # xyzrpy gains
        self.master_gain = 1.0
        if self.use_gui:
            self.update_sliders()

    def move_slider_changed(self, sender_id):
        value = self.intensity_sliders[sender_id].value()
        # print "slider", sender_id, "value is ", value *.01
        if sender_id < 6:
            self.gains[sender_id] = float(value) *.01
        elif sender_id == 6:
           self.master_gain =  float(value) *.01 

    def update_sliders(self):
        for idx, val in enumerate(self.gains):
            self.intensity_sliders[idx].setValue(int(self.gains[idx]*100))
        self.ui.sld_master_6.setValue(int(self.master_gain *100))

    def begin(self, range, config_fname):
        self.range = range
        self.default_config()
        self.config_fname = config_fname
        self.read_config()

    def set_gain(self, idx, value):
        self.gains[idx] = value
        #  print "in shape", idx, " gain set to ", value

    def set_master_gain(self, value):
        self.master_gain = float(value)
        #  print "in shape, master gain set to ", value

    def get_master_gain(self):
        return self.master_gain

    def set_intensity(self, value):
        #  expects float between 0 and 1.0
        self.intensity = value

    def get_intensity(self):
        return self.master_gain * self.intensity

    def get_overall_intensity(self):
        return self.master_gain * self.intensity
        
    def regulate(self, request):
    # returns real values adjusted for intensity and washout
        # print request
        # print "in filter", request, self.gains, self.master_gain
        r = np.multiply(request, self.gains) * self.master_gain * self.intensity

        np.clip(r, -1, 1, r)  # clip normalized values
        #  print "clipped", r
        """
        for idx, f in enumerate(self.washout_factor):
            #  if washout enabled and request is less than prev washed value, decay more
            if f != 0 and abs(request[idx]) < abs(self.prev_value[idx]):
                #  here if washout is enabled
                r[idx] =  self.prev_value[idx] * self.washout_factor[idx]
        self.prev_value = r       
        """
        #  convert from normalized to real world values
        r = np.multiply(r, self.range)  
        #print "real",r, self.range
        return r

    def read_config(self):
        # in this version we only read gains
        try:
            with open(self.config_fname) as f:
                lines = f.readlines()
                for line in lines:
                    fields = line.split(',')
                    if fields[0] == 'gains':
                       gains = fields[1:]
                       self.gains = np.array([float(i) for i in fields[1:-1]])
                       self.master_gain = float(fields[7])
            log.info("loaded gains from file %s", self.config_fname)
            self.update_sliders()
        except IOError:
            log.error("Unable to open gains config file %s, using defaults", self.config_fname)

    def save_config(self):
        try:
            with open(self.config_fname, "w") as outfile:
                outfile.write("# saved values for gain and washout\n")
                #generate an array with strings
                arrstr = np.char.mod('%.2f', self.gains)
                gain_str = ','.join(arrstr) + ',' + str(self.master_gain)
                outfile.write("gains," + gain_str)
        except Exception, e: 
            log.error("error saving gains to %s: %s", self.config_fname, e)