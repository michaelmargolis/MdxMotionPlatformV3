"""
    RemoteControl.py 
    Provides interface to serial and networked remote controllers
"""

from RemoteControls.serial_remote import SerialRemote
from RemoteControls.udp_remote import UdpRemote

class RemoteControl(object):
   # default uses serial remote with UDP remote disabled
    def __init__(self, actions, serial=True, UDP=False):
        self.serial = serial
        self.UDP = UDP
        
        self.actions = actions
        """
                  {'detected remote': self.detected_remote, 'activate': self.controller.activate,
                   'deactivate': self.controller.deactivate, 'pause': self.controller.pause,
                   'dispatch': self.controller.dispatch, 'reset': self.controller.reset_vr,
                   'emergency_stop': self.controller.emergency_stop, 'intensity' : self.controller.set_intensity
                   # ,'show_parks' : self.show_parks,'scroll_parks' : self.scroll_parks}
                   }
        """
        if self.serial:
            self.SerialRemoteControl = SerialRemote(self.actions)
        if self.UDP:
            self.UdpRemoteControl = UdpRemote(self.actions)

    def send(self, to_send):
        if self.serial:
            self.SerialRemoteControl.send(to_send)
        if UDP:
            self.UdpRemoteControl.send(to_send) 

    def service(self):
        if self.serial:
            self.SerialRemoteControl.service()
        if self.UDP:
            self.UdpRemoteControl.service() 
    """
    def detected_remote(self, info):
        if "Detected Remote" in info:
            self.set_status_label((info, "green"))
        elif "Looking for Remote" in info:
            self.set_status_label((info, "orange"))
        else:
            self.set_status_label((info, "red"))
    """