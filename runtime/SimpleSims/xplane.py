# sim class for X-Plane using nasa xplaneConnect

import os, sys
import socket
import logging as log
import traceback
from collections import namedtuple
from math import pi, degrees, radians, sqrt
import SimpleSims.xpc as xpc # the interface to NASA XplaneConnect

from fs_panel import Panel  # these two imports only needed if using Panel and 
from fs_gui_frame import SimUI

RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(RUNTIME_DIR))

# pot_map_vars lists possible variables to be associated with Panel potentiometers
pot_map_vars = ('Throttle', 'Propeller', 'Mixture', 'Spoilers')

# xplane uses OpenGL coordinates - x is right, y up, z back

transform_refs = namedtuple('transform_refs', ('DR_groundspeed','DR_fnrml_prop', 'DR_fside_prop', 'DR_faxil_prop', \
                      'DR_fnrml_aero', 'DR_fside_aero', 'DR_faxil_aero', 'DR_fnrml_gear', \
                      'DR_fside_gear', 'DR_faxil_gear', 'DR_m_total', 'DR_the', 'DR_psi', 'DR_phi', 'DR_acf_axial'))
                      # todo 'DR_N_prop', 'DR_N_aero', 'DR_N_gear')) 
                      

xyzrpy = (b'g_axil', b'g_side', b'g_nrml', b'vy_acf_axis', b'vx_acf_axis', b'vz_acf_axis')

xyzrpy_drefs = [b'sim/flightmodel/forces/' + e for e in xyzrpy]

# prop lever not yet implimented
panel_refs = namedtuple('panel_refs', ('DR_parking_brake', 'DR_gear_deploy', 'DR_flap_deployment', 'DR_throttle', 'DR_mixture' ))

class Sim():
    """ this class is imported by the motion platform SimInterface """
    def __init__(self, sleep_func, frame):
        self.frame = frame
        self.is_connected = False
        # self.norm_factors = [2.0, 2.0, .5, -.02, .15, .15]
        self.norm_factors = [-2, .2, .1, .015, -.03, .1]
        self.name = "X-Plane"
        self.prev_yaw = None
        self.x_plane = X_Plane(sleep_func)
        """ comment out next two lines if Panel not wanted """
        self.sim_ui = SimUI(self.x_plane, sleep_func)
        self.sim_ui.init_ui(frame)
    
    def set_norm_factors(self, norm_factors):
        # values for each element that when multiplied will normalize data to a range of +- 1 
        self.norm_factors = norm_factors
    
    def set_state_callback(self, callback):
        self.state_callback = callback

    def load(self, loader):
        log.info("Attempting to start sim by executing " + loader)
        os.startfile(loader)
    
    def connect(self):
        ret = self.x_plane.connect()
        if self.x_plane.is_connected:
            self.state_callback("X Plane connected")

    def run(self):
        print("run")  
        self.x_plane.run()

    def pause(self):
        print("pause") 
        self.x_plane.pause()
        
    def read(self):
        self.is_connected = self.x_plane.is_connected
        if self.is_connected:
            return self.x_plane.read_transform()
            

class X_Plane():
    """ this is the interface to X-Plane """
    def __init__(self, sleep_func,  interval_ms = 25):
        self.sleep_func = sleep_func
        self.interval_ms = interval_ms
        self.is_connected = False
        self.norm_factors = [-2, .2, .1, .015, -.03, .1]
       
        self.xpc = None
        self.ip_addr = '127.0.0.1' # address of pc running xplane
        self.port = 49009
        
        self.parking_brake = 0
        self.parking_brake_info = None
        self.gear_toggle = None        
        self.gear_info = [0,0,0] # center, left, right
        self.gear_state = None # 0 if all up, 1 if all down
        self.flaps_angle = 0
        self.flaps_index = None
        

    def __del__(self):
        if self.xpc:
            self.xpc.close()
    
    def set_norm_factors(self, norm_factors):
        # values for each element that when multiplied will normalize data to a range of +- 1 
        self.norm_factors = norm_factors


    def init_drefs(self):
        self.xform_drefs = []
        # the following must match transform_refs namedtuple
        self.xform_drefs.append(b"sim/flightmodel/position/groundspeed")
        self.xform_drefs.append(b"sim/flightmodel/forces/fnrml_prop")
        self.xform_drefs.append(b"sim/flightmodel/forces/fside_prop")
        self.xform_drefs.append(b"sim/flightmodel/forces/faxil_prop")
        self.xform_drefs.append(b"sim/flightmodel/forces/fnrml_aero")
        self.xform_drefs.append(b"sim/flightmodel/forces/fside_aero")
        self.xform_drefs.append(b"sim/flightmodel/forces/faxil_aero")
        self.xform_drefs.append(b"sim/flightmodel/forces/fnrml_gear")
        self.xform_drefs.append(b"sim/flightmodel/forces/fside_gear")
        self.xform_drefs.append(b"sim/flightmodel/forces/faxil_gear")
        self.xform_drefs.append(b"sim/flightmodel/weight/m_total")
        self.xform_drefs.append(b"sim/flightmodel/position/theta")
        self.xform_drefs.append(b"sim/flightmodel/position/psi")
        self.xform_drefs.append(b"sim/flightmodel/position/phi")
        self.xform_drefs.append(b'sim/flightmodel/forces/vx_acf_axis')
        # added by mem (not working yet
        """
        self.xform_drefs.append(b"sim/flightmodel/position/N_prop")
        self.xform_drefs.append(b"sim/flightmodel/position/N_aero")
        self.xform_drefs.append(b"sim/flightmodel/position/N_gear")
        """
        self.panel_drefs = []
        self.panel_drefs.append(b"sim/flightmodel/controls/parkbrake")
        self.panel_drefs.append(b"sim/multiplayer/position/plane1_gear_deploy")
        self.panel_drefs.append(b"sim/multiplayer/controls/flap_request")
        self.panel_drefs.append(b"sim/cockpit2/engine/actuators/throttle_ratio") # 1.0 is max
        self.panel_drefs.append(b"sim/cockpit2/engine/actuators/mixture_ratio_all") # 0 cutoff, 1.0 full rich
                   
        
    def connect(self):
        # returns error string or None if no error
        try:
            if self.xpc == None:
                self.xpc = xpc.XPlaneConnect(self.ip_addr)
                # print(self.xpc.getDREFs(xyzrpy_drefs)) # try and get translation and rotation data
                self.init_drefs()
                data = self.xpc.getDREFs(self.xform_drefs) # try and get telemetry
                d = transform_refs._make(data) # load namedtuple with values 
                log.info("X-Plane connected on " + self.ip_addr)
                self.is_connected = True
            return None
        except ConnectionResetError:
            return "XPC network connection error" 
        except socket.timeout:
            return "XPC connection error, is xplane running?"
            
        except Exception as e:
            print("Error connecting to Xplane", str(e))
            print(traceback.format_exc())
            return(str(e))
            
    def run(self):       
        if self.is_connected:
            self.xpc.pauseSim(False)
    def pause(self):        
        if self.is_connected:
            self.xpc.pauseSim(True)
            
    def read_transform(self):
        try:
            """
            drefs = self.xpc.getDREFs(xyzrpy_drefs)            
            xyzrpy = [float(drefs[i][0]) * self.norm_factors[i] for i in range(len(drefs))]
            csv = ['%.4f' %  elem for elem in xyzrpy]
            print(','.join(csv))  
            """            
            raw_data = self.xpc.getDREFs(self.xform_drefs) # try and get telemetry
            named_data = transform_refs._make(raw_data) # load namedtuple with values 
            pre_norm = self.calculate_transform(named_data)
            # return (x, y, z, roll, pitch, yaw)
            xyzrpy = [pre_norm[i] * self.norm_factors[i] for i in range(len(pre_norm))]
            return xyzrpy
        except Exception as e:
            print("in xplane read:", str(e))
            print(traceback.format_exc())
            return (0,0,0,0,0,0)

   # method below derived from: https://developer.x-plane.com/code-sample/motionplatformdata/
    def calculate_transform(self, dref):

        ratio = self.clamp(dref.DR_groundspeed * 0.2, 0.0, 1.0)
        nrml_ = dref.DR_fnrml_prop + dref.DR_fnrml_aero + dref.DR_fnrml_gear
        nrml = self.fallout(nrml_, -0.1, 0.1)
        a_nrml = nrml / max(dref.DR_m_total,1.0)
        side =  dref.DR_fside_prop + dref.DR_fside_aero + dref.DR_fside_gear
        a_side = side / max(dref.DR_m_total,1.0)*ratio
        axil = dref.DR_faxil_prop + dref.DR_faxil_aero + dref.DR_faxil_gear
        a_axil = axil / max(dref.DR_m_total,1.0)*ratio
         
        #print("{},{},{},{}",format(ratio, nrml, side, axil)) 
        # print("{},{},{}".format(dref.DR_phi, dref.DR_the, dref.DR_psi)) 
        # yaw = dref.DR_N_aero + dref.DR_N_prop + dref.DR_N_gear 
        yaw = dref.DR_acf_axial #dref.DR_psi
        a_nrml = 0
        xyzrpy = [a_axil, a_side, a_nrml, dref.DR_phi, dref.DR_the, yaw]
        return xyzrpy
    
    def read_panel_status(self):
        raw_data = self.xpc.getDREFs(self.panel_drefs) # try and get telemetry
        named_data = panel_refs._make(raw_data) # load namedtuple with values 
        # print(named_data)
        self.parking_brake = named_data.DR_parking_brake
        self.parking_brake_info = self.parking_brake
        pass
        """
        if self.simconnect.ok: #  and self.simconnect.running:
            try:
                self.parking_brake_info = int(self.aq.get( "BRAKE_PARKING_POSITION"))
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
        """

    def get_gear_info(self):
        pass
        """
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
        """
        
    def set_parking_brake(self, value): 
        print("PARKING_BRAKES", value) 
        self.parking_brake = value
            
    def set_gear(self, value): # up 0, down 1
        print("GEAR_SET")
        if value == 1: value = 2 # state: 0 is up, 2 is down
        if  self.gear_state != value: 
            pass
            # toggle 
            ### self.gear_set.value = value # todo does this need inverting
        
    def set_flaps(self, value): # up 0, down 1
        if value == 0 and self.flaps_index > 0:
            print("moving flaps index up to", self.flaps_index-1)
            ### self.flap_index.value = self.flaps_index-1
        if value == 1 and self.flaps_index < self.flap_positions:
            print("moving flaps index down to", self.flaps_index+1)
            ### self.flap_index.value = self.flaps_index+1

    def set_flaps_index(self, value): #0, 1 or 2
        pass
        ### self.flap_index.value = value  
        
    def set_simvar_axis(self, simvar, value):
        if self.is_connected:
            try:
                if simvar == 'Throttle':
                    DR_throttle = value / 100.0
                """
                elif simvar == 'Propeller':
                   for idx, prop in enumerate(self.props):
                        prop.setIndex(idx+1)
                        prop.value = value
                elif simvar == 'Mixture':
                   for idx, mix in enumerate(self.mixture):
                        mix.setIndex(idx+1)
                        mix.value = value
                """
            except OSError:
                self.is_connected = False
     
    
  
    def yaw_rate_not_used(self, yaw_angle):
        yaw = -radians(yaw_angle)
        if self.prev_yaw != None:
            # handle crossings between 0 and 360 degrees
            if yaw - self.prev_yaw > pi:
                yaw_rate = (self.prev_yaw - yaw) + (2*pi)
                self.flip= 2
            elif  yaw - self.prev_yaw < -pi:
                yaw_rate = (self.prev_yaw - yaw) - (2*pi)
                self.flip= -2
            else:
                yaw_rate = self.prev_yaw - yaw
        else:
            yaw_rate = 0

        self.prev_yaw = yaw
        ###if yaw_rate != 0:
        ###   print(yaw,yaw_rate, self.flip)
        # the following code limits dynamic range nonlinearly
        if yaw_rate > pi:
           yaw_rate = pi
        elif yaw_rate < -pi:
            yaw_rate = -pi
        dbgYr2 = yaw_rate
        yaw_rate = yaw_rate / 2
        if yaw_rate >= 0:
            yaw_rate = sqrt(yaw_rate)
        elif yaw_rate < 0:
            yaw_rate = -sqrt(-yaw_rate) 
        return yaw_rate            

    def fallout(self, data, low, high):  
        if (data < low) or (data > high): return data
        elif (data < ((low + high) * 0.5)): return low
        return high

    def clamp(self, n, minn, maxn):
        return max(min(maxn, n), minn)                