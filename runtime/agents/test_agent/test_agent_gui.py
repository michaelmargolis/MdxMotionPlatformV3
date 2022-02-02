"""
  test_agent_gui.py
"""
import logging
import common.gui_utils as gutil
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from agents.agent_gui_base import AgentGuiBase
from agents.agent_base import  RemoteMsgProtocol
from platform_config import cfg
from common.udp_tx_rx import UdpSend

ui, base = uic.loadUiType("agents/test_agent/simple_input_gui.ui")

log = logging.getLogger(__name__)


class frame_gui(QtWidgets.QFrame, ui):
    def __init__(self, parent=None):
        super(frame_gui, self).__init__(parent)
        self.setupUi(self)

class AgentGui(AgentGuiBase):
    def __init__(self, frame, proxy):
        self.ui = frame_gui(frame)

        self.sliders = [self.ui.sld_x_0, self.ui.sld_y_1,self.ui.sld_z_2,self.ui.sld_roll_3,
                                  self.ui.sld_pitch_4,self.ui.sld_yaw_5]
        self.ui.sld_x_0.valueChanged.connect(lambda: self.move_slider_changed(0))
        self.ui.sld_y_1.valueChanged.connect(lambda: self.move_slider_changed(1))
        self.ui.sld_z_2.valueChanged.connect(lambda: self.move_slider_changed(2))
        self.ui.sld_roll_3.valueChanged.connect(lambda: self.move_slider_changed(3))
        self.ui.sld_pitch_4.valueChanged.connect(lambda: self.move_slider_changed(4))
        self.ui.sld_yaw_5.valueChanged.connect(lambda: self.move_slider_changed(5))

        self.ui.btn_mid_pos.clicked.connect(self.set_mid_pos)
        self.transform = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.event_address = ('127.0.0.1', cfg.FIRST_AGENT_PROXY_EVENT_PORT)
        self.event_sender = UdpSend()

    def move_slider_changed(self, sender_id):
        try:
            value = self.sliders[sender_id].value()
            self.transform[sender_id] = float(value) *.01
            self.update()
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

    def detected_remote(self, info):
        pass
        
    def update(self):
        event = RemoteMsgProtocol.encode(0, 0, 0, False, self.transform, "", "")
        self.event_sender.send(event.encode('utf-8'), self.event_address)