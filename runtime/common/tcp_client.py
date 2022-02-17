"""
 tcp_client.py
 code to support tcp connection to networked socket servers
 """

import time
import sys
import socket
import threading
import traceback
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

import logging
log = logging.getLogger(__name__)

class Status():
    def __init__(self):
        self._connected = False  # set True when client is connected
        self._thr_is_alive = False
        self.mutex = threading.Lock()

    @property 
    def is_connected(self):
        self.mutex.acquire()
        state = self._connected
        self.mutex.release()
        return state

    @is_connected.setter
    def is_connected(self, state):
        log.debug("previous connection state %s, new state now %s", str(self._connected), str(state))
        self.mutex.acquire()
        self._connected = state
        self.mutex.release()

    @property 
    def is_thr_alive(self):
        self.mutex.acquire()
        state = self._thr_is_alive
        self.mutex.release()
        return state

    @is_thr_alive.setter
    def is_thr_alive(self, state):
        self.mutex.acquire()
        self._thr_is_alive = state
        self.mutex.release()

class TcpClient(object):
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
            self.status.is_connected = True
            self.thr = threading.Thread(target=self.listener_thread, args= (self.sock, self.in_queue,self.status,))
            self.thr.daemon = True
            self.thr.start()
            self.status.thr_is_alive = True
            log.debug('Connected to %s:%d', self.ip_addr, self.port)
            return True
        except socket.error as e: 
            self.status.is_connected= False
            log.info("client socket connect error %s", e)
            self.sock.close()
            # print(traceback.format_exc())
            return False
        except Exception as e:
            log.error("Error connecting to client %s", e)
            self.status.is_connected= False
            raise

    def disconnect(self):
        self.status.is_connected = False
        while self.status.is_thr_alive:
            time.sleep(.1)
            # print("*", end =" ")
        log.debug("thread no longer running")
        # if self.thr:
        #    self.thr.join()
        if self.sock:
            self.sock.close()
        log.debug("client socket closed")

    def get_addr(self): # fixme
        return (self.ip_addr, self.port )  
        
    def send(self, msg):
        if self.status.is_connected:
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
        if self.available() > 0:
            return self.in_queue.get_nowait()
        else:
            return None

    def service(self):
        pass # 
 
    def listener_thread(self, sock, inQ, status):
        # This method receives client events 
        buffer = ""
        while status.is_connected:
            try:
                buffer += sock.recv(1024).decode("utf-8")
                while True:
                    #  end = buffer.find('\n')
                    #  if end > 0:
                    line, sep, buffer = buffer.partition('\n')
                    if len(line):
                       print("in thread", line)
                       inQ.put(line)
                    #  inQ.put(msg[:end])
                    #  log.debug("in client thread, msg=%s", msg[:end])
                    #  msg = msg[end+1:]
                    else:
                        break
            except socket.timeout:
                pass
            except socket.error as e: 
               log.error("socket error in tcp client thread %s", e)
               status.is_connected = False
               break
            except Exception as e:
                log.error("unhandled listener thread err %s", e)
        log.debug("terminating tcp client thread")
        status.thr_is_alive = False

##################  test code when run from main ################

def millis():
    return  int(time.perf_counter() * 1000)
 
def latency_test(addr, port = 10015, id = 0):
    # this code sends a time stamp and waits for a reply with a server
    # time stamp appended. difference between the time stamps is printed
    log.info("running letency test to " + str((addr, port)))
    client = TcpClient(addr, port)
    prev_send = 0
    while True:
        try:
            if not client.status.is_connected:
                client.connect()
                log.info("tcp client connected to %s", addr)
                client.send(format("%d,%d\n" % (id, millis())))
        except Exception as e:
             print(e)
        if client.status.is_connected:
            if client.available() > 0:
                m = client.receive()
                vals = m.split(',')
                if vals[0] == str(id):
                    now = millis()
                    try:
                        t = int(vals[1])
                        if now < t:
                            latency = t-now # rollover
                        else:    
                            latency = now-t
                    except Exception as e:
                        print(e)
                        latency = -1
                    # delta between first element and time now is total latency 
                    print("latency (ms)", latency)
            if millis() - prev_send > 50:
                client.send(format("%d,%d\n" % (id, millis())))
                prev_send = millis()
                
        if kb.kbhit(): 
            key = kb.getch()
            if ord(key) == 27: # esc
                break
    client.disconnect()


def coaster_test(addr, port= 10015):
    log.info("running coaster test to " + str((addr, port)))
    client = TcpClient(addr, port)
    while True:
        try:
            if not client.status.is_connected:
                client.connect()
            else: 
                msg = "telemetry\n"
                client.send(msg)
                client.service()
        except Exception as e:
            print( "err", str(e))
        if kb.kbhit(): 
            key = kb.getch()
            if ord(key) == 27: # esc
                return
            elif client.status.is_connected:
                cmd = None
                if key == 'd': cmd = 'dispatch'
                elif key == 'p': cmd = 'pause'
                elif key == 'r': cmd = 'reset'
                else: cmd == str(key)
                if cmd:
                    client.send(cmd)
        time.sleep(.5)
        if client.available():
            event = client.receive()
            if event:
                print("got:", event)
            else:
                break
    print("disconnecting")
    client.disconnect()


def echo_test(addr, port= 10015):
    log.info("running echo test to " + str((addr, port)))
    client = TcpClient(addr, port)
    while True:
        try:
            if not client.status.is_connected:
                client.connect()
            else: 
                client.service()
        except Exception as e:
            print( "err", str(e))
        if kb.kbhit(): 
            key = kb.getch()
            if ord(key) == 27: # esc
                return
            elif client.status.is_connected:
                cmd = None
                if key == 'd': cmd = 'dispatch'
                elif key == 'p': cmd = 'pause'
                elif key == 'r': cmd = 'reset'
                else: cmd == str(key)
                if cmd:
                    client.send(cmd)

        event = client.receive()
        if event:
            print("got:", event)

    print("disconnecting")
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
    
if __name__ == "__main__":
    from kbhit  import KBHit
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
    if args.port:
        port = int(args.port)
    else:
        port = 10015 
    if args.id:
        id = int(args.id)
        print("id=", id)
    else:
        id = 0 
        
    kb = KBHit()
    if args.address:
        latency_test(args.address, port, id)
        # coaster_test(args.address, port)
    elif args.echo:
        echo_test('127.0.0.1', port) # todo add non local addresses
    else:
        # latency_test('127.0.0.1', port, id)
        coaster_test('127.0.0.1', port )




