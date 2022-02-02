"""
  simple_input.py
"""
import sys
#  from simple_input_gui_defs import *
from PyQt5 import QtCore, QtGui, QtWidgets
from clients.test_client.simple_input_gui_defs import Ui_Frame
from clients.client_api import ClientApi

class InputInterface(ClientApi):

    def __init__(self):
        super(InputInterface, self).__init__()
        self.name  = "Simple test Client"
        self.is_normalized = True # transform value extents are -1 to +1

    def init_gui(self, frame):
        self.ui = Ui_Frame()
        self.ui.setupUi(frame)
        self.frame = frame
        self.sliders = [self.ui.sld_x_0, self.ui.sld_y_1,self.ui.sld_z_2,self.ui.sld_roll_3,
                                  self.ui.sld_pitch_4,self.ui.sld_yaw_5]
        self.ui.sld_x_0.valueChanged.connect(lambda: self.move_slider_changed(0))
        self.ui.sld_y_1.valueChanged.connect(lambda: self.move_slider_changed(1))
        self.ui.sld_z_2.valueChanged.connect(lambda: self.move_slider_changed(2))
        self.ui.sld_roll_3.valueChanged.connect(lambda: self.move_slider_changed(3))
        self.ui.sld_pitch_4.valueChanged.connect(lambda: self.move_slider_changed(4))
        self.ui.sld_yaw_5.valueChanged.connect(lambda: self.move_slider_changed(5))

        self.ui.btn_mid_pos.clicked.connect(self.set_mid_pos)

    def move_slider_changed(self, sender_id):
        try:
            value = self.sliders[sender_id].value()
            self.transform[sender_id] = float(value) *.01
        except Exception as e:
            log.error("Client input error: %s", e)

    def update_sliders(self):
        for idx, val in enumerate(self.transform):
            self.sliders[idx].setValue(int(self.transform[idx]*100))

    def set_mid_pos(self):
        self.transform = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.update_sliders()

    def begin(self, cmd_func, limits, pc_address):
        self.cmd_func = cmd_func
        self.limits = limits  # note limits are in mm and radians

