# laser_ping.py

from serialProcess import *
from moving_average import MovingAverage
import sys
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

class LaserPing(SerialProcess):

    def __init__(self):
        self.result_queue = Queue() 
        super(self.__class__, self).__init__(self.result_queue)
        #  super(self.__class__, self).__init__()

    def read(self):
        try:
            msg = super(self.__class__, self).read()
            if msg:
                msg = int(msg.strip('\r'))
                return msg
            return None
        except:
            return None 



if __name__ == "__main__":
    laser_ping = LaserPing()
    laser_ping.set_term_char('\r')
    port = 'COM31'
    MA = MovingAverage(4)
    if laser_ping.open_port(port, 9600):
        print("laser ping connected on port", port)
        while True:
            if laser_ping.available():
                distance = laser_ping.read()
                print(int(round(MA.next(distance))))


