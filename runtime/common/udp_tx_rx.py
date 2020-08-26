"""
 udp_tx_rx.py
 
 Simple classes for sending and receiving UDP text messages
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

class Udpsend(object):
    def __init__(self):
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, data, addr):
        self.send_sock.sendto(data, addr)

class UdpReceive(object):

    def __init__(self, port):
        self.in_q = Queue()
        listen_address = ('', port)
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.listen_sock.bind(listen_address)
        t = threading.Thread(target=self.listener_thread, args= (self.listen_sock, self.in_q))
        t.daemon = True
        log.debug("UDP receiver listening on port %d", listen_address)
        t.start()
        
    def available(self):
        return self.in_q.qsize()
 
    def get(self):  # returns address, msg
        if self.available():
            return self.in_q.get_nowait()
        else:
            return None

    def listener_thread(self, listen_sock, in_q ):
        MAX_MSG_LEN = 256
        while True:
            try:
                msg, addr = listen_sock.recvfrom(MAX_MSG_LEN)
                #  print addr, msg
                msg = msg.rstrip()
                self.in_q.put((addr, msg))
            except Exception as e:
                print("Udp listen error", e)
