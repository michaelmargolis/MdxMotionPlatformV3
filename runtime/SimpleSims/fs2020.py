# sim class for FS 2020
from SimConnect import *
import subprocess
import logging as log
import traceback

class Sim():
    def __init__(self, sleep_func,  interval_ms = 25):
        self.sleep_func = sleep_func
        # Create SimConnect link
        self.interval_ms = interval_ms
        self.sm = None
        self.is_connected = False
        self.norm_factors = [.01, .01, .01, 1, 1, 1]
        self.name = "MS FS2020"

    def __del__(self):
        if self.sm:
            self.sm.exit()
    
    def set_norm_factors(self, norm_factors):
        # values for each element that when multiplied will normalize data to a range of +- 1 
        self.norm_factors = norm_factors
    
    def load(self):
        try:
            with open("SimpleSims\\fs2020.load") as f:
                cmd = f.readline()
            log.info("Starting FS 2020")
            subprocess.Popen([cmd])
            #os.startfile(line)
            return("loading...") 
        except Exception as e:
            print(e)
            return(str(e))            
   
    def connect(self):
        # returns string code or None if no error
        try:
            self.sm = SimConnect()
            # Note the default _time is 25 to be refreshed every 25 ms
            if self.sm:
                self.aq = AircraftRequests(self.sm, _time=self.interval_ms)
                self.is_connected = True
                log.info("FS 2020 is connected")
                # Use _time=ms where ms is the time in milliseconds to cache the data.
                # Setting ms to 0 will disable data caching and always pull new data from the sim.
                # There is still a timeout of 4 tries with a 10ms delay between checks.
                # If no data is received in 40ms the value will be set to None
                # Each request can be fine tuned by setting the time param.
                return None 
            else:
                return("Not connecting to SimConnect") 
        except ConnectionError:
            return "Not connecting, is FS2020 loaded?"
        except Exception as e:
            log.info("FS2020 connect err: " + str(e)) 
            return(e)

    def run(self):
        print("todo run")

 
    def read(self):
        try:
            x = self.aq.get("ACCELERATION_BODY_X") * self.norm_factors[0]
            y = self.aq.get("ACCELERATION_BODY_Y") * self.norm_factors[1]
            z = self.aq.get("ACCELERATION_BODY_Z") * self.norm_factors[2]
            roll = self.aq.get("PLANE_BANK_DEGREES") * self.norm_factors[3]  # actually radians
            pitch = self.aq.get("PLANE_PITCH_DEGREES") * self.norm_factors[4] # actualy radians
            yaw = self.aq.get("TURN_COORDINATOR_BALL") * self.norm_factors[5]
            return (x, y, z, roll, pitch, yaw)
        except:
            return (0,0,0,0,0,0)



if __name__ == '__main__':
    sim = Sim()
    if(sim.is_connected):
        sim.set_norm_factors([.01, .01, .01, 1, 1, 1])
        while(1):
            xyzrpy = fs.read()
            csv = ['%.3f' %  elem for elem in xyzrpy]
            print(','.join(csv))   
    quit()