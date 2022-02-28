# sim class for dcs flight simulator
from SimpleSims.dcs_gateway import DCS_gateway as dcs
import os
import time
import logging as log
import traceback
       
class Sim():
    def __init__(self, sleep_func,  interval_ms = 25):
        self.sleep_func = sleep_func
        self.interval_ms = interval_ms
        self.gateway = None
        self.is_connected = False
        self.norm_factors = [1, 1, 1, 1, 1, 1] # these are updated in the dcs gateway
        self.name = "DCS"
        self.dcs = dcs()

    def __del__(self):
        pass
    
    def set_norm_factors(self, norm_factors):
        # values for each element that when multiplied will normalize data to a range of +- 1 
        self.norm_factors = norm_factors
    
    def set_state_callback(self, callback):
        self.state_callback = callback

    def load(self, loader):
        try:
            log.info("Starting DCS executing: " + loader)
            os.startfile(loader)

        except Exception as e:
            print(e)
            return(str(e))            
   
    def connect(self):
        # returns string code or None if no error
        try:
            if self.dcs:
                self.dcs.listen()
                time.sleep(.1) # wait for at leat one  message
                if self.dcs.is_connected:
                    self.is_connected = True 
                    log.info("Connected to DCS")               
                    return None
                else:
                    return("Not connecting to DCS, is it running")
            else:
                return("DCS gateway not available") 
        except ConnectionError:
            #note that current gateway does not check if gateway is connected
            log.info("Not connecting, is DCS loaded? " + str(e)) 
            print(traceback.format_exc())
            return "Not connecting, is DCS loaded?"
        except Exception as e:
            log.info("DCS connect err: " + str(e)) 
            print(traceback.format_exc())
            return(str(e))

    def run(self):
        print("todo run")

    def pause(self):
        print("todo pause")
 
    def read(self):
        if self.dcs:
            return self.dcs.read()
        else:
            pass # fall through to return (0,0,0,0,0,0)
        return (0,0,0,0,0,0)