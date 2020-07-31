"""
encoders.py

Support for serial and TCP encoders
 fixme this code is deprecated
"""

import logging
log = logging.getLogger(__name__)

try:
    from queue import Queue
except ImportError:
    from Queue import Queue
if __name__ == '__main__':
    from serialProcess import SerialProcess
    from tcp_client import TcpClient
    from tcp_server import SockServer
else:
    from common.serialProcess import SerialProcess
    from common.tcp_client import TcpClient
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

class TcpEncoder(TcpClient, object):
    def __init__(self, ip_addr, port):
        super(TcpEncoder, self).__init__(ip_addr, port)
    
    def read(self):
        data = self.receive()
        if data:
            data = data.rstrip('\r\n}').split(',')
            # Data format for mm:     D0,e1,e2,e3,e4,e5,e6,timestamp\n"
            if len(data) >= 8:
                return data[1:7], data[7]
        return None, 0

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

    tcp_port = 10016
    client = TcpEncoder('', tcp_port)
    while True:
        try:
            if not client.status.is_connected:
                client.connect()
            else: 
                if client.available() > 0:
                    data = client.receive()
                    data = data.decode('utf-8')
                    # Convert decoded data into list
                    data = eval(data)
                    print data
        except Exception as e:
            print( "err", str(e))
        if kb.kbhit(): 
            key = kb.getch()
            if ord(key) == 27: # esc
                break
    client.disconnect()

if __name__ == "__main__":
    main()