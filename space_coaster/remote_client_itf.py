# remote_client_itf
# code to support tcp connection to networked clients

"""
  this module sends commands to the client on the remote PC
  return messages are have msg type as header {telemetry, status, connection, temp}
  return telemetry message:
      frame_nbr, state, is_paused, x,y,z,r,p,y\n
  return status, connection, and temp messages:
     status_string, color
      
      
"""

import time
import sys
import socket
import threading
from Queue import Queue
import traceback

import logging
log = logging.getLogger(__name__)


class ClientNetworkItf(object):
    def __init__(self, ip_addr, port, timeout=0):
        # Create a TCP/IP socket to service remote clients
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception:
            print((sys.exc_info()[0]))
            print(traceback.format_exc())
            raise
        self.eventQ = Queue()  # for incoming client messages
        self.ip_addr = ip_addr
        self.port = port
        self.timeout = timeout
        self.thr = None
        self.is_thr_running = False
        self.is_connected = False
        log.info('Awaiting connection command for %s:%d', self.ip_addr, self.port)


    def connect(self):
        log.info('Attempting to connect to %s:%d', self.ip_addr, self.port)
        try:
            self.sock.settimeout(None)
            self.sock.connect((self.ip_addr, self.port))
            self.is_connected = True
            print("starting thread")
            self.sock.settimeout(timeout)
            self.thr = threading.Thread(target=self.listener_thread, args= (self.sock, self.eventQ,))
            self.thr.daemon = True
            self.thr.start()
            self.is_thr_running = True
            log.info('Connected to %s:%d', self.ip_addr, self.port)
        except socket.error: 
            self.is_connected = False
        except Exception:
            print((sys.exc_info()[0]))
            print(traceback.format_exc())
            print("Error connecting to client", e,s)
            self.is_connected = False
            raise

    def disconnect(self):
        print("starting disconnect")
        self.is_connected = False
        while self.is_thr_running:
            time.sleep(.1)
        if self.thr:
            self.thr.join()
            print("joining tread")
        self.sock.close()
        print("socket closed")


    
    def send_cmd(self, cmd):
        if self.is_connected:
            try: 
               self.sock.sendall(cmd)
            except socket.error as error:
                if error.errno == socket.errno.WSAECONNRESET:
                    log.error("got disconnect error on connection to %s", self.ip_addr)
                    self.disconnect() # kill thread
                elif error.errno == 10057:
                    log.warning("socket not connected, is target running")
                    self.disconnect() # kill thread
                else:
                   self.is_connected = False
                   print("socket error in send")
                   self.disconnect() # kill thread
        else:
            print("wha")


    def service(self):
        pass # 
 
    def listener_thread(self, sock, inQ):
        # This method receives client events 
        msg = ""
        while self.is_connected:
            try:
                msg += sock.recv(512)
                print(("in thread:", msg))
                while True:
                    end = msg.find('\n')
                    if end > 0:
                       inQ.put(msg[:end])
                       # print("in thread", msg[:end])
                       msg = msg[end+1:]
                    else:
                        break
            except socket.timeout:
                pass
            except socket.error: 
               print(("socket error in thread", sys.exc_info()[0]))
               self.is_connected = False
               break
            except Exception:
                print(( "unhandled listener err", sys.exc_info()[0]))
                print((traceback.format_exc()))
        print("wha, killing thread")
        self.is_thr_running = False


import logging.handlers
import logging as log

def start_logging(level):
    log_format = log.Formatter('%(asctime)s,%(levelname)s,%(message)s')
    logger = log.getLogger()
    logger.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler("local_client.log", maxBytes=(10240 * 5), backupCount=2)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    console_handler = log.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)   
    
if __name__ == "__main__":
    import msvcrt # for kbhit
    
    start_logging(logging.DEBUG)
    client = ClientNetworkItf('127.0.0.1', 10015)
    while True:
        try:
            if not client.is_connected:
                client.connect()
            else: 
                print("sending msg")
                client.send_cmd("dispatch")
                client.service()
        except Exception:
            print(( "err", sys.exc_info()[0]))
        if msvcrt.kbhit(): 
            key = msvcrt.getch()
            print("got key", key)
            if ord(key) == 27: # esc
                break
            elif client.is_connected:
                client.send_cmd(str(key))
        time.sleep(.5)
        print("whwwww")
                
    client.disconnect()
