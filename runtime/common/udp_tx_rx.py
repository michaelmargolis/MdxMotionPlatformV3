"""
 udp_tx_rx.py
 
 single threaded classes for sending and receiving UDP text messages
"""

import socket
import threading
import traceback
import signal

try:
    #  python 3.x
    from queue import Queue
except ImportError:
    #  python 2.7
    from Queue import Queue

import logging
log = logging.getLogger(__name__)

class UdpSend(object):
    def __init__(self):
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, data, addr):
        self.send_sock.sendto(data, addr)

class UdpReceive(object):

    def __init__(self, port):
        self.in_q = Queue()
        listen_address = ('', port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.sock.bind(listen_address)
        t = threading.Thread(target=self.listener_thread, args= (self.sock, self.in_q))
        t.daemon = True
        log.debug("UDP receiver listening on port %d", listen_address[1])
        t.start()
        
    def available(self):
        return self.in_q.qsize()
 
    def get(self):  # returns address, msg
        if self.available():
            return self.in_q.get_nowait()
        else:
            return None

    def send(self, data, addr):
        self.sock.sendto(data.encode('utf-8'), addr)    

    def listener_thread(self, sock, in_q ):
        MAX_MSG_LEN = 256
        while True:
            try:
                msg, addr = sock.recvfrom(MAX_MSG_LEN)
                #  print addr, msg
                msg = msg.decode('utf-8').rstrip()
                self.in_q.put((addr, msg))
            except Exception as e:
                print("Udp listen error", e)


""" the following is for testing """
    
def man():
    parser = argparse.ArgumentParser(description='UDP tx rx tester')
    parser.add_argument("-l", "--log",
                        dest="logLevel",
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")
    parser.add_argument("-a", "--addr",
                        dest="address",
                        help="Set the target ip address")
                        
    parser.add_argument("-p", "--port",
                        dest="port",
                        help="Set the target socket port")

    parser.add_argument("-i", "--id",
                        dest="id",
                        help="Set this client id (used in latency test")
    
    parser.add_argument("-e", "--echo",
                        dest="echo",
                        help="do echo test")    
    return parser
 

def echo_target(addr, port = 10015):
    udp = UdpReceive(port)
    while True:
        if udp.available():
            msg = udp.get()
            print("got msg ", msg)
            udp.send(msg[1], msg[0]) # echo
    
def echo_sender(address, port = 10015 ):
    print("udp sender")
    udp = UdpReceive(port+1)
    for i in range(100):
        udp.send(str(time.time()), (address, port)) #  echo
        time.sleep(.00001)
 
if __name__ == "__main__":
    from kbhit  import KBHit
    import argparse
    import time
    args = man().parse_args()
    print(args)
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%H:%M:%S')
    if args.logLevel:
        level = args.logLevel
    else:
        level = 'DEBUG'
    print(level, "logging level")
    log.setLevel(level)
    
    if args.port:
        port = int(args.port)
    else:
        port = 10020 
        
    if args.address:
        address = args.address
    else:
        address = '127.0.0.1'
    if args.id:
        id = int(args.id)
        print("id=", id)
    else:
        id = 0 
        
    kb = KBHit()

    if args.echo:
        echo_target(address, port) 
    else:
        # send msgs with sequential 
        echo_sender(address, port )