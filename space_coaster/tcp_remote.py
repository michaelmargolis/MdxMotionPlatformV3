""" TCP remote control """

import sys, traceback
import time
import threading
import os
import socket
try:
    from queue import Queue
except ImportError:
    from Queue import Queue


class TcpRemote(object):
    """ provide action strings associated with UDB messages."""
    auto_conn_str = "MdxRemote_V1"  # remote responds with this when promted for version

    def __init__(self, actions):
        """ Call with dictionary of action strings.
 
        Keys are the strings sent by the remote,
        values are the functons to be called for the given key.
        """
        self.HOST = "localhost"
        self.PORT = 10013
        self.sock = None
        self.client = None
        self.address = None
        self.inQ = Queue()
        self.actions = actions
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((self.HOST, self.PORT))
            print("opening TCP remote control socket on", self.PORT)
            self.sock.listen(1)  # listen for incoming connection
            t = threading.Thread(target=self.listener_thread, args=(self.inQ, self.sock))
            t.daemon = True
            t.start()
        except:
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print("thread init err", e, s)

    def listener_thread(self, inQ, sock):
        MAX_MSG_LEN = 80
        while True:
            self.client, self.address = sock.accept()
            infile = self.client.makefile()
            print("Connection from remote controller at", self.address)
            while self.client:
                try:
                    line = infile.readline()
                    if line and len(line) > 0:
                        inQ.put(line)
                    print(len(line), self.client, infile)
                except:
                    e = sys.exc_info()[0]
                    s = traceback.format_exc()
                    print("listener err", e,s) 
            print(self.client)
    """
    def listener_thread(self, inQ, sock):
        MAX_MSG_LEN = 80
        while True:
            self.connection, self.address = sock.accept()
            print "Connection from remote controller at", self.address
            while self.connection:
                try:
                    for line in self.readlines(self.connection):
                        inQ.put(line)
                except:
                    e = sys.exc_info()[0]
                    s = traceback.format_exc()
                    print "listener err", e, s
                    
    def readlines(self, sock, recv_buffer=4096, delim='\n'):
        infile = sock.makefile()
        while True:
            line = infile.readline()
            if line and len(line) > 0:
                print line
                yield line
            else:
                break
    """   
    """    
        buffer = ''
        data = sock.recv(recv_buffer)
        while data.find(delim) != -1:
            print "d", data
            buffer += data
            if len(buffer) > 0:
               print "b", buffer
            while buffer.find(delim) != -1:
                line, buffer = buffer.split('\n', 1)
                yield line
        return
    """

    def send(self, toSend):
        if self.address:
            try:
                self.sock.sendto(toSend, self.address)
            except:
                print("unable to send to", self.address)

    def service(self):
        """ Poll to service remote control requests."""
        while not self.inQ.empty():
            msg = self.inQ.get().rstrip()
            print(msg)
            if "intensity" in msg:
                try:
                    m,intensity = msg.split('=',2)
                    #print m, "=", intensity
                    self.actions[m](intensity)
                except ValueError:
                    print(msg, "is invalid intensity msg")
            else:
                self.actions[msg]()

if __name__ == "__main__":
    def detected_remote(info):
        print(info)
    def activate():
        print("activate")
    def deactivate():
        print("deactivate") 
    def pause():
        print("pause")
    def dispatch():
        print("dispatch")
    def reset():
        print("reset")
    def deactivate():
        print("deactivate")
    def emergency_stop():
        print("estop")
    def set_intensity(intensity):
        print("intensity ", intensity)
            
    actions = {'detected remote': detected_remote, 'activate': activate,
               'deactivate': deactivate, 'pause': pause, 'dispatch': dispatch,
               'reset': reset, 'emergency_stop': emergency_stop, 'intensity' : set_intensity}
 
    RemoteControl = TcpRemote(actions)
    while True:
         RemoteControl.service()
         time.sleep(.1)
         # RemoteControl.send(str(time.time()))
