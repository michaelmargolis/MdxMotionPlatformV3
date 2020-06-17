"""
nl2_datalink.py

code for communicating with nl2 telemetry using TCP or Serial
"""

from time import time,sleep
from struct import *
#import collections
import sys
import threading
try:
    from queue import Queue
except ImportError:
    from Queue import Queue
import ctypes #  for bit fields
import os
import traceback


ethernet_address = "127.0.0.1"
com_port = "COM13"
use_ethernet = True

if use_ethernet:
  import socket
else:
  import serial
  import os
  
class NL2Datalink(object):
    def __init__(self, queue):
        self.nl2Q = queue
        print "use_ethernet flag is", use_ethernet
        if use_ethernet:
            self.nl2_msg_buffer_size = 255
            self.nl2_msg_port = 15151
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.settimeout(0.5)
            self.nl2Q = Queue()
            t = threading.Thread(target=self.listener_thread, args= (self.sock,))
            t.daemon = True
            t.start()
        else:
            self.ser = None
            self.ser_buffer = ""
            self.baud_rate = 230400
            try:
                self.ser = serial.Serial(com_port, self.baud_rate)
                print "opened serialport", com_port
                print self.ser.read
                sleep(2)
                reader = ReadMessage(self.ser.read, self.nl2Q)
                t = threading.Thread(target=self.rx_thread, args=(reader,))
                t.daemon = True
                t.start()
            except:
                e = sys.exc_info()[0]  # report error
                s = traceback.format_exc()
                print e, s
                self.ser = None
                print "unable to open serial port:", com_port
            # self.timeout_period = 1
      

    def connect(self):
        print "todo connect"
        if use_ethernet:
           pass
        else:
           pass
        return True

    def send(self, toSend):
        msg, requestId, size = (unpack('>HIH', toSend[1:9]))
        print "sending:", msg, requestId
        # above just for debug
        if use_ethernet:
            print "socket send todo"
            try:
                self.sock.sendall(toSend)
            except:
                e = sys.exc_info()[0]  # report error
                print e
        else:
            if self.ser:
                if self.ser.isOpen() and self.ser.writable:
                    self.ser.write(toSend)
                    self.ser.flush()
                    return
            print "unable to send message"

    

    def listener_thread(self, sock):
        """ received msgs added to queue, telemetry requests sent on socket timeout """
        while True:
            try:
                msg = data = None
                data = sock.recv(self.nl2_msg_buffer_size)
                if data:
                     msg, requestId, size = (unpack('>HIH', data[1:9]))
                     self.nl2Q.put((msg, requestId, data, size))
                     #print msg, requestId,  ((time() - self.start_time)*1000) -requestId 
                     # todo - perhaps check time of most recent incoming telemetry msg and issue fresh request if greater than timeout time
            except socket.timeout:
                self._send(self._create_simple_message(self.N_MSG_GET_TELEMETRY, self._get_msg_id()))
                # print "timeout in listener"
            except:
                if msg:
                    print "bad msg:",msg, "len=", len(msg)
                elif data: 
                    print "bad data",data
                e = sys.exc_info()[0]
                s = traceback.format_exc()
                print "listener thread err", e, s

    def rx_thread(self, reader):
        print "in serial rx thread"
        while True:
            #  wait forever for data to forward to client
            try:
                reader.read_msg()
            except:
                print "serial error"


class ReadMessage(object):
    #  returns message or None if invalid or no message
    def __init__(self, reader, queue):
        self.read = reader
        self.queue = queue
    
    def read_msg(self):
        #print "in readmsg, reader=", self.read
        header = bytearray(9)
        try:
            header[0] = self.read(1)
            if header[0] == 0x4e:
                print "got header"
                sleep(2)
            if header[0] != 0x4e:
                print ".",  #header[0], hex(header[0])
                return
            print "in reader, got prefix"
            for i in range(8):
                header[i+1] = self.read(1)
            msg, requestId, size = (unpack('>HIH', header[1:9]))
            print "in reader, msg,size=", msg, size, type(size)
            data = self.read(size)
            print len(data),
            print ":".join("{:02x}".format(ord(c)) for c in data)
            sleep(2) 
            self.queue.put((msg, requestId, data, size))
        except:
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print "read msg err", e, s
            return


if __name__ == "__main__":
    #  identifyConsoleApp()
    coaster = CoasterInterface()
    coaster_thread = threading.Thread(target=coaster.get_telemetry)
    coaster_thread.daemon = True
    coaster_thread.start()

    while True:
        if raw_input('\nType quit to stop this script') == 'quit':
            break
