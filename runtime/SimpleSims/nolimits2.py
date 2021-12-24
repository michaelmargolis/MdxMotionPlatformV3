# sim class for NoLimits2
from SimpleSims.nl2_simple_itf import CoasterInterface
import os
import logging as log
import traceback

class Sim():
    def __init__(self, sleep_func, interval_ms = 25):
        self.sleep_func = sleep_func
        self.interval_ms = interval_ms
        self.is_connected = False
        self.is_paused = False
        self.norm_factors = [1, 1, 1, 1, 1, 1]
        self.name = "NoLimits2"
        self.coaster = None

    def __del__(self):
        pass
    
    def set_norm_factors(self, norm_factors):
        # values for each element that when multiplied will normalize data to a range of +- 1 
        self.norm_factors = norm_factors
    
    def set_state_callback(self, callback):
        self.state_callback = callback
        
    def load(self, loader):
        try:
            log.info("Starting NoLimits2 executing: " + loader)
            # os.startfile(r"C:\Users\memar\Desktop\Vr\NoLimits 2.lnk")
            os.startfile(loader)
            return("loading...") 
        except Exception as e:
            print(e)
            return(str(e))            
   
    def connect(self):
        pass

    def run(self):
        self.coaster.dispatch()
        self.is_paused = False

    def pause(self):
        self.is_paused = not self.is_paused
        self.coaster.set_pause(self.is_paused)
        
    def read(self):
        try:
            xform = self.coaster.get_telemetry(1)
            return xform
        except Exception as e:
            print("in read", str(e))
            return (0,0,0,0,0,0)

