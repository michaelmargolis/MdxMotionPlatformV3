"""
  simple_input.py
"""

from client_api import ClientApi

from simple_input_gui_defs import *


InputParmType = 'normalized'


class InputInterface(ClientApi):

    def __init__(self, sleep_func):
        super(InputInterface, self).__init__(sleep_func)
        self.name  = "Simple test Client"
        if InputParmType == 'normalized':
            self.is_normalized = True

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
        value = self.sliders[sender_id].value()
        print("slider", sender_id, "value is ", value *.01)
        if sender_id < 6:
            self.levels[sender_id] = float(value) *.01
            print(self.levels)

    def update_sliders(self):
        for idx, val in enumerate(self.levels):
            self.sliders[idx].setValue(int(self.levels[idx]*100))

    def set_mid_pos(self):
        self.levels = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.update_sliders()

    def begin(self, cmd_func, move_func, limits):
        self.cmd_func = cmd_func
        self.move_func = move_func
        self.limits = limits  # note limits are in mm and radians



