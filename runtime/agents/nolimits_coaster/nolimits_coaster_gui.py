"""
nolimits_coastergui.py

"""

import os
import sys
import logging
#  from coaster_gui_defs import *
from PyQt5 import QtCore, QtGui, QtWidgets,  uic


from agents.ride_state import RideState
from agents.agent_gui_base import AgentGuiBase
import common.gui_utils as gutil
from common.kb_sleep import kb_sleep

ui, base = uic.loadUiType("agents/nolimits_coaster/nolimits_coaster_gui.ui")


log = logging.getLogger(__name__)

class frame_gui(QtWidgets.QFrame, ui):
    def __init__(self, parent=None):
        super(frame_gui, self).__init__(parent)
        self.setupUi(self)

class AgentGui(AgentGuiBase):

    def __init__(self, frame, proxy):
        self.ui = frame_gui(frame)
        self.lbl_pc_conn_status = [ self.ui.lbl_pc_conn_status_0, self.ui.lbl_pc_conn_status_1,
              self.ui.lbl_pc_conn_status_2, self.ui.lbl_pc_conn_status_3, self.ui.lbl_pc_conn_status_4]

        self.park_path = []
        self.park_names = []
        self.seat = []
        self._park_callback = None
        self.current_park = 0
        self.is_scrolling = False

        self.is_activated = False
        self.sleep_func = kb_sleep
        
        # configure signals
        self.ui.btn_dispatch.clicked.connect(proxy.dispatch_pressed)
        self.ui.btn_pause.clicked.connect(proxy.pause_pressed)
        self.ui.btn_reset_rift.clicked.connect(proxy.reset_vr)

        # Create custom buttons
        self.custom_btn_dispatch = gutil.CustomButton( self.ui.btn_dispatch, ('white','darkgreen'), ('black', 'lightgreen'), 10, 0) 
        self.custom_btn_pause = gutil.CustomButton( self.ui.btn_pause, ('black','orange'), ('black', 'yellow'), 10, 0) 
        # self.ui.btn_pause.setStyleSheet("background-color: orange;  border-radius:10px; border: 0px;QPushButton::pressed{background-color :yellow; }")
        self.show_state_change(RideState.NON_SIM_MODE, self.is_activated) # update buttons

        self.read_parks()  # load cmb_select_ride 
        self.report_coaster_status("Starting software!black")
        log.info("Agent GUI initialized")

    def set_rc_label(self, info):
        gutil.set_text(self.ui.lbl_remote_status, info[0], info[1])
        
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
       
    def set_seat(self, seat):
        if seat != '':
           log.info("seat set to %d", int(seat))

    def read_parks(self):
        try:
            path = os.path.abspath('agents/nolimits_coaster/coaster_parks.cfg')
            log.debug("Path to coaster parks: %s", path)
            with open(path) as f:
                parks = f.read().splitlines()
                for park in parks:
                    p = park.split(',')
                    self.park_path.append(p[0]) 
                    self.seat.append(p[1])
                    #  print park
                    p = p[0].split('/')
                    p = p[len(p)-1]
                    #  print p,
                    self.park_names.append(p.split('.')[0])
            log.debug("Available rides are:\n  %s", ','.join(p for p in self.park_names))
            self.ui.cmb_select_ride.addItems(self.park_names)
            self.ui.cmb_select_ride.currentIndexChanged.connect(self._park_selection_changed)
        except Exception as e:
            log.error("Unable to load parks, (error %s)", e)

    def select_ride_callback(self, cb):
        self._park_callback = cb

    def _park_selection_changed(self, value):
        if not self.is_scrolling: # ignore if encoder is pressed 
            self._park_by_index(value)

    def _park_by_index(self, idx):
        # print idx, self.park_path[idx]
        #  print "park by index", idx, self.current_park, idx == self.current_park
        if idx != self.current_park and self._park_callback != None:
            log.info("loading park %s", self.park_names[idx])
            # load park in pause mode, this will unpuase when park is loaded
            self._park_callback(True, self.park_path[idx], self.seat[idx])
            self.current_park = idx

    def get_selected_park(self): 
        return None

    def scroll_parks(self, dir):
        count = self.ui.cmb_select_ride.count()
        index = self.ui.cmb_select_ride.currentIndex()
        self.is_scrolling = True # flag to supress selection until encoder released
        if dir == '1':
            if index < count - 1:
                self.ui.cmb_select_ride.setCurrentIndex(index+1)
        elif dir == '-1':
            if index > 0:
                self.ui.cmb_select_ride.setCurrentIndex(index-1)
        print("scroll parks, dir=", dir,  "index = ", index)
        self.is_scrolling = False

    def show_parks(self, isPressed):
        # todo ignore if input tab not active 
        print("\nshow parks, pressed=", isPressed)
        if isPressed == 'False': 
            # here when encoder switch is released
            self._park_by_index(self.ui.cmb_select_ride.currentIndex())
        """
           if self.is_parklist_focused == False:
              #open pop down list
              self.park_listbox.focus_set()
              self.park_listbox.event_generate('<Button-1>')
        else:  
            if self.is_parklist_focused == True:
                # print "select item here" 
                self.park_listbox.event_generate('<Return>')
            else:
               log.warning("Unhandled state in Show_parks, pressed=%d", isPressed) # , "is open = ", self.is_parklist_focused
        """
        
    def hide_parks_dialog(self):
         self.top.destroy()

    def set_activation(self, is_enabled):
        #  print(("is activated in gui set to ", is_enabled))
        if is_enabled:
            self.is_activated = True
            self.ui.cmb_select_ride.setEnabled(False)
        else:
            self.is_activated = False
            self.ui.cmb_select_ride.setEnabled(True)

    def emergency_stop(self):
        log.warning("legacy emergency stop callback")
        self.deactivate()

    def show_activated(self, state):
        self.show_state_change(state, True)

    def show_deactivated(self, state):
        self.show_state_change(state, False)

    def temperature_status_changed(self, status):
        gutil.set_text(self.ui.lbl_temperature_status, status[0], status[1])

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
                # self.custom_btn_pause.set_attributes(True, False, "Prop Platform")  # enabled, not checked

        elif new_state == RideState.RUNNING:
            self.custom_btn_dispatch.set_attributes(False, True, 'Dispatched')  # not enabled, checked
            self.custom_btn_pause.set_attributes(True, False, "Pause")  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Coaster is Running", "green")            
        elif new_state == RideState.PAUSED:
            self.custom_btn_dispatch.set_attributes(False, True)  # not enabled, checked
            self.custom_btn_pause.set_attributes(True, True, "Continue")  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Coaster is Paused", "orange")
        elif new_state == RideState.EMERGENCY_STOPPED:
            self.custom_btn_dispatch.set_attributes(False, True)  # not enabled, checked
            self.custom_btn_pause.set_attributes(False, True, 'E-Stopped')  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Emergency Stop", "red")
        elif new_state == RideState.NON_SIM_MODE:
            self.custom_btn_dispatch.set_attributes(False, True)  # not enabled, checked
            self.custom_btn_pause.set_attributes(False, False)  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Coaster is resetting", "blue")

    def set_button_style(self, object, is_enabled, is_checked=None, text=None):
        if text != None:
           object.setText(text)
        if is_checked!= None:
           object.setCheckable(True)
           object.setChecked(is_checked)
        if is_enabled != None:
           object.setEnabled(is_enabled)
           