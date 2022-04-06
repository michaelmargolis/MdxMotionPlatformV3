""" kinematics

Copyright Michael Margolis, Middlesex University 2019; see LICENSE for software rights.

finds actuator lengths L such that the platform is in position defined by
    request as:  [surge, sway, heave, roll, pitch yaw]

"""

import math
import copy
import numpy as np

class Kinematics(object):
    def __init__(self, scale=1.0):
        self.intensity = 1.0
        self.scale = scale # scale non-normalized xyz values by this factor

    def set_geometry(self, base_pos, platform_pos, platform_mid_height):
        self.base_pos = base_pos
        self.platform_pos = platform_pos
        self.platform_mid_height = platform_mid_height

    """ 
    returns numpy array of actuator lengths for given request orientation
    """
    def inverse_kinematics(self, request):
        print "kinematics request: ", request,
        adj_req = np.asarray(request)
        adj_req =  adj_req * self.intensity

        hack = .75 # temp hack to reduce values to compensate for slider inefficiencies 
        
        adj_req[2] = self.platform_mid_height*self.scale + adj_req[2]  # z axis displacement value is offset from center 
        if self.platform_mid_height < 0: # is fixed platform above moving platform
            adj_req[2] = -adj_req[2]  # invert z value on inverted stewart platform
        
        #print "z = ", request[2], "adjusted z =:", adj_req[2], "mid height", self.platform_mid_height
        adj_req[0] = adj_req[0] * self.scale * hack
        adj_req[1] = adj_req[1] * self.scale * hack
        print "adjusted", adj_req, "using scale:", self.scale
        a = np.array(adj_req).transpose()
        roll = a[3] * hack  # positive roll is right side down
        pitch = -a[4] * hack  # positive pitch is nose down
        yaw = a[5] * hack  # positive yaw is CCW
        #  Translate platform coordinates into base coordinate system
        #  Calculate rotation matrix elements
        cos_roll = math.cos(roll)
        sin_roll = math.sin(roll)
        cos_pitch = math.cos(pitch)
        sin_pitch = math.sin(pitch)
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        #  calculate rotation matrix
        #  Note that it is a 3-2-1 rotation matrix
        Rzyx = np.array([[cos_yaw*cos_pitch, cos_yaw*sin_pitch*sin_roll - sin_yaw*cos_roll, cos_yaw*sin_pitch*cos_roll + sin_yaw*sin_roll],
                         [sin_yaw*cos_pitch, sin_yaw*sin_pitch*sin_roll + cos_yaw*cos_roll, sin_yaw*sin_pitch*cos_roll - cos_yaw*sin_roll],
                         [-sin_pitch, cos_pitch*sin_roll, cos_pitch*cos_roll]])
        #  platform actuators points with respect to the base coordinate system
        xbar = a[0:3] - self.base_pos
        #  orientation of platform wrt base

        uvw = np.zeros(self.platform_pos.shape)
        for i in xrange(6):
            uvw[i, :] = np.dot(Rzyx, self.platform_pos[i, :])

        #  leg lengths are the length of the vector (xbar+uvw)
        L = np.sum(np.square(xbar + uvw), 1)
        H = np.full(6,self.platform_mid_height*self.platform_mid_height)
        
        self.distances = np.sqrt(L-H)
        # print "h =", H, "d =",  self.distances
        return np.sqrt(L)
    
    def slider_distances(self, strut_lengths):
        print "strut lengths",strut_lengths.astype(int) , (self.distances-60).astype(int)
        # print  "clipped\n", (distances - np.clip(distances,0,100)).astype(int)
        return  np.clip(self.distances-65,0,100).astype(int)
        
    def set_intensity(self, intensity):
        self.intensity = intensity
    

if __name__ == "__main__":
    from cfg_SlidingActuators import *
    import plot_config
    
    cfg = PlatformConfig()
    scale = 0.5
    k = Kinematics(scale)
    cfg.calculate_coords()
    
    if len(cfg.BASE_POS) == 3:
        #  if only three vertices, reflect around X axis to generate right side coordinates
        otherSide = copy.deepcopy(cfg.BASE_POS[::-1])  # order reversed
        for inner in otherSide:
            inner[1] = -inner[1]   # negate Y values
        cfg.BASE_POS.extend(otherSide)

        otherSide = copy.deepcopy(cfg.PLATFORM_POS[::-1])  # order reversed
        for inner in otherSide:
            inner[1] = -inner[1]   # negate Y values
        cfg.PLATFORM_POS.extend(otherSide)
    k.set_geometry( cfg.BASE_POS, cfg.PLATFORM_POS, cfg.PLATFORM_MID_HEIGHT)

    
    #  uncomment the following to plot the array coordinates
    # plot_config.plot(cfg.BASE_POS, cfg.PLATFORM_POS, cfg.PLATFORM_MID_HEIGHT, cfg.PLATFORM_NAME )
    
#  calculates inverse kinematics and prints actuator lenghts
    while True:
        request = raw_input("enter orientation on command line as: surge, sway, heave, roll, pitch yaw ")
        if request == "":
            exit()
        request = map( float, request.split(',') )
        if len(request) == 6:
            v_strut_lengths = k.inverse_kinematics(request)
            distances = k.slider_distances(v_strut_lengths)
            print distances.astype(int)
        else:
           print "expected 3 translation values in mm and 3 rotations values in radians"
    