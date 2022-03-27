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
import traceback

ui, base = uic.loadUiType("agents/test_agent/simple_input_gui.ui")

log = logging.getLogger(__name__)


class frame_gui(QtWidgets.QFrame, ui):
    def __init__(self, parent=None):
        super(frame_gui, self).__init__(parent)
        self.setupUi(self)

class AgentGui(AgentGuiBase):
    def __init__(self, frame, layout,  proxy):
        self.ui = frame_gui(frame)
        layout.addWidget(self.ui)

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
        self.event_address = ('127.0.0.1', cfg.AGENT_PROXY_EVENT_PORT)
        self.event_sender = UdpSend()
        
        self.ui.btn_animate.clicked.connect(self.start_animation)
        self.animation_timer = QtCore.QTimer(self.ui)
        self.animation_timer.timeout.connect(self.animation_update)
        self.is_animating = False

    def move_slider_changed(self, sender_id):
        try:
            value = self.sliders[sender_id].value()
            self.transform[sender_id] = float(value) *.01
            self.update()
        except Exception as e:
            log.error("Client input error: %s", e)
            print(traceback.format_exc())
            

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
        event = RemoteMsgProtocol.encode(0, 0, 0, 0, False, self.transform, "", "")
        self.event_sender.send(event.encode('utf-8'), self.event_address)

    def start_animation(self):
        if self.is_animating:
            self.animation_timer.stop()
            self.ui.btn_animate.setText("Animate")
            self.ui.btn_animate.setStyleSheet("background-color: light gray")
            self.is_animating = False
        else:
            self.interval_ms = int(self.ui.txt_interval.text())
            self.nbr_cycles = int(self.ui.txt_cycles.text())
            self.current_axis = 0
            self.nbr_steps = int(self.ui.txt_steps.text()) # steps should be multiple of 4 or some steps will be missed
            self.nbr_steps = self.nbr_steps - (self.nbr_steps % 4) # round down to neex multiple of 4 
            self.ui.txt_steps.setText(str( self.nbr_steps))
            self.ui.btn_animate.setText("Stop")
            self.ui.btn_animate.setStyleSheet("background-color: red")
            
            self.current_cycle = 0
            self.current_step = 0
            self.waveform = list(self.triangle(self.nbr_steps, 100))
            print("nbr steps", len(self.waveform))
            self.is_animating = True
            self.animation_timer.start(self.interval_ms) 
    
    def animation_update(self):
        print( "axis: ", self.current_axis,  "step index=", self.current_step,  end='')
        print( ", val=", self.waveform[self.current_step],"axis=",  self.current_axis)
        self.sliders[self.current_axis].setValue(self.waveform[self.current_step])
       
        self.current_step += 1
        if self.current_step > self.nbr_steps:
            self.current_step = 0
            self.current_axis  += 1
            if self.current_axis >= 6:
                self.current_axis = 0
                self.current_cycle += 1      
                if self.current_cycle >= self.nbr_cycles:
                    self.current_cycle = 0
                    self.animation_timer.stop()
                
         
    def triangle(self, steps, amplitude):
        section = steps // 4
        for direction in (1, -1):
            for i in range(section):
               yield round(i * (amplitude / section) * direction)
            for i in range(section):
               yield round((amplitude - (i * (amplitude / section))) * direction)
        yield 0