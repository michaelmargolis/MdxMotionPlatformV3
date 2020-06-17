""" Serial remote control """

import sys
import serial
import time
import serial.tools.list_ports


ser = None
ser_buffer = ""
baud_rate = 57600
timeout_period = 2


def search():
    for p in sorted(list(serial.tools.list_ports.comports())):
        port = p[0] 
        print port, len(port)
        if connect(port):
            return port
    return None

def connect(portName):
    # Private method try and connect to the given portName.
    global ser 
    connected = False
    ser = None
    result = ""
    try:
        ser = serial.Serial()
        ser.port = portName
        ser.baudrate = baud_rate
        ser.timeout = timeout_period
        ser.setDTR(False)
        ser.open()
        if not ser.isOpen():
            print "Connection failed:", portName, "has already been opened by another process"
            ser = None
            return False
        ser.flush()
        time.sleep(.1)
        print "Looking for Remote control on ", portName
        ser.write('V')
        time.sleep(.1)

        while True:
            result = ser.readline()
            if len(result) > 0:
                print "serial data:", result
            if "MdxRemote_V1" in result or "deactivate" in result:
                print "found remote"
                return True
            if len(result) < 1:
                break
        ser.close()
    except:
        ser = None
        pass
    return False

def send(toSend):
    # private method sends given string to serial port
    if ser:
        if ser.isOpen() and ser.writable:
            ser.write(toSend)
            ser.flush()
            return True
    return False

