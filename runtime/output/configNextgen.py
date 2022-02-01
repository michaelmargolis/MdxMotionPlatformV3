
"""
This file defines the coordinates of the upper (base) and lower (platform) attachment points

The coordinate frame follows ROS conventions, positive values: X is forward, Y is left, Z is up,
roll is right side down, pitch is nose down, yaw is CCW; all from perspective of person on platform.

The each of the three upper inner, upper outer, lower inner and lower outer attachment points define circles with the center at the origin
The X axis is the line through the origin running  from back to front (X values increase moving forward).
The Y axis passes through the origin with values increasing to the left.
                   +y 
                 -------- 
                []::::::
                []:::::::                
      -x        []::::::::   +X  (front)
                []::::::: 
                {}::::::
                 --------
                   -y

"""

import math
import numpy as np


class PlatformConfig(object):
       
    PLATFORM_NAME = "Flying Platform"
    PLATFORM_TYPE = "SLIDER"
    PLATFORM_INVERTED = False

    def __init__(self):
    
        # config for top facing muscles 0 and 5
        #self.INVERT_AXIS = (1,-1,-1,-1,1,-1) # set element to -1 to invert axis direction
        #self.SWAP_ROLL_PITCH = False  # also swaps x and y
        
        # config for top front facing muscles 1 and 2
        self.INVERT_AXIS = (1,1,-1,-1,-1,-1) # set element to -1 to invert axis direction
        self.SWAP_ROLL_PITCH = True  # also swaps x and y

    
        # normal distance from center axis to center of upper ball joint
        self.center_to_inner_joint = 383 
        self.center_to_outer_joint = 483 

        # normal distance from center axis to center of lower ball joints
        self.center_to_lower_inner_joint = 505 
        self.center_to_lower_outer_joint = 585

        self.PLATFORM_MID_HEIGHT = 302  #
        self.LOAD_RANGE = (20,90) # in Kg

        self.is_slider = True
        self.joint_min_offset = 130 # min distance from ball joint to slider center
        self.joint_max_offset = 330 # min distance plus full max of actuator slide
        self.slider_range = self.joint_max_offset - self.joint_min_offset
        self.strut_length = 400  # distance between upper and lower ball joints centers

        self.joint_angle = -math.pi*2/3 # 120 degrees

        self.upper_coordinates = [] # moving platform attachment points
        self.lower_coordinates = [] # slider midpoints
        self.lower_origin = [] # slider coordinates closest to center 

        self.DISABLED_LEN = 0 # muscles fully relaxed
        self.PROPPING_LEN = 0 # only used when platform has piston prop or stairs
        self.HAS_PISTON = False  # True if platform has piston actuated prop
        self.HAS_BRAKE = True # True if platform has electronic braking when parked

        #  the range in mm or radians from origin to max extent in a single DOF 
        self.limits_1dof = [60, 60, 75 , math.radians(12), math.radians(12), math.radians(12)]

        # limits at extremes of movement
        self.limits_6dof = [40, 40, 50, math.radians(6), math.radians(6), math.radians(6)]

        self.MIN_ACTUATOR_LEN = 0  
        self.MAX_ACTUATOR_RANGE = self.slider_range
        self.MAX_ACTUATOR_LEN = self.slider_range
        
    def calculate_coords(self):
        self.joint_mid_offset = (self.joint_min_offset + self.joint_max_offset)/2  # offset at mid position
        # print("center_to_inner_joint=", self.center_to_inner_joint)
        # print("center_to_outer_joint=", self.center_to_outer_joint)
        
        z = self.PLATFORM_MID_HEIGHT  

        # calculate moving platform attachment coordinates
        upper_0 = [ self.center_to_inner_joint, 0, z]
        upper_5 = [ self.center_to_outer_joint, 0, z]
        self.upper_coordinates.append(upper_0)
        self.upper_coordinates.append(self.rotate(upper_5, self.joint_angle))
        self.upper_coordinates.append(self.rotate(upper_0, self.joint_angle))
        self.upper_coordinates.append(self.rotate(upper_5, self.joint_angle*2))
        self.upper_coordinates.append(self.rotate(upper_0, self.joint_angle*2))
        self.upper_coordinates.append(upper_5)

        # calculate coordinates of mid point of slider 
        lower_0 = [ self.center_to_inner_joint, -self.joint_mid_offset, 0]
        lower_5 = [ self.center_to_outer_joint, self.joint_mid_offset, 0]
        self.lower_coordinates.append(lower_0)
        self.lower_coordinates.append(self.rotate(lower_5, self.joint_angle))
        self.lower_coordinates.append(self.rotate(lower_0, self.joint_angle))
        self.lower_coordinates.append(self.rotate(lower_5, self.joint_angle*2))
        self.lower_coordinates.append(self.rotate(lower_0, self.joint_angle*2))
        self.lower_coordinates.append(lower_5)
       
       
        # list of slider angles
        ###self.slider_angles = [0,self.joint_angle,self.joint_angle,self.joint_angle*2,self.joint_angle*2, 0 ]
        # values are: [angle in rads, x sign, y sign]
        self.slider_angles = [[0,1,-1], 
                              [self.joint_angle,-1, 1],
                              [self.joint_angle, 1, -1],
                              [self.joint_angle*2, -1, 1],
                              [self.joint_angle*2, 1, -1], 
                              [0, 1, 1]]
    
        self.BASE_POS = np.array(self.lower_coordinates)
        self.PLATFORM_POS = np.array(self.upper_coordinates)

    def rotate(self, point, radians):
        # rotates point around z axis, angle in radians
        px, py, pz = point        
        qx = math.cos(radians) * px - math.sin(radians) * py
        qy = math.sin(radians) * px  + math.cos(radians) * py
        # print "angle=", math.degrees(radians), px, py, round(qx), round(qy)
        return qx, qy, pz

if __name__ == "__main__":
    import numpy as np
    from kinematicsV2 import Kinematics
    import plot_config  #  only for testing

    cfg = PlatformConfig() 
    cfg.calculate_coords()
    k = Kinematics()
    
    print(cfg.upper_coordinates)
    print(cfg.lower_coordinates)
    
    print("base\n", cfg.BASE_POS)
    print("platform\n", cfg.PLATFORM_POS)
    plot_config.plot( cfg.BASE_POS,  cfg.PLATFORM_POS, cfg.PLATFORM_MID_HEIGHT, cfg.PLATFORM_NAME )
    plot_config.plot3d(cfg, cfg.PLATFORM_POS)
 
    k.set_geometry( cfg.BASE_POS,  cfg.PLATFORM_POS)
    mid_pos = k.inverse_kinematics([0,0,0,0,0,0])
    #  calculates inverse kinematics and prints actuator lenghts
    while True:
        request = input("enter orientation on command line as: surge, sway, heave, roll, pitch yaw ")
        if request == "":
            exit()
        request = list(map( float, request.split(',') ))
        if len(request) == 6:
            actuator_lengths = k.inverse_kinematics(request)
            print(np.around(actuator_lengths- mid_pos))
            # print actuator_lengths.astype(int) 
        else:
           print("expected 3 translation values in mm and 3 rotations values in radians")