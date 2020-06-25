# tcp_client.py
# code to support tcp connection to networked socket servers

import time
import sys
import socket
import threading
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

import logging
log = logging.getLogger(__name__)

class Status():
    def __init__(self):
        self.connected = False  # set True when client is connected
        self.thr_running = False # True when thread is running
    
    
class SockClient():
    def __init__(self, ip_addr, port):
        self.in_queue = Queue()  # for incoming messages
        self.ip_addr = ip_addr
        self.port = port
        self.thr = None
        self.sock = None
        self.status = Status()
        log.debug('TCP client ready to connect to %s:%d', self.ip_addr, self.port)

    def connect(self):
        log.debug('Attempting to connect to %s:%d', self.ip_addr, self.port)
        # Create a TCP/IP socket to service remote clients
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        except Exception as e:
            log.error("error creating client socket %s", e)
            raise
        try:
            #  self.sock.connect((self.ip_addr, self.port))
            self.sock = socket.create_connection((self.ip_addr, self.port),1) # timeout after one second
            self.status.connected = True
            self.thr = threading.Thread(target=self.listener_thread, args= (self.sock, self.in_queue,self.status,))
            self.thr.daemon = True
            self.thr.start()
            self.status.running = True
            log.info('Connected to %s:%d', self.ip_addr, self.port)
            return True
        except socket.error as e: 
            self.status.connected = False
            log.debug("client socket error %s", e)
            self.sock.close()
            return False
        except Exception as e:
            log.error("Error connecting to client %s", e)
            self.status.connected = False
            raise

    def disconnect(self):
        self.status.connected = False
        while self.status.thr_running:
            time.sleep(.1)
            # print("*", end =" ")
        log.debug("thread no longer running")
        # if self.thr:
        #    self.thr.join()
        if self.sock:
            self.sock.close()
        log.debug("client socket closed")

    def send(self, msg):
        if self.status.connected:
            try: 
               self.sock.sendall(msg.encode("utf-8"))
               log.debug("sent: %s", msg )
            except socket.error as error:
                if error.errno == socket.errno.WSAECONNRESET:
                    log.error("got disconnect error on connection to %s", self.ip_addr)
                elif error.errno == 10057:
                    log.warning("socket not connected, is target running")
                else:
                   log.error("error in client socket send");
                self.disconnect() # kill thread
        else:
            log.debug("unable to send because not connected ->%s ", msg)

    def available(self):
        return self.in_queue.qsize()
 
    def receive(self):
        if self.available():
            return self.in_queue.get()
        else:
            return None

    def service(self):
        pass # 
 
    def listener_thread(self, sock, inQ, status):
        # This method receives client events 
        msg = ""
        while status.connected:
            try:
                msg += sock.recv(512).decode("utf-8")
                while True:
                    end = msg.find('\n')
                    if end > 0:
                       inQ.put(msg[:end])
                       # log.debug("in client thread, msg=%s", msg[:end])
                       msg = msg[end+1:]
                    else:
                        break
            except socket.error as e: 
               log.error("socket error in thread %s", e)
               status.connected = False
               break
            except Exception as e:
                log.error("unhandled listener thread err %s", e)
        log.debug("terminating tcp client thread")
        status.running = False

##################  test code when run from main ################
from datetime import datetime
def millis():
    dt = datetime.now()
    return  int(dt.microsecond/1000)
 
def latency_test(addr):
    # this code sends a time stamp and waits for a reply with a server
    # time stamp appended. difference between the time stamps is printed
    client = SockClient(addr, 10015)
    while True:
        try:
            if not client.status.connected:
                client.connect()
                client.send(str(millis()) +'\n' )
        except Exception as e:
             print(e)
        if client.status.connected:
            if client.available() > 0:
                m = client.receive()
                print("got", m)
                vals = m.split(',')
                latency = []
                now = millis()
                for v in vals:
                    try:
                        t = int(v)
                        if now < t:
                            latency.append(t-now) # rollover
                        else:    
                            latency.append(now-t)
                    except Exception as e:
                        print(e)
                # delta between first element and time now is total latency 
                print("latency (ms)", latency[0])
                time.sleep(0.05)
                client.send(str(millis()) + '\n')
                
        if msvcrt.kbhit(): 
            key = msvcrt.getch()
            if ord(key) == 27: # esc
                break
    client.disconnect()


def coaster_test(addr):
    client = SockClient(addr, 10015)
    while True:
        try:
            if not client.status.connected:
                client.connect()
            else: 
                msg = "telemetry"
                print("sending msg:",  msg)
                client.send(msg)
                client.service()
        except Exception as e:
            print( "err", str(e))
        if msvcrt.kbhit(): 
            key = msvcrt.getch()
            if ord(key) == 27: # esc
                return
            elif client.status.connected:
                if key == 'd': cmd = 'dispatch'
                elif key == 'p': cmd = 'pause'
                elif key == 'r': cmd = 'reset'
                else: cmd == str(key)
                client.send(cmd)
        time.sleep(.5)
        while True:
            event = client.receive()
            if event:
                print("got:", event)
            else:
                break
    client.disconnect()

def man():
    parser = argparse.ArgumentParser(description='TCP client latency test mode')
    parser.add_argument("-l", "--log",
                        dest="logLevel",
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")
    parser.add_argument("-a", "--addr",
                        dest="address",
                        help="Set the target ip address")
    return parser
    
if __name__ == "__main__":
    import msvcrt # for kbhit  
    import argparse
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
    if args.address:
        latency_test(args.address)
        # coaster_test(args.address)
    else:
        latency_test('127.0.0.1')
        # coaster_test('127.0.0.1')




