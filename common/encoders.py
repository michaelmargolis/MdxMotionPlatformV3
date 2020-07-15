"""
encoders.py

Support for serial and TCP encoders
"""

import logging
log = logging.getLogger(__name__)

try:
    from queue import Queue
except ImportError:
    from Queue import Queue
if __name__ == '__main__':
    from serialProcess import SerialProcess
    from tcp_client import SockClient
    from tcp_server import SockServer
else:
    from common.serialProcess import SerialProcess
    from common.tcp_client import SockClient
    from common.tcp_server import SockServer


class SerialEncoder(SerialProcess):
    def __init__(self, tcp_port):
        super(SerialEncoder, self).__init__()
        self.server = SockServer('', tcp_port)
        self.server.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.server.close()
        self.server.join()
    
    def read(self):
        #data = super(self.__class__, self).read()
        data = super(SerialEncoder, self).read()
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

class TcpEncoder(SockClient, object):
    def __init__(self, ip_addr, port):
        super(TcpEncoder, self).__init__(ip_addr, port)

    def read(self):
        while self.available():
            data = self.receive()
        if data:
            try:
                return list(map(int, eval(data)))
            except Exception as e:
                print("error with eval of encoder data",  e)
        return None

    def reset(self):
        self.send("R\n")

    def set_error_mode(self):
        self.send("M=E\n")

    def set_distance_mode(self):
        self.send("M=D\n")

    def get_info(self):
        self.send("?\n")

def main():
    import traceback
    from kbhit  import KBHit

    #logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s',
    #                datefmt='%H:%M:%S')

    kb = KBHit()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%H:%M:%S')
    serial_port = "COM5"
    tcp_port = 10016
    encoders = SerialEncoder(tcp_port)
    if encoders.open_port(serial_port, 115200):
        log.info("Encoders connected on %s", serial_port) 
        while True:
            try:
                encoders.server.service()
                encoder_data, timestamp = encoders.read()
                print(encoder_data, timestamp )
                if encoders.server.connected_clients() > 0:
                     encoders.server.send(str(encoder_data)+ '\n') # echo data, strip out timestamp
                if kb.kbhit():  
                    if ord(kb.getch()) == 27: # esc
                        break
            except Exception as e:
                print(e, traceback.format_exc())
    else:
        log.error("Unable to open encoder port %s", serial_port )
    print('End.')

if __name__ == "__main__":
    main()        