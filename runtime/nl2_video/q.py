import sys
import scipy.io as sio
import numpy as np
#import cv2
#import os
#import time

# from quaternion_to_euler import Quaternion
# from my_quaternion import Quaternion
# from pyquaternion import Quaternion
import quaternion  # for mobile/quaternion
import math
# from quat.py import Quaternion
import traceback


telemetry = np.loadtxt('mdx_coaster.csv', delimiter = ',', skiprows=1) 

print 'read', len(telemetry), 'records'

#                    x,y,z,w
quats = telemetry[:,[12,13,14,15]]

headings = telemetry[:,[8]]

deltas = []
for idx, h in enumerate(headings):
    if idx > 0:
        prev = headings[idx-1] 
        deltas.append(min(h-prev, h-prev+2*math.pi, h-prev-2*math.pi, key=abs))
np.savetxt("deltas.csv", deltas, delimiter=',', fmt='%0.3f')

"""
for idx, q in enumerate(quats):
    if idx > 0:
        q0 = quaternion.quaternion(quats[idx-1][0], quats[idx-1][1], quats[idx-1][2], quats[idx-1][3])
        q1 = quaternion.quaternion(quats[idx][0], quats[idx][1], quats[idx][2], quats[idx][3])
        # print quaternion.as_euler_angles(q1-q0)[1]
"""


