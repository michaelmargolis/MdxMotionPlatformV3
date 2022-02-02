""" transform.py
input is nl2 telemetry msg, output is: surge, sway, heave, roll, pitch, yaw
"""

from agents.nolimits_coaster.my_quaternion import Quaternion
import math

class Transform():
    def __init__(self, gain=.6):
        self.prev_yaw = 0
        self.gain = gain # adjusts level of outputs
        self.prev_yaw = None
        self.lift_height = 32 # max height of lift in meters

    def reset_xform(self):
            # call this when train is dispatched (todo test if needed)
            self.prev_yaw = None

    def set_lift_height(self, height):
        self.lift_height = height # max height of lift in meters
        
    def get_transform(self, tm_msg): 
        # returns surge, sway, heave, roll, pitch, yaw from nl2 telemetry msg 
        quat = Quaternion(tm_msg.quatX, tm_msg.quatY, tm_msg.quatZ, tm_msg.quatW) 
        roll = self.gain * quat.toRollFromYUp() / math.pi
        pitch = self.gain * -quat.toPitchFromYUp()
        yaw_rate = self.gain * self.process_yaw(-quat.toYawFromYUp()) 

        #  y from coaster is vertical. z forward,  x side
        if tm_msg.posY > self.lift_height:
           self.lift_height = tm_msg.posY
        heave = ((tm_msg.posY * 2) / self.lift_height) -1
        
        if  tm_msg.gForceZ >=0:
            surge = math.sqrt( tm_msg.gForceZ)
        elif tm_msg.gForceZ < 0:
            surge = -math.sqrt(-tm_msg.gForceZ)

        if  tm_msg.gForceX >=0:
            sway = math.sqrt( tm_msg.gForceX)
        elif tm_msg.gForceX < 0:
            sway = -math.sqrt(-tm_msg.gForceX)

        return  [surge, sway, heave, roll, pitch, yaw_rate]

    def process_yaw(self, yaw):
        if self.prev_yaw != None:
            # handle crossings between 0 and 360 degrees
            if yaw - self.prev_yaw > math.pi:
                yaw_rate = (self.prev_yaw - yaw) + (2*math.pi)
            elif  yaw - self.prev_yaw < -math.pi:
                yaw_rate = (self.prev_yaw - yaw) - (2*math.pi)
            else:
                yaw_rate = self.prev_yaw - yaw
        else:
            yaw_rate = 0
        self.prev_yaw = yaw

        # the following code limits dynamic range 
        if yaw_rate > math.pi:
           yaw_rate = math.pi
        elif yaw_rate < -math.pi:
            yaw_rate = -math.pi

        yaw_rate = yaw_rate / 2
        if yaw_rate >= 0:
            yaw_rate = math.sqrt(yaw_rate)
        elif yaw_rate < 0:
            yaw_rate = -math.sqrt(-yaw_rate)

        return yaw_rate 