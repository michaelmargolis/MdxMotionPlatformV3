# sim class for FS 2020
from SimConnect import *
from SimConnect.Enum import *
import os, sys
import logging as log
import math
import traceback

from fs_panel import Panel
from fs_gui_frame import SimUI

RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(RUNTIME_DIR))

# pot_map_vars lists possible variables to be associated with Panel potentiometers
pot_map_vars = ('Throttle', 'Propeller', 'Mixture', 'Spoilers')


class Sim():
    """ this class is imported by the motion platform SimInterface """
    def __init__(self, sleep_func, frame):
        self.is_connected = False
        self.is_running = False
        self.norm_factors = [.1, .05, .01, 1, 1, .3]
        self.name = "MS FS2020"

        self.fs2020 = FS2020(sleep_func)
        self.fs2020.set_norm_factors(self.norm_factors)

        self.sim_ui = SimUI(self.fs2020, sleep_func)
        self.sim_ui.init_ui(frame)
        self.fs2020.set_ui(self.sim_ui)

   
    def __del__(self):
        if self.sim_ui:
            self.sim_ui = None
            print("exiting FS2020")

    def set_norm_factors(self, norm_factors):
        # values for each element that when multiplied will normalize data to a range of +- 1 
        self.fs2020.set_norm_factors(norm_factors)

    def set_state_callback(self, callback):
        self.state_callback = callback
        
    def load(self, loader):
        try:
            log.info("Attempting to start sim by executing " +  loader)
            os.startfile(os.getcwd() + os.sep +loader)
            return("loading...") 
        except Exception as e:
            print(e)
            return(str(e))
   
    def connect(self):
        ret = self.fs2020.connect()
        self.is_connected = self.fs2020.is_connected
        if self.is_connected:
            self.state_callback("FS 2020 Connected")
        return ret

    def run(self):
        print("todo run")
        
    def pause(self):
        print("todo pause")
 
    def read(self):
        self.is_connected = self.fs2020.is_connected
        self.is_running = self.fs2020.is_running
        return self.fs2020.read_transform()
            
class FS2020():
    """ this is the interface to FS 2020 SimConnect """
    def __init__(self, sleep_func,  interval_ms = 25):
        self.sleep_func = sleep_func
        self.sim_ui = None
        # Create SimConnect link
        self.interval_ms = interval_ms
        self.is_connected = False
        self.is_running = self.is_connected # FIXME !!!
        self.norm_factors = [.1, .05, .01, 1, 1, .3]
        self.name = "MS FS2020"
        self.gear_toggle = None
        
        self.parking_brake_info = None
        self.gear_info = [0,0,0] # center, left, right
        self.gear_state = None # 0 if all up, 1 if all down
        self.flaps_angle = 0
        self.flaps_index = None
        
        self.simconnect = SimConnect(auto_connect=False)
    
    """
    def __del__(self):
        if self.simconnect and self.simconnect.ok:
            self.simconnect.exit()
    """
   
    def set_ui(self, ui):
        self.sim_ui = ui
 
    def set_norm_factors(self, norm_factors):
        # values for each element that when multiplied will normalize data to a range of +- 1 
        self.norm_factors = norm_factors
   
    def connect(self):
        # returns string code or None if no error
        try:
            self.simconnect.connect() 
            # Note the default _time is 25 to be refreshed every 25 ms
            print(self.simconnect.ok, self.simconnect.running)
            if self.simconnect.ok: # and self.simconnect.running:
                self.init_simvars()
                self.is_connected = True
                log.info("FS 2020 is connected")
                # Use _time=ms where ms is the time in milliseconds to cache the data.
                # Setting ms to 0 will disable data caching and always pull new data from the sim.
                # There is still a timeout of 4 tries with a 10ms delay between checks.
                # If no data is received in 40ms the value will be set to None
                # Each request can be fine tuned by setting the time param.
                return None 
            else:
                log.info("failed to connect to SimConnect")
                return("Not connecting to SimConnect") 
        except ConnectionError:
            # print(traceback.format_exc())
            return "Not connecting, is FS2020 loaded?"
        except Exception as e:
            log.info("FS2020 connect err: " + str(e)) 
            print(traceback.format_exc())
            return(e)

    def init_simvars(self):
        self.aq = AircraftRequests(self.simconnect, _time=self.interval_ms)
        self.ae = AircraftEvents(self.simconnect)
        # self.gear_set = self.ae.Miscellaneous_Systems.get("GEAR_SET")
        self.gear_set = self.aq.find('GEAR_HANDLE_POSITION') # True/False
        self.brake_toggle = self.ae.Miscellaneous_Systems.get("PARKING_BRAKES")     
        self.nbr_engines =  self.aq.find('NUMBER_OF_ENGINES').value
        self.throttles = []
        self.props = []
        self.mixture = []
        if self.nbr_engines : 
            self.nbr_engines = int(self.nbr_engines)
            log.info("aircraft has {} engines".format(self.nbr_engines))        
            for idx in range(1,self.nbr_engines+1): 
                self.throttles.append(self.aq.find('GENERAL_ENG_THROTTLE_LEVER_POSITION:'+ str(idx)))
                self.props.append(self.aq.find('GENERAL_ENG_PROPELLER_LEVER_POSITION:'+ str(idx)))         
                self.mixture.append(self.aq.find('GENERAL_ENG_MIXTURE_LEVER_POSITION:'+ str(idx)))      

        flap_positions_req = self.aq.find('FLAPS_NUM_HANDLE_POSITIONS')
        self.flap_positions = flap_positions_req.value
        if self.flap_positions:
            log.info("aircraft has %d flap positions", self.flap_positions)
        self.flap_index = self.aq.find('FLAPS_HANDLE_INDEX')  

    def read_transform(self):
        if self.simconnect.ok:
            # print("wha", self.simconnect.ok, self.simconnect.paused, self.simconnect.running)
            try:
                x = self.aq.get("ACCELERATION_BODY_X") * self.norm_factors[0]
                y = self.aq.get("ACCELERATION_BODY_Y") * self.norm_factors[1]
                z = self.aq.get("ACCELERATION_BODY_Z") * self.norm_factors[2]
                roll = -self.aq.get("PLANE_BANK_DEGREES") * self.norm_factors[3]  # actually radians
                pitch = self.aq.get("PLANE_PITCH_DEGREES") * self.norm_factors[4] # actualy radians
                yaw = self.aq.get("TURN_COORDINATOR_BALL") * self.norm_factors[5]
                return (x, y, z, roll, pitch, yaw)
            except:
                pass
        return (0,0,0,0,0,0)

    
    def read_panel_status(self):
        if self.simconnect.ok: #  and self.simconnect.running:
            try:
                brake = int(self.aq.get( "BRAKE_PARKING_POSITION")) # on is 1  
                if brake:
                #    print("brake is ",  "on" if brake else "off")                  
                    if self.sim_ui.ui.chk_auto_brake.isChecked() and brake == 1:
                        print("brake =", brake)
                        self.set_parking_brake(0)                  
                    else: 
                        if self.parking_brake_info  !=  brake:
                            print("parking brake state change to", "on" if brake else "off")
                            self.parking_brake_info = brake

                
                # print("flaps avail", self.aq.get( "FLAPS_AVAILABLE"))

                flaps_angle = self.aq.get("TRAILING_EDGE_FLAPS_LEFT_ANGLE")
                flaps_index = self.aq.get("FLAPS_HANDLE_INDEX")
                if flaps_index != self.flaps_index:
                    print("flaps index changed from {} to {}".format(self.flaps_index, flaps_index))
                    self.flaps_index = flaps_index
                if flaps_angle is not None:
                   self.flaps_angle = round(math.degrees(flaps_angle))
                   percent = self.aq.get( "FLAPS_HANDLE_PERCENT")
                   if percent:
                       self.flaps_percent = round(percent)
                   # print("flaps",  self.flaps_angle)
                self.get_gear_info()
            except TypeError:
                pass # ignore errors when not in sim mode


    def get_gear_info(self):
        # self.gear_toggle = ae.Miscellaneous_Systems.get("GEAR_TOGGLE")
        # print("is gear retreactable", self.aq.get("IS_GEAR_RETRACTABLE"))
        gear_center =  self.aq.get("GEAR_CENTER_POSITION")
        gear_left = self.aq.get("GEAR_LEFT_POSITION")
        gear_right =  self.aq.get("GEAR_RIGHT_POSITION")
        self.gear_info = [gear_center, gear_left, gear_right]
        if(all(g == 0 for g in self.gear_info)):
            self.gear_state = 0
        elif (all(g==1 for g in self.gear_info)):
            self.gear_state = 2
        else:
            self.gear_state = 1
        # print("gear info", self.gear_state)    
    
    def set_parking_brake(self, value): 
        print("PARKING_BRAKES", self.parking_brake_info) 
        if self.parking_brake_info != value:
            print("toggling PARKING_BRAKES" ) 
            self.brake_toggle()
            
    def set_gear(self, value): # up 0, down 1
        print("GEAR_SET")
        if value == 1: value = 2 # state: 0 is up, 2 is down
        if  self.gear_state != value: 
            # toggle 
            self.gear_set.value = value # todo does this need inverting
        
    def set_flaps(self, value): # up 0, down 1
        if value == 0 and self.flaps_index > 0:
            print("moving flaps index up to", self.flaps_index-1)
            self.flap_index.value = self.flaps_index-1
        if value == 1 and self.flaps_index < self.flap_positions:
            print("moving flaps index down to", self.flaps_index+1)
            self.flap_index.value = self.flaps_index+1

    def set_flaps_index(self, value): #0, 1 or 2
        self.flap_index.value = value  
        
    def set_simvar_axis(self, simvar, value):
        if self.is_connected:
            try:
                if simvar == 'Throttle':
                    for idx, throttle in enumerate(self.throttles):
                        throttle.setIndex(idx+1)
                        throttle.value = value
                elif simvar == 'Propeller':
                   for idx, prop in enumerate(self.props):
                        prop.setIndex(idx+1)
                        prop.value = value
                elif simvar == 'Mixture':
                   for idx, mix in enumerate(self.mixture):
                        mix.setIndex(idx+1)
                        mix.value = value

            except OSError:
                self.is_connected = False
                
