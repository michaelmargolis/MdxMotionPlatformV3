# class for agent frame

from PyQt5 import QtCore, QtGui, QtWidgets, uic

# ui must be defined by the parent gui class

"""
todo this to replace code in agent gui

class frame_gui(QtWidgets.QFrame, ui):
    def __init__(self, parent=None):
        super(frame_gui, self).__init__(parent)
        self.ui.setupUi(self)
"""

# base class for agent GUI elements
class AgentGuiBase(object):
    def __init__(self, ui_defs, frame):
        self.frame = frame
        self.ui = frame_gui(frame)
    
    def set_rc_label(self, label):
        """pass string with remote control text if supported by this agent"""
        pass

    def intensity_status_changed(self, status):
        """pass string with ride intensity text if supported by this agent"""
        pass

    def ride_state_changed(self, state): # or status string?`
        pass

    def select_ride_callback(self, cb):
        pass # override this if ride can be select at runtime
        
    def report_connection_status(self, index, pc_str, text):
        pass 
        
    def report_coaster_status(self, text):
        pass # todo rename to report_ride_status

    def show_activated(self, state):
        """ platform activation state changed, can be used to update status string""" 
        pass 

    def show_parked(self):
        pass
    def show_deactivated(self, state):
        """ platform activation state changed, can be used to update status string""" 
        pass 
        
    def show_state_change(self, state, is_platform_activated):
        pass