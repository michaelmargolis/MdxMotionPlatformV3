# sim class for dcs_gateway
from SimpleSims.dcs_gateway import DCS_gateway as dcs
import subprocess
import logging as log
import traceback
       
class Sim():
    def __init__(self, sleep_func,  interval_ms = 25):
        self.sleep_func = sleep_func
        self.interval_ms = interval_ms
        self.gateway = None
        self.is_connected = False
        self.norm_factors = [1, 1, 1, 1, 1, 1] # these are set in the gateway
        self.name = "DCS"
        self.dcs = dcs()

    def __del__(self):
        pass
    
    def set_norm_factors(self, norm_factors):
        # values for each element that when multiplied will normalize data to a range of +- 1 
        self.norm_factors = norm_factors
    
    def set_state_callback(self, callback):
        self.state_callback = callback

    def load(self):
        try:
            print("you could start DCS here")
            #subprocess.Popen([cmd])
            #os.startfile(line)
            return("loading...") 
        except Exception as e:
            print(e)
            return(str(e))            
   
    def connect(self):
        # returns string code or None if no error
        try:
            if self.dcs:
                self.dcs.listen()
                self.is_connected = True
                return None 
            else:
                return("Not connecting to DCS") 
        except ConnectionError:
            #note that current gateway does not check if gateway is connected
            return "Not connecting, is DCS loaded?"
        except Exception as e:
            log.info("DCS connect err: " + str(e)) 
            return(e)

    def run(self):
        print("todo run")

 
    def read(self):
        if self.dcs:
            return self.dcs.read()
        else:
            pass # fall through to return (0,0,0,0,0,0)
        return (0,0,0,0,0,0)