"""
Fan interace module

Sends percent fan speed to serial port

"""

from __future__ import print_function
import sys
import time
import traceback
import serial
import serial.tools.list_ports
from nl2_telemetry_only import *
import interpolate
import fan_config as fan_cfg

def scale(val, src, dst) :  # the Arduino 'map' function written in python
    return (val - src[0]) * (dst[1] - dst[0]) / (src[1] - src[0])  + dst[0]


class FanController():

    def __init__(self, get_power_limits):
        self.get_power_limits  = get_power_limits # callback for min and max power %
        self.ser = None
        self.connected = True # todo we are not yet checking for connection so force true
        self.ser_buffer = ""
        self.baud_rate = 57600
        self.timeout_period = 1
        self.interp = interpolate.Interpolate(fan_cfg.speeds, fan_cfg.power)
        self.speed_threshold = fan_cfg.threshold_speed  # speeds below this will not use fan

    def set_speed_threshold(self, threshold_speed):
        self.speed_threshold = threshold_speed

    def set_fan_speed(self, coaster_speed):
        if coaster_speed > self.speed_threshold:
            fan_power = self.interp(coaster_speed)
            fan_power = scale(fan_power, (0,100), self.get_power_limits())
        else:
            fan_power = 0
        msg = format("power=%d" % (fan_power))
        print(msg)
        self.send_serial(msg)
        return fan_power

    def connect_serial(self, port):
        try:
            if port == None:
                print("Serial port not defined")
                sys.exit()
            print("opening",port,  end=' ')
            self.ser = serial.Serial(port, self.baud_rate)
            # print(" opened ", end='')
            self.ser.timeout = self.timeout_period
            if not self.ser.isOpen():
                print(" Connection failed:", port, "has already been opened by another process", end='')
                self.ser = None
                raise SystemExit
            self.ser.flush()
            sleep(0.5)
            data = self.ser.readline()
            if "fan" in data:
                return True
            else:
               print(format(" port %s does not appear to be a fan" % port), end='')
        except SystemExit:
            raise
        except:
            self.ser = None
        print()
        return False



    def select_port(self):
        is_selected = False
        while True:
            try:
                ports = self.list_ports()
                if len(ports) == 1:
                    is_selected = fan.connect_serial(ports[0])
                    if is_selected:
                         break
                #  if fan.connect_serial(fan_cfg.com_port):
                #      break;
                elif len(ports) > 1:
                    print()
                    for i in range(len(ports)):
                       print(format(" (%d) %s" % (i+1, ports[i]))),
                    print()
                    index = raw_input("Enter the index of the desired port (or 0 to exit)")
                    print(index)
                    if(index == '0'):
                        is_selected = False
                        break
                    index = int(index)-1
                    if index >= 0 and index < len(ports):
                        is_selected = self.connect_serial(ports[index])
                        if is_selected:
                            break
                else:
                    port = raw_input(format("unable to connect to %s\nConnect controller and hit enter, or enter another port " % (fan_cfg.com_port)))
                    if port != "":
                        fan_cfg.com_port = port
            except SystemExit:
                is_selected = false
            break
        return is_selected

    def list_ports(self):
        ch340_ports = []
        for p in sorted(list(serial.tools.list_ports.comports())):
            port = p[0]
            #print "p[0]", p[0], "p[1]", p[1],"p[2]", p[2]
            if 'USB-SERIAL CH340' in  p[1]: 
                #print("found USB-SERIAL CH340 on port", port)
                ch340_ports.append(port)
            #  if 'PID=1A86:7523' in p[2]:
            #    print("found Serial PID")
            #    port.append(port)
        return ch340_ports 

    def send_serial(self, toSend):
        try:
            if self.ser and self.connected :
                if self.ser.isOpen():
                    self.ser.write(toSend)
                    self.ser.flush()
                    return True
            else:
                print("serial not connected")
                return False
        except:
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print("Error sending serial data",e,s)
            #self.self.system_status.is_nl2_connected = False


def get_power_limits():
    return (13,70)  # min and max percent range to send
    
if __name__ == "__main__":
    #  identifyConsoleApp()
    
    # for i in range(40):
    #   print(i, fan_cfg.interp(i))

    fan = FanController(get_power_limits)
    coaster = CoasterInterface()
    coaster.begin()
    abort = False

    abort = not fan.select_port() # returns true if comms opened ok
    
    # fan.set_fan_speed(0)  # arm esc
    # sleep(5)
    
    if abort == False:
        print("serial connected")
        coaster.connect_to_coaster('localhost')  # this assumes nl2 running on this PC
    
    while abort == False:
        coaster.service()
        telemetry_data = coaster.get_telemetry(.2)  # argument is timeout value
        if telemetry_data and len(telemetry_data) == 2:
            if coaster.system_status.is_in_play_mode:
                speed = telemetry_data[0]
                #  print("coaster speed is ", speed, "m/s")
                if coaster.system_status.is_paused == False:
                    fan.set_fan_speed(speed)
                else:
                    fan.set_fan_speed(0)  # coaster is paused
            else:
                print("Coaster not in play mode")
                fan.set_fan_speed(0)
            """ 
            if telemetry_data[1] and len(telemetry_data[1]) == 6:  # check if we have data for all 6 DOF
                #  print(telemetry_data[1])  # show orientation
                pass  
            """
        else:
            if coaster.system_status.is_nl2_connected:
                print("Telemetry error: %s" % coaster.get_telemetry_err_str())
            else:
                print("No connection to NoLimits, is it running?")
                abort = True
        sleep(0.2)

