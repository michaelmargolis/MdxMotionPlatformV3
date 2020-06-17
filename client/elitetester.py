"""
  elitetester.py


"""

import sys
import socket
import traceback
import time

if __name__ == "__main__":
    new_msg = ['{"LinearAcceleration": [0.0,-0.0,0.000686],"AngularAcceleration": [0.000000,-0.000000,0.013]}',
           '{"LinearAcceleration": [0.1,-0.1,0.000686],"AngularAcceleration": [0.000000,-0.000000,0.013]}',
           '{"LinearAcceleration": [0.2,-0.2,0.000686],"AngularAcceleration": [0.000000,-0.000000,0.013]}',
           '{"LinearAcceleration": [0.3,-0.3,0.000686],"AngularAcceleration": [0.000000,-0.000000,0.013]}',
           '{"LinearAcceleration": [0.4,-0.4,0.000686],"AngularAcceleration": [0.000000,-0.000000,0.013]}',]
           
    org_msg = ['{"LinearAcceleration": "x:0.005790,y:0.033458,z:0.000686","AngularAcceleration": "x:0.000000,y:-0.000000,z:0.000013"}',
               '{"LinearAcceleration": "x:0.005790,y:0.033458,z:0.000686","AngularAcceleration": "x:0.000000,y:-0.000000,z:0.000013"}',
               '{"LinearAcceleration": "x:0.005790,y:0.033458,z:0.000686","AngularAcceleration": "x:0.000000,y:-0.000000,z:0.000013"}',
               '{"LinearAcceleration": "x:0.005790,y:0.033458,z:0.000686","AngularAcceleration": "x:0.000000,y:-0.000000,z:0.000013"}',
               '{"LinearAcceleration": "x:0.005790,y:0.033458,z:0.000686","AngularAcceleration": "x:0.000000,y:-0.000000,z:0.000013"}',]

    msg = org_msg
    HOST = "127.0.0.1"
    PORT = 5150
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    iter=0
    while True:
        try:
          print("sending", msg[iter])
          sock.sendto(msg[iter], (HOST, PORT));
          iter +=1
          if iter > 4:
             iter = 0
          time.sleep(.0125)
        except:
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print "err", e, s      
