"""
Python Coaster client GUI for pyqt

This version requires NoLimits attraction license and NL ver 2.5.3.4 or later
"""

import os
import sys
#  from coaster_gui_defs import *
from PyQt5 import QtCore, QtGui, QtWidgets
from coaster.coaster_gui_defs import Ui_Frame

sys.path.insert(0, './common')
from ride_state import RideState
import gui_utils as gutil

import logging
log = logging.getLogger(__name__)

class CoasterGui(object):

    def __init__(self, dispatch, pause, reset):
        self.dispatch = dispatch
        self.pause = pause
        self.reset = reset
        # self.activate_callback_request = activate_callback_request
        # self.quit = quit_callback
        self.park_path = []
        self.park_name = []
        self.seat = []
        self._park_callback = None
        self.current_park = 0
        self.ui = None
        self.is_activated = False

    def init_gui(self, frame):
        self.ui = Ui_Frame()
        self.ui.setupUi(frame)
        
        # configure signals
        self.ui.btn_dispatch.clicked.connect(self.dispatch)
        self.ui.btn_pause.clicked.connect(self.pause)
        self.ui.btn_reset_rift.clicked.connect(self.reset)

        self.read_parks()  # load cmb_park_listbox
        # self.set_button_style(self.ui.btn_deactivate, False, True, "Deactivated")  # disabled, checked
        log.info("Client GUI initialized")

    def set_seat(self, seat):
        if seat != '':
           log.info("seat set to %d", int(seat))

    def read_parks(self):
        try:
            path = os.path.abspath('CoasterParks/parks.cfg')
            log.info("Path to coaster parks: %s", path)
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
                    self.park_name.append(p.split('.')[0])
            log.info("Available parks are:\n  %s", self.park_name)
            self.ui.cmb_park_listbox.addItems(self.park_name)
            self.ui.cmb_park_listbox.currentIndexChanged.connect(self._park_selection_changed)
        except:
            e = sys.exc_info()[0]
            log.error("Unable to load parks, (error %s)", e)

    def set_park_callback(self, cb):
        self._park_callback = cb

    def _park_selection_changed(self, value):
        self._park_by_index(value)

    def _park_by_index(self, idx):
        # print idx, self.park_path[idx]
        #  print "park by index", idx, self.current_park, idx == self.current_park
        if idx != self.current_park and self._park_callback != None:
            log.info("loading park %s", self.park_name[idx])
            # load park in pause mode, this will unpuase when park is loaded
            self._park_callback(True, self.park_path[idx], self.seat[idx])
            self.current_park = idx

    def get_selected_park(self): 
        return None

    def scroll_parks(self, dir):
        self.park_listbox.event_generate(dir) 
        #  print "scroll parks, dir=", dir, "is open = ", self.is_parklist_focused

    def show_parks(self, isPressed):
        # todo ignore if input tab not active 
        #print "\nshow parks, pressed=", isPressed, "is open = ", self.is_parklist_focused
        if isPressed == 'True':
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

    def hide_parks_dialog(self):
         self.top.destroy()

    def set_activation(self, is_enabled):
        print(("is activated in gui set to ", is_enabled))
        if is_enabled:
            self.is_activated = True
            self.ui.cmb_park_listbox.setEnabled(False)
        else:
            self.is_activated = False
            self.ui.cmb_park_listbox.setEnabled(True)

    def set_coaster_status_label(self, status):
        #  print status
        gutil.set_text(self.ui.lbl_coaster_status, status[0], status[1])
        
    def set_coaster_connection_label(self, status):
        gutil.set_text(self.ui.lbl_coaster_connection, status[0], status[1])

    #  def chair_status_changed(self, status):
    #      gutil.set_text(self.ui.lbl_festo_status, status[0], status[1])

    def temperature_status_changed(self, status):
        gutil.set_text(self.ui.lbl_temperature_status, status[0], status[1])

    def intensity_status_changed(self, status):
        gutil.set_text(self.ui.lbl_intensity_status, status[0], status[1])

    def set_remote_status_label(self, status):
        gutil.set_text(self.ui.lbl_remote_status, status[0], status[1])

    def hotkeys(self, event):
        print("pressed", repr(event.char))
        if event.char == 'd':  self.dispatch()
        if event.char == 'p':  self.pause()
        if event.char == 'r':  self.reset()
        if event.char == 'e':  self.emergency_stop()

    def process_state_change(self, new_state, isActivated):
        log.debug("Coaster state changed to: %s (%s)", RideState.str(new_state), "Activated" if isActivated else "Deactivated")
        if new_state == RideState.READY_FOR_DISPATCH:
            if isActivated:
                log.debug("Coaster is Ready for Dispatch")
                self.set_button_style(self.ui.btn_dispatch, True, False)  # enabled, not checked
                gutil.set_text(self.ui.lbl_coaster_status, "Coaster is Ready for Dispatch", "green")
                self.set_button_style(self.ui.btn_pause, True, False, "Pause")  # enabled, not checked
            else:
                log.debug("Coaster at Station but deactivated")
                self.set_button_style(self.ui.btn_dispatch, False, False)  # not enabled, not checked
                gutil.set_text(self.ui.lbl_coaster_status, "Coaster at Station but deactivated", "orange")
                self.set_button_style(self.ui.btn_pause, True, False, "Prop Platform")  # enabled, not checked
            self.set_button_style(self.ui.btn_reset_rift, True, False)  # enabled, not checked

        elif new_state == RideState.RUNNING:
            self.set_button_style(self.ui.btn_dispatch, False, True)  # not enabled, checked
            self.set_button_style(self.ui.btn_pause, True, False, "Pause")  # enabled, not checked
            self.set_button_style(self.ui.btn_reset_rift, True, False)  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Coaster is Running", "green")
            
        elif new_state == RideState.PAUSED:
            self.set_button_style(self.ui.btn_dispatch, False, True)  # not enabled, checked
            self.set_button_style(self.ui.btn_pause, True, True, "Continue")  # enabled, not checked
            self.set_button_style(self.ui.btn_reset_rift, True, False)  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Coaster is Paused", "orange")
        elif new_state == RideState.EMERGENCY_STOPPED:
            self.set_button_style(self.ui.btn_dispatch, False, True)  # not enabled, checked
            self.set_button_style(self.ui.btn_pause, False, True)  # enabled, not checked
            self.set_button_style(self.ui.btn_reset_rift, True, False)  # enabled, not checked
            gutil.set_text(self.ui.lbl_coaster_status, "Emergency Stop", "red")
        elif new_state == RideState.RESETTING:
            self.set_button_style(self.ui.btn_dispatch, False, True)  # not enabled, checked
            self.set_button_style(self.ui.btn_pause, False, False)  # enabled, not checked
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