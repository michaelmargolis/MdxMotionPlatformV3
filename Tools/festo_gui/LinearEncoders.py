#!/usr/bin/python
"""
LinearEncoders.py

"""

import serial
import time
import serial.tools.list_ports
import threading
import os
from Queue import Queue
import traceback


class Encoder(object):

    def __init__(self):
        self.ser = None
        self.readings = None
        self.timeout = None
        self.is_connected = False
        self.RxQ = Queue()

    def connect(self, com_port, baud, _timeout):
        """
        Open serial port
            com_port: serial port name string
            baud: integer baud rate
            timeout:  max wait time in seconds as float
        """
        self.timeout = _timeout
        try:
            self.ser = serial.Serial(com_port, baud, timeout=_timeout)
            self.is_connected = True
            t = threading.Thread(target=self.rx_thread, args=(self.ser, self.RxQ,))
            t.daemon = True
            t.start()
            return True
        except serial.SerialException:
            return False
        except Exception as e: 
            s=traceback.format_exc()
            print(str(e), s)
        return False
        
    def disconnect(self):
        """ close serial port """
        self.ser.close()
        self.ser = None
        self.is_connected = False
        print("serial port closed")

    def read(self, command = "", delay=0):
        """
          command: string to trigger a sensor reading or "" of none
          delay in seconds or 0 if none
           returns:  data from rx queue
        """
        if command != "":
            self.send(command)
            if delay > 0:
                time.sleep(delay)
        if self.RxQ.empty():
            return None
        else:    
            return self.RxQ.get().rstrip()

    def send(self, toSend):
        if self.ser and self.is_connected :
            if self.ser.isOpen() and self.ser.writable:
                self.ser.write(toSend)
                self.ser.flush()
                return True
        return False

    def get_serial_ports(self):
       return sorted(list(serial.tools.list_ports.comports()))

    def rx_thread(self, ser, RxQ):
        while self.is_connected:
            #  wait forever for data to forward to client
            try:
                result = self.ser.readline()
                if len(result) > 0:
                    self.RxQ.put(result)
            except:
                print "serial error, trying to reconnect"
                self.RxQ.put("Reconnect Remote Control")
                while True:
                    port = self._search()
                    if port != None:
                        self.RxQ.put("Detected Remote Control on %s" % port)
                        break
        print("serial rx thread terminated")


def main():
    port = "COM28"
    try:
        encoders = Encoder()
        if encoders.connect(port, 57600, 0):
           while True:
               readings = encoders.read()
               if readings != None:
                    print(readings)
                    time.sleep(20)
        else:
           print("unable to connect to", port)
           for p in encoders.get_serial_ports():
               print p



    except Exception as e:
        s = traceback.format_exc()
        print(str(e), s)


if __name__ == "__main__":
    main()
