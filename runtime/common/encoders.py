"""
encoders.py

Support for serial and TCP encoders
"""

import signal
import threading
import socket
import logging
log = logging.getLogger(__name__)

try:
    from common.serialProcess import SerialProcess
    from common.tcp_client import TcpClient
    from common.tcp_server import TcpServer
except:
    from serialProcess import SerialProcess
    from tcp_client import TcpClient
    from tcp_server import TcpServer

class SerialEncoder(SerialProcess):
    def __init__(self, tcp_port):
        super(SerialEncoder, self).__init__()
        self.server_address = ('', tcp_port)
        self.start_server()

    def __exit__(self, exc_type, exc_value, traceback):
        self.server.close()
        self.server.join()
    
    def start_server(self):
        signal.signal(signal.SIGINT, signal.SIG_DFL) # keyboard interrupt handler
        try:
            self.server = TcpServer(self.server_address)
            self.server.start()
            log.info("Encoders data broadcast on port %d, commands on port %d", self.server_address[1], self.server_address[1]+1)
        except socket.error:
            log.error("Error starting encoder TCP server on port %d, is it already in use?", self.server_address[1])

    def read(self):
        #data = super(self.__class__, self).read()
        data = super(SerialEncoder, self).read()
        if data:
            data = data.decode().rstrip('\r\n}').split(',')
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

class EncoderClient(TcpClient, object):
    def __init__(self, ip_addr, port=10016):
        super(EncoderClient, self).__init__(ip_addr, port)
        self.cmd_addr = (ip_addr, port + 1) # back channel port is server port +1
        self.cmd_channel = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        
    def read(self):
        data = None
        while self.available():
            data = self.receive()
        if data:
            try:
                return list(map(int, eval(data)))
            except Exception as e:
                print("error with eval of encoder data",  e)
        return None

    def send(self, cmd):
        self.cmd_channel.sendto(cmd, self.cmd_addr)

    def reset(self):
        self.send("R\n")

    def set_error_mode(self):
        self.send("M=E\n")

    def set_distance_mode(self):
        self.send("M=D\n")

    def get_info(self):
        self.send("?\n")


def main():
    try:
        from common.udp_tx_rx import UdpReceive
    except:
        from udp_tx_rx import UdpReceive
    kb = KBHit()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%H:%M:%S')
    serial_port = "COM3"
    ENCODER_SERVER_PORT = 10016  # must be same as value in system_config
    encoders = SerialEncoder(ENCODER_SERVER_PORT)
    cmd_channel = UdpReceive(ENCODER_SERVER_PORT+1)
    args = man().parse_args()
    is_testmode = args.testMode
    if encoders.open_port(serial_port, 115200):
        log.info("Encoders connected on serial port: %s", serial_port) 
        prev_timestamp = 0
        while True:
            try:
                encoder_data, timestamp = encoders.read()
                if encoder_data and prev_timestamp != timestamp:
                    encoder_data = ','.join(n for n in encoder_data)
                    if is_testmode:
                        encoder_data = testMode(encoder_data)
                    #  print(encoder_data, timestamp )
                    # if encoders.server.connected_clients() > 0:
                    # print encoder_data
                    #print("Encoder main:", encoder_data)
                    encoders.server.broadcast(encoder_data+'\n') # echo data, ignore timestamp
                    while cmd_channel.available():
                        incoming = cmd_channel.get() 
                        print("incoming=",  incoming)
                        if incoming[1] == 'R':
                            encoders.reset()
                            
            # except AttributeError as e:
            #     print(e)
            #    break
            except Exception as e:
                print(e, traceback.format_exc())
            if kb.kbhit():
                key = kb.getch()
                if ord(key) == 27: # esc
                    break
                if key == 'r':
                    print("reset")
                    encoders.reset()
        encoders.close_port()
    else:
        log.error("Unable to open encoder port %s", serial_port)

    print('End.')


def man():
    parser = argparse.ArgumentParser(description='Encoder gateway')
    parser.add_argument("-t", "--test",
                        dest="testMode",
                        help="Set mode to simulate non-present encoder values")
    parser.add_argument("-l", "--log",
                        dest="logLevel",
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")
    return parser

def testMode(data):
    data = map(int, data)
    m = max(data)
    for idx, d in enumerate(data):
        if d == 0:
           data[idx] = m + random.randint(-4,5)
           if data[idx] < 0:
               data[idx] = 0
    return data
    
if __name__ == "__main__":
    import traceback
    import random
    import argparse
    from kbhit  import KBHit
    main()