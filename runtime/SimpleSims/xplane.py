# sim class for X-Plane using nasa xplaneConnect

import os
import socket
import logging as log
import traceback
from collections import namedtuple
from math import pi, degrees, radians, sqrt
import SimpleSims.xpc as xpc

# xplane uses OpenGL coordinates - x is right, y up, z back

datarefs = namedtuple('datarefs', ('DR_groundspeed','DR_fnrml_prop', 'DR_fside_prop', 'DR_faxil_prop', \
                      'DR_fnrml_aero', 'DR_fside_aero', 'DR_faxil_aero', 'DR_fnrml_gear', \
                      'DR_fside_gear', 'DR_faxil_gear', 'DR_m_total', 'DR_the', 'DR_psi', 'DR_phi', 'DR_acf_axial'))
                      # todo 'DR_N_prop', 'DR_N_aero', 'DR_N_gear')) 
                      

xyzrpy = (b'g_axil', b'g_side', b'g_nrml', b'vy_acf_axis', b'vx_acf_axis', b'vz_acf_axis')

xyzrpy_drefs = [b'sim/flightmodel/forces/' + e for e in xyzrpy]

class Sim():
    def __init__(self, sleep_func, interval_ms = 25):
        # todo Create  link
        self.sleep_func = sleep_func
        self.interval_ms = interval_ms
        self.xpc = None
        self.is_connected = False
        # self.norm_factors = [2.0, 2.0, .5, -.02, .15, .15]
        self.norm_factors = [2, .2, .1, .015, -.03, .1]
        self.name = "X-Plane"
        self.ip_addr = '127.0.0.1' # address of pc running xplane
        self.port = 49009
        self.prev_yaw = None

    def __del__(self):
        if self.xpc:
            self.xpc.close()
    
    def set_norm_factors(self, norm_factors):
        # values for each element that when multiplied will normalize data to a range of +- 1 
        self.norm_factors = norm_factors
    
    def set_state_callback(self, callback):
        self.state_callback = callback

    def load(self, loader):
        log.info("Attempting to start sim by executing " + loader)
        os.startfile(loader)
       
   
    def connect(self):
        # returns error string or None if no error
        try:
            self.xpc = xpc.XPlaneConnect(self.ip_addr)
            # print(self.xpc.getDREFs(xyzrpy_drefs)) # try and get translation and rotation data
            self.init_drefs()
            data = self.xpc.getDREFs(self.drefs) # try and get telemetry
            d = datarefs._make(data) # load namedtuple with values 
            log.info("X-Plane connected on " + self.ip_addr)
            self.is_connected = True
            return None
        except Exception as e:
            print("Error connecting to Xplane", str(e))
            print(traceback.format_exc())
            return(str(e))

    def init_drefs(self):
        self.drefs = []
        # the following must match datarefs namedtuple
        self.drefs.append(b"sim/flightmodel/position/groundspeed")
        self.drefs.append(b"sim/flightmodel/forces/fnrml_prop")
        self.drefs.append(b"sim/flightmodel/forces/fside_prop")
        self.drefs.append(b"sim/flightmodel/forces/faxil_prop")
        self.drefs.append(b"sim/flightmodel/forces/fnrml_aero")
        self.drefs.append(b"sim/flightmodel/forces/fside_aero")
        self.drefs.append(b"sim/flightmodel/forces/faxil_aero")
        self.drefs.append(b"sim/flightmodel/forces/fnrml_gear")
        self.drefs.append(b"sim/flightmodel/forces/fside_gear")
        self.drefs.append(b"sim/flightmodel/forces/faxil_gear")
        self.drefs.append(b"sim/flightmodel/weight/m_total")
        self.drefs.append(b"sim/flightmodel/position/theta")
        self.drefs.append(b"sim/flightmodel/position/psi")
        self.drefs.append(b"sim/flightmodel/position/phi")
        self.drefs.append(b'sim/flightmodel/forces/vx_acf_axis')
        # added by mem (not working yet
        """
        self.drefs.append(b"sim/flightmodel/position/N_prop")
        self.drefs.append(b"sim/flightmodel/position/N_aero")
        self.drefs.append(b"sim/flightmodel/position/N_gear")
        """

    def is_connected(self):
        # todo
        return True            

    def run(self):
        print("run")  
        if self.is_connected:
            self.xpc.pauseSim(False)

    def pause(self):
        print("pause")  
        if self.is_connected:
            self.xpc.pauseSim(True)
        
    def read(self):
        try:
            """
            drefs = self.xpc.getDREFs(xyzrpy_drefs)            
            xyzrpy = [float(drefs[i][0]) * self.norm_factors[i] for i in range(len(drefs))]
            csv = ['%.4f' %  elem for elem in xyzrpy]
            print(','.join(csv))  
            """            
            raw_data = self.xpc.getDREFs(self.drefs) # try and get telemetry
            named_data = datarefs._make(raw_data) # load namedtuple with values 
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
        """
        float groundspeed = XPLMGetDataf(DR_groundspeed);
        float fnrml_prop = XPLMGetDataf(DR_fnrml_prop);
        float fside_prop = XPLMGetDataf(DR_fside_prop);
        float faxil_prop = XPLMGetDataf(DR_faxil_prop);
        float fnrml_aero = XPLMGetDataf(DR_fnrml_aero);
        float fside_aero = XPLMGetDataf(DR_fside_aero);
        float faxil_aero = XPLMGetDataf(DR_faxil_aero);
        float fnrml_gear = XPLMGetDataf(DR_fnrml_gear);
        float fside_gear = XPLMGetDataf(DR_fside_gear);
        float faxil_gear = XPLMGetDataf(DR_faxil_gear);
        float m_total = XPLMGetDataf(DR_m_total);
        float the = XPLMGetDataf(DR_the);
        float psi = XPLMGetDataf(DR_psi);  yaw
        float phi = XPLMGetDataf(DR_phi); roll
        
        datarefs = namedtuple('datarefs', ('DR_groundspeed','DR_fnrml_prop', 'DR_fside_prop', 'DR_faxil_prop', \
                      'DR_fnrml_aero', 'DR_fside_aero', 'DR_faxil_aero', 'DR_fnrml_gear', \
                      'DR_fside_gear', 'DR_faxil_gear', 'DR_m_total', 'DR_the', 'DR_psi', 'DR_phi')) 
                      
        
        """
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

if __name__ == '__main__':
    sim = Sim()
    if(sim.is_connected):
        sim.set_norm_factors([.01, .01, .01, 1, 1, 1])
        while(1):
            xyzrpy = sim.read()
            csv = ['%.3f' %  elem for elem in xyzrpy]
            print(','.join(csv))   
    quit()