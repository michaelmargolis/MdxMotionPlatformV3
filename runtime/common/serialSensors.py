""" SerialSensors.py
    Classes to support specific sensor protocols
"""

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

try:
    from common.serialProcess import SerialProcess
except:
    from serialProcess import SerialProcess  

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
        self.direction = (1,1,1,1,1,1)

    def read(self):
        if super(Encoder, self).available():
            msg = super(Encoder, self).read()
            if msg:
                data = msg.rstrip('\r\n}').split(',')
                # Data format for mm:     ">,e1,e2,e3,e4,e5,e6,timestamp\n"
                values = []
                if len(data) >= 8:
                    for idx, val in enumerate(data[1:7]):
                        try:
                            v = float(val) * self.direction[idx] 
                            values.append(v)
                        except ValueError:
                            print("conversion error for serial value", val, "full message", msg, "len=", len(data))
                    return values, data[7]
        return None, 0

    def set_direction(self, values):
        self.direction = values
    
    def reset(self):
        self.s.write("R".encode())
        
    def set_interval(self, interval_ms):
        msg = format("I=%d" % (interval_ms))
        self.s.write(msg.encode()) 
        
    def set_precision(self, precision): # nbr digits after decimal point
        msg = format("P=%d" % (precision))
        self.s.write(msg.encode()) 

    """ not supported in this version
    def set_error_mode(self):
        self.s.write("M=E".encode())

    def set_distance_mode(self):
        self.s.write("M=D".encode())

    def get_info(self):
        self.s.write("?".encode())
    """
    
class IMU(SerialProcess):
    def __init__(self):
        super(IMU, self).__init__()

    def read(self):
        msg = super(Imu, self).read()
        return msg.rstrip('\r\n}')

    def tare(self):
        self.write("T".encode())

class Scale(SerialProcess):
    def __init__(self):
        super(Scale, self).__init__()

    def read(self):
        return self.update()

    def update(self):
        if self.is_open():
            try:
                self.write('{"measure":"kg"}'.encode())
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

if __name__ == "__main__":
    import time
    import logging
    log = logging.getLogger(__name__)
    encoder_directions = [1,-1,1,1,1,-1]
    log.info("encoder directions are: %s", str(encoder_directions))
    port = "COM12"
    encoder = SerialContainer(Encoder(), port, "encoder", None, 115200)
    encoder.sp.set_direction(encoder_directions)
    if encoder.sp.open_port(port, 115200):
        print("port opened")
        count = 0
        while(True):
            encoder_data,timestamp = encoder.sp.read()
            if encoder_data:
                if len(encoder_data) != 6:
                    print("error, data len = ", len(encoder_data))
                print(encoder_data, timestamp)    
            # time.sleep(.005)
        
    else:
       print(port + " port not available")
    
