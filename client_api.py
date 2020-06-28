"""
client_api.py
  
Base Class for Mdx platform clients 
all but the most basic clients will override these methods 

This module can become an abstract base class when the code is migrated to python 3
"""

class ClientApi(object):

    def __init__(self, sleep_func):
        self.sleep_func = sleep_func
        self.levels = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    def init_gui(self, frame):
        """pass pyqt frame and add init code if using GUI"""
        pass

    def set_rc_label(self, label):
        """pass string with remote control text if supported by this client"""
        pass

    def intensity_status_changed(self, status):
        """pass string with ride intensity text if supported by this client"""
        pass

    def chair_status_changed(self, chair_status):
        """pass string with ride status text if supported by this client"""
        pass

    def activate(self):
        """code to execute in client when platform is activated goes here"""
        pass

    def deactivate(self):
        """code to execute in client when platform is deactivated goes here"""
        pass

    def get_current_pos(self):
        """return list of xyzrpy float levels"""
        return self.levels
        
    def service(self):
        """code to execute each frame prior to sending data to the platform"""  
        pass

    def begin(self, cmd_func, move_func, limits):
        """code to start the client goes here"""
        pass

    def fin(self):
        """client exit code goes here"""
        pass

