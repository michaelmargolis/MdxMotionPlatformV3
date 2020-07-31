"""
client_api.py
  
Base Class for Mdx platform clients 
all but the most basic clients will override these methods 

This module can become an abstract base class when all code is migrated to python 3
"""

class ClientApi(object):

    def __init__(self):
        # orientation is: x, y, z translations, roll, pitch , yaw
        self.transform = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.is_normalized = True  # set to false if client provides real world orientation values
        self.ride_state = None
        self.is_connected = False

    def init_gui(self, frame):
        """pass pyqt frame and add init code if using GUI"""
        pass

    def set_rc_label(self, label):
        """pass string with remote control text if supported by this client"""
        pass

    def intensity_status_changed(self, status):
        """pass string with ride intensity text if supported by this client"""
        pass

    def activate(self):
        """code to execute in client when platform is activated goes here"""
        pass

    def deactivate(self):
        """code to execute in client when platform is deactivated goes here"""
        pass

    def get_transform(self):
        """return list of xyzrpy float levels"""
        return self.transform

    def set_transform(self, transform):
        """set xyzrpy float levels"""
        self.transform = transform

    def get_ride_state(self):
        """return ride state"""
        return self.ride_state

    def set_ride_state(self, state):
        self.ride_state= state

    def service(self):
        """code to execute each frame prior to sending data to the platform"""  
        pass

    def reset_vr(self):
        """override this with code to reset vr headset"""
        pass

    def begin(self, cmd_func, move_func, limits, remote_addresses=None):
        """code to start the client goes here"""
        pass

    def set_address(self, address):
        # format of address is client dependent
        self.address = address

    def get_address(self):
        return self.address

    def connect(self):
        #  address must be set prior to connect
        return is_connected

    def is_connected(self):
        return is_connected

    def fin(self):
        """client exit code goes here"""
        pass

