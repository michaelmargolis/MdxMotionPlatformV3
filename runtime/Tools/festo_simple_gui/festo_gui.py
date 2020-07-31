#!/usr/bin/python

import sys, os
import traceback
import Tkinter as tk
import tkMessageBox
import ttk
import socket
import time
import copy
from fstlib import easyip

# Set the socket parameters
FST_ip = '192.168.0.10' # default IP, can be changed using cmd line argument
FST_port = easyip.EASYIP_PORT
bufSize = 1024

WAIT_FESTO_RESPONSE = False # waits for response from festo messages
SHOW_FESTO_PRESSURE = True # above must also be set to True
PRINT_PRESSURE_DELTA = False; # todo fix div when pressure is zero
MAX_PRESSURE = 6000.0  # used for scaling slow moves
isRunning = True

class FestoTest(object):
    def __init__(self):
        self.FSTs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.FST_addr = (FST_ip, FST_port)
        print "Using Festo controller socket at",  FST_ip, FST_port
        self.FSTs.bind(('0.0.0.0', 0))
        self.FSTs.settimeout(1)  # timout after 1 second if no response
        self.activate_piston_flag = 0  # park piston is extended when flag set to 1, parked when 0
        self.levels = [0, 0, 0, 0, 0, 0]
        self.off = [0, 0, 0, 0, 0, 0]
        self.is_enabled = False

    def init_gui(self, master):
        self.master = master
        frame = tk.Frame(master)
        frame.pack()

        self.label0 = tk.Label(frame, text="Adjust Muscle Pressures")
        self.label0.pack(fill=tk.X, pady=10)

        slider_frame = tk.Frame(master)
        slider_frame.pack(fill=tk.X, side=tk.TOP, pady=10)

        self.pressure_readings = []
        sLabels = ("1", "2", "3", "4", "5", "6")
        for i in range(6):
            sframe = tk.Frame(slider_frame)
            sframe.pack(fill=tk.X, side=tk.LEFT, pady=10)        
            s = tk.Scale(sframe, from_=6000, to=0, resolution=50, length=200,
                         command=lambda g, i=i: self.set_value(i, g), label=sLabels[i])
            s.set(0)
            s.pack(anchor = tk.W, padx=(6, 4))
            
            self.pressure_readings.append( tk.StringVar())
            p = tk.Label(sframe, text= str(i), fg="slate gray", textvariable=self.pressure_readings[i])
            p.pack(side=tk.BOTTOM )
            #self.pressure_readings[i].set(format("%4d" % (i*1000)))
            
        self.pistonState = tk.StringVar()
        self.pistonState.set('disable')

        frame2 = tk.Frame(master)
        frame2.pack(fill=tk.X, side=tk.TOP, pady=10)

        self.piston_cb = tk.Checkbutton(frame2, text="Piston", command=self.piston,
                                        variable=self.pistonState, onvalue='enable', offvalue='disable')
        self.piston_cb.pack(side=tk.TOP)

        frame3 = tk.Frame(master)
        frame3.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
        
        self.status_text = format("Using Festo address: %s  port %d" % (FST_ip, FST_port))
        self.status_Label = tk.Label(frame3, text=self.status_text, fg="slate gray")
        self.status_Label.pack()

        self.enableState = tk.StringVar()
        self.enableState.set('disable')
        self.enable_cb = tk.Checkbutton(frame3, text="Enable Festo Messages", command=self.enable,
                                        variable=self.enableState, onvalue='enable', offvalue='disable')
        self.enable_cb.pack(side=tk.LEFT, padx=160)

        self.close_button = tk.Button(frame3, text="Quit", command=self.quit)
        self.close_button.pack(side=tk.LEFT, padx= 10)

    def piston(self):
        if self.pistonState.get() == 'enable':
            self.activate_piston_flag = 1;
            if self.is_enabled:
                self.send(self.levels)
                print("Piston activated")
            else:
                 print("Piston activated but Festo messages are disabled")
        else:
            self.activate_piston_flag = 0
            if self.is_enabled:
                self.send(self.levels)
                print("Piston deactivated")
            else:
                print("Piston deactivated but Festo messages are disabled")
 
    def enable(self):
        #self.master.update_idletasks()
        if self.enableState.get() == 'enable':
            self.is_enabled = True
            self.status_Label.config(fg="green3")
            self.master.update()
            print("Enabling Festo messages")
            self.slow_move(self.off, self.levels, 2000)
        else:
            self.is_enabled = False
            self.status_Label.config(fg="slate gray")
            self.master.update()
            print("Disabling Festo messages")
            self.slow_move(self.levels, self.off, 2000)
 
    def slow_move(self, start, end, duration):
        begin_max = max(start)
        end_max = max(end)
        if begin_max > end_max:
            scale = begin_max / MAX_PRESSURE
        else:
            scale = end_max / MAX_PRESSURE
        interval = 50  # time between steps in ms
        duration = duration * scale
        steps = int(duration) / interval
        if steps < 1:
            self.send(end)
        else:
            current = start
            print "In controller: moving from", start, "to", end, "steps", steps
            delta = [(e - s)/steps for s, e in zip(start, end)]
            for step in xrange(steps):
                current = [x + y for x, y in zip(current, delta)]
                for idx, val in enumerate(current):
                    if current[idx] < 0 :
                        current[idx] = 0
                # print current
                self.send(copy.copy(current))
                time.sleep(interval / 1000.0)

    def set_value(self, idx, value):
        self.levels[idx] = int(value)
        if self.is_enabled:
            self.send(self.levels)

    def quit(self):
        global isRunning
        isRunning = False

    def send(self, muscle_pressures):
        try:
            msg = copy.copy(muscle_pressures)
            msg.append(self.activate_piston_flag)
            print "Festo values:",  msg
            packet = easyip.Factory.send_flagword(0, msg)
            try:
                self.send_packet(packet)
                #  print "festo output:", packet, FST_port
                if SHOW_FESTO_PRESSURE:
                    self.actual_pressures = self._get_pressure()
                    if len(self.actual_pressures) >= 6:
                        for i in range(6):
                            self.pressure_readings[i].set(format("%4d" % (self.actual_pressures[i])))
                            if PRINT_PRESSURE_DELTA:
                                delta = [act - req for req, act in zip(muscle_pressures[:6], self.actual_pressures[:6])]
                                self.pressure_percent = [int(d * 100 / req) for d, req in zip(delta, muscle_pressures[:6])]
                                print muscle_pressures, delta, self.pressure_percent

            except socket.timeout:
                print "timeout waiting for replay from", self.FST_addr
        except:
            e = sys.exc_info()[0]
            s = traceback.format_exc()
            print "error sending to Festo", e, s

    def send_packet(self, packet):
        if self.is_enabled :
            data = packet.pack()
            #  print "sending to", self.FST_addr
            # print(":".join("{:02x}".format(ord(c)) for c in data))
            self.FSTs.sendto(data, self.FST_addr)
            if WAIT_FESTO_RESPONSE:
                #  print "in sendpacket,waiting for response..."
                data, srvaddr = self.FSTs.recvfrom(bufSize)
                resp = easyip.Packet(data)
                #  print "in senddpacket, response from Festo", resp
                if packet.response_errors(resp) is None:
                    self.netlink_ok = True
                    self.status_Label.config(text=self.status_text, fg='green3')
                    #  print "No send Errors"
                else:
                    self.netlink_ok = False
                    t = format("Festo send errors=%r" % packet.response_errors(resp))
                    self.status_Label.config(text=t, fg='red')
            else:
                resp = None
            return resp

    def _get_pressure(self):
        # first arg is the number of requests your making. Leave it as 1 always
        # Second arg is number of words you are requesting (probably 6, or 16)
        # third arg is the offset.
        # words 0-5 are what you sent it.
        # words 6-9 are not used
        # words 10-15 are the current values of the presures
        # packet = easyip.Factory.req_flagword(1, 16, 0)
        try:
            packet = easyip.Factory.req_flagword(1, 6, 10)
            resp = self.send_packet(packet)
            if resp:
                values = resp.decode_payload(easyip.Packet.DIRECTION_REQ)
                #  print list(values)
                return list(values)
        except socket.timeout:
            print "timeout waiting for Pressures from Festo"
        return [0,0,0,0,0,0]

def main():
    global FST_ip, isRunning
    if len(sys.argv) > 1:
        print(sys.argv[1])
        FST_ip = sys.argv[1]
    festo = FestoTest()

    try:
        root = tk.Tk()
        if festo.init_gui(root) == False:
            print("init gui returned false")
            exit() 
        while os.system("ping " + ("-n 1 " if  sys.platform =="win32" else "-c 1 ") + FST_ip) != 0:
           msg = FST_ip + " not responding, check network connection and try again"
           if tkMessageBox.askretrycancel("Connection Error", msg) == False:
               print(msg)
               return 
    except:
        e = sys.exc_info()[0]  # report error
        s = traceback.format_exc()
        print e, s

    print "starting main service loop"
    while isRunning:
        root.update_idletasks()
        root.update()

if __name__ == "__main__":
    main()


