# space_coaster_gui.py

import logging
import common.gui_utils as gutil
from PyQt5 import QtCore, QtGui, QtWidgets, uic

from agents.ride_state import RideState
from agents.agent_gui_base import AgentGuiBase
import common.gui_utils as gutil

log = logging.getLogger(__name__)

qt_gui_ui = "agents/space_coaster/space_coaster_gui.ui"
ui, base = uic.loadUiType(qt_gui_ui)

class frame_gui(QtWidgets.QFrame, ui):
    def __init__(self, parent=None):
        super(frame_gui, self).__init__(parent)
        self.setupUi(self)

class AgentGui(AgentGuiBase):
    def __init__(self, frame, proxy):

        self.ui = frame_gui(frame)

        self.lbl_pc_conn_status = [ self.ui.lbl_pc_conn_status_0, self.ui.lbl_pc_conn_status_1,
              self.ui.lbl_pc_conn_status_2, self.ui.lbl_pc_conn_status_3, self.ui.lbl_pc_conn_status_4]
        # configure signals
        self.ui.btn_dispatch.clicked.connect(proxy.dispatch_pressed)
        self.ui.btn_pause.clicked.connect(proxy.pause_pressed)
        self.ui.btn_reset_rift.clicked.connect(proxy.reset_vr)

        # Create custom buttons
        self.custom_btn_dispatch = gutil.CustomButton( self.ui.btn_dispatch, ('white','darkgreen'), ('black', 'lightgreen'), 10, 0) 
        self.custom_btn_pause = gutil.CustomButton( self.ui.btn_pause, ('black','orange'), ('black', 'yellow'), 10, 0) 
        # self.ui.btn_pause.setStyleSheet("background-color: orange;  border-radius:10px; border: 0px;QPushButton::pressed{background-color :yellow; }")
        self.show_state_change(RideState.NON_SIM_MODE, False) # update buttons
        
        self.report_coaster_status("Starting software!black")

        log.info("Agent GUI initialized")

    def set_rc_label(self, info):
        gutil.set_text(self.ui.lbl_remote_status, info[0], info[1])
        
    def show_activated(self, state):
        self.show_state_change(state, True)

    def show_deactivated(self, state):
        self.show_state_change(state, False)

    def report_coaster_status(self, text):
        # msg string format is: text!color
        text,color = text.split('!')
        self.coaster_status_str = format("%s,%s" % (text,color))
        gutil.set_text(self.ui.lbl_coaster_status, text, color)

    def report_connection_status(self, index, pc_str, text):
        # msg string format is: text!color
        text = pc_str + ' ' + text
        text,color = text.split('!')
        gutil.set_text(self.lbl_pc_conn_status[index], text, color)

    def report_sync_status(self, text, color):
             gutil.set_text(self.lbl_sync_status, text, color)

    def detected_remote(self, info):
        # fixme - is this needed?
        if "Detected Remote" in info:
            gutil.set_text(self.ui.lbl_remote_status, info, "green")
        elif "Looking for Remote" in info:
            gutil.set_text(self.ui.lbl_remote_status, info, "orange")
        else:
             gutil.set_text(self.ui.lbl_remote_status, info, "red")

    def intensity_status_changed(self, intensity):
       gutil.set_text(self.ui.lbl_intensity_status, intensity[0], intensity[1])


    def show_state_change(self, new_state, isActivated):
        # print("Coaster state changed to ", RideState.str(new_state), str(isActivated))
        log.debug("Coaster state changed to: %s (%s)", RideState.str(new_state), "Activated" if isActivated else "Deactivated")
        if new_state == RideState.READY_FOR_DISPATCH:
            if isActivated:
                log.debug("Coaster is Ready for Dispatch")
                self.custom_btn_dispatch.set_attributes(True, False, 'Dispatch')  # enabled, not checked
                self.custom_btn_pause.set_attributes(True, False, 'Pause')  # enabled, not checked
                gutil.set_text(self.ui.lbl_coaster_status, "Coaster is Ready for Dispatch", "green")
                # self.set_button_style(self.ui.btn_pause, True, False, "Pause")  # enabled, not checked
            else:
                log.debug("Coaster at Station but deactivated")
                self.custom_btn_dispatch.set_attributes(False, False, 'Dispatch')  # not enabled, not checked
                gutil.set_text(self.ui.lbl_coaster_status, "Coaster at Station but deactivated", "orange")
                self.custom_btn_pause.set_attributes(True, False, "Prop Platform")  # enabled, not checked
            self.set_button_style(self.ui.btn_reset_rift, True, False)  # enabled, not checked

        elif new_state == RideState.RUNNING:
            self.custom_btn_dispatch.set_attributes(False, True, 'Dispatched')  # not enabled, checked
            self.custom_btn_pause.set_attributes(True, False, "Pause")  # enabled, not checked
            self.set_button_style(self.ui.btn_reset_rift, True, False)  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Coaster is Running", "green")
            
        elif new_state == RideState.PAUSED:
            self.custom_btn_dispatch.set_attributes(False, True)  # not enabled, checked
            self.custom_btn_pause.set_attributes(True, True, "Continue")  # enabled, not checked
            self.set_button_style(self.ui.btn_reset_rift, True, False)  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Coaster is Paused", "orange")
        elif new_state == RideState.EMERGENCY_STOPPED:
            self.custom_btn_dispatch.set_attributes(False, True)  # not enabled, checked
            self.custom_btn_pause.set_attributes(False, True)  # enabled, not checked
            self.set_button_style(self.ui.btn_reset_rift, True, False)  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Emergency Stop", "red")
        elif new_state == RideState.NON_SIM_MODE:
            self.custom_btn_dispatch.set_attributes(False, True)  # not enabled, checked
            self.custom_btn_pause.set_attributes(False, False)  # enabled, not checked
            self.set_button_style(self.ui.btn_reset_rift, True, False)  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Coaster is resetting", "blue")

    def set_button_style(self, object, is_enabled, is_checked=None, text=None):
        if text != None:
           object.setText(text)
        if is_checked!= None:
           object.setCheckable(True)
           object.setChecked(is_checked)
        if is_enabled != None:
           object.setEnabled(is_enabled)
