""" SerialSensors.py
    Classes to support specific sensor protocols
"""

try:
    from queue import Queue
except ImportError:
    from Queue import Queue
from common.serialProcess import SerialProcess

class SerialContainer(object):
    def __init__(self, sp, combo, desc, label, baud):
        self.sp = sp
        self.combo = combo
        self.desc = desc
        self.label = label
        self.baud = baud

class Encoder(SerialProcess):
    def __init__(self):
        super(Encoder, self).__init__()

    def read(self):
        data = super(Encoder, self).read()
        if data:
            data = data.rstrip('\r\n}').split(',')
            # Data format for mm:     D0,e1,e2,e3,e4,e5,e6,timestamp\n"
            if len(data) >= 8:
                return data[1:7], data[7]
        return None, 0

    def reset(self):
        self.s.write("R")

    def set_error_mode(self):
        self.s.write("M=E")

    def set_distance_mode(self):
        self.s.write("M=D")

    def get_info(self):
        self.s.write("?")

class IMU(SerialProcess):
    def __init__(self):
        super(IMU, self).__init__()

    def read(self):
        msg = super(Imu, self).read()
        return msg.rstrip('\r\n}')

    def tare(self):
        self.write("T")

class Scale(SerialProcess):
    def __init__(self):
        super(Scale, self).__init__()

    def read(self):
        return self.update()

    def update(self):
        if self.is_open():
            try:
                self.write('{"measure":"kg"}')
                msg = super(Scale, self).read()
                if '"measurement"' in msg:
                    msg = msg.split(":")
                    weight = msg[1].rstrip('\r\n}')
                    return weight
                else:
                    pass
                    # print "scale", msg
            except TypeError:
                pass
            except Exception as e:
                print("error reading scale:", e)
        return None

    def tare(self):
        print("Press yellow button, tare not yet supported in scale firmware\n")

class ServoModel(SerialProcess):
    def __init__(self):
        self.result_queue = Queue()
        super(ServoModel, self).__init__(self.result_queue)

    def read(self):
        msg = super(ServoModel, self).read()
        if msg:
            msg = msg.rstrip('\r\n}')
            return msg
        return None
