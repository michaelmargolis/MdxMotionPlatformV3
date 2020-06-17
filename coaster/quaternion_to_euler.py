# Helper class to decode rotation quaternion into pitch/yaw/roll

from numpy import sin, cos, arctan2, sqrt, pi  # import from numpy
#from quat.py import calc_angvel

class Quaternion (object):

    def __init__(self, x, y, z, w):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def __repr__(self):
        return format("%.5f,%.5f,%.5f,%.5f" % (self.x, self.y, self.z, self.w))

    def toPitchFromYUp(self):
        vx = 2 * (self.x * self.y + self.w * self.y)
        vy = 2 * (self.w * self.x - self.y * self.z)
        vz = 1.0 - 2 * (self.x * self.x + self.y * self.y)
        return arctan2(vy, sqrt(vx * vx + vz * vz))

    def toYawFromYUp(self):
        return arctan2(2 * (self.x * self.y + self.w * self.y),
                       1.0 - 2 * (self.x * self.x + self.y * self.y))

    def toRollFromYUp(self):
        return arctan2(2 * (self.x * self.y + self.w * self.z),
                       1.0 - 2 * (self.x * self.x + self.z * self.z))
    
    def toYawRate(self):
        calc_angvel()
