#!/usr/bin/python

import sys, os
import traceback
import Tkinter as tk
import tkMessageBox
import ttk
import socket
import time
import copy
import LinearEncoders
import config as cfg  # configuration data


sys.path.insert(0,'..')  # fstlib is in the parent dir
from fstlib import easyip  

fst_bufSize = 1024
FST_port = easyip.EASYIP_PORT

MAX_PRESSURE = 6000.0  # used for scaling slow moves
isRunning = True
root = None

class FestoTest(object):
    def __init__(self):
        self.FSTs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.FST_addr = (cfg.FST_ip, FST_port)
        print "Using Festo controller socket at",  cfg.FST_ip, FST_port
        self.FSTs.bind(('0.0.0.0', 0))
        self.FSTs.settimeout(1)  # timout after 1 second if no response
        self.activate_piston_flag = 0  # park piston is extended when flag set to 1, parked when 0
        self.levels = [0, 0, 0, 0, 0, 0]
        self.off = [0]*6
        self.mid_level = [MAX_PRESSURE/2]*6
        self.pressure_percent = [0]*6
        self.delta = [0]*6
        self.is_enabled = False
        self.enable_oscillate = None
        self.frame_period = .04
        self.osc_dir = 1
        self.paused_time = 0
        self.xyzrpy_funcs = [self.move_x,self.move_y,self.move_z,self.move_roll,self.move_pitch,self.move_yaw]

    def init_gui(self, master):
        self.master = master
        self.nb = ttk.Notebook(master)
        page1 = ttk.Frame(self.nb)  # manual
        self.nb.add(page1, text='Manual Control')

        page2 = ttk.Frame(self.nb)  # oscillate
        self.nb.add(page2, text='  Oscillate  ')

        page3 = ttk.Frame(self.nb)  # xyzrpy
        self.nb.add(page3, text='  Orientation  ')

        self.nb.pack(expand=1, fill="both")

        self.init_manual(page1)
        self.init_auto(page2)
        self.init_orientation(page3)

        self.nb.bind("<<NotebookTabChanged>>", self.handle_tab_changed)

    def init_manual(self, master):
        frame = tk.Frame(master)
        frame.pack()

        self.label0 = tk.Label(frame, text="Adjust Muscle Pressures")
        self.label0.pack(fill=tk.X, pady=10)

        slider_frame = tk.Frame(master)
        slider_frame.pack(fill=tk.X, side=tk.TOP, pady=10)
        self.manual_sliders = []

        self.pressure_readings = []

        sLabels = ("0", "1", "2", "3", "4", "5")
        for i in range(6):
            sframe = tk.Frame(slider_frame)
            sframe.pack(fill=tk.X, side=tk.LEFT, pady=10)
            s = tk.Scale(sframe, from_=MAX_PRESSURE, to=0, resolution=50, length=200,
                         command=lambda g, i=i: self.set_manual_value(i, g), label=sLabels[i])
            s.set(3000)
            s.pack(anchor = tk.W, padx=(6, 4))
            self.manual_sliders.append(s)

            self.pressure_readings.append( tk.StringVar())
            p = tk.Label(sframe, text= str(i), fg="slate gray", textvariable=self.pressure_readings[i])
            p.pack(side=tk.BOTTOM )
            #self.pressure_readings[i].set(format("%4d" % (i*1000)))


        self.pistonState = tk.StringVar()
        self.pistonState.set('disable')

        frame2 = tk.Frame(master)
        frame2.pack(fill=tk.X, side=tk.TOP, pady=10)

        self.piston_cb = tk.Checkbutton(frame2, text="Prop Piston", command=self.piston,
                                        variable=self.pistonState, onvalue='enable', offvalue='disable')
        self.piston_cb.pack(side=tk.LEFT, padx = 100)

        self.gangState = tk.StringVar()
        self.gangState.set('disable')
        self.gang_cb = tk.Checkbutton(frame2, text="Gang Sliders", 
                                        variable=self.gangState, onvalue='enable', offvalue='disable')
        self.gang_cb.pack(side=tk.RIGHT,  padx=100)

        frame3 = tk.Frame(master)
        frame3.pack(fill=tk.X, side=tk.BOTTOM, pady=10)

        self.status_text = format("Using Festo address: %s  port %d" % (cfg.FST_ip, FST_port))
        self.status_Label = tk.Label(frame3, text=self.status_text, fg="slate gray")
        self.status_Label.pack()

        self.enableState = tk.StringVar()
        self.enableState.set('disable')
        self.enable_cb = tk.Checkbutton(frame3, text="Enable Festo Messages", command=self.enable,
                                        variable=self.enableState, onvalue='enable', offvalue='disable')
        self.enable_cb.pack(side=tk.LEFT, padx=160)

        frame4 = tk.Frame(master)
        frame4.pack(side=tk.BOTTOM, pady=10)
        if cfg.encoders_port != "":
            encoder_port = tk.Label(frame4, text="Encoder port: " + cfg.encoders_port)
            encoder_port.pack(padx=1, side= tk.TOP)
            encoder_label = tk.Label(frame4, text="Encoder Readings:")
            encoder_label.pack(padx=1, side= tk.TOP)
            self.encoder_values = []
            for i in range(6):
                self.encoder_values.append(tk.Label(frame4, text="0"))
                self.encoder_values[i].pack(padx=30, side= tk.LEFT)
            self.encoders = LinearEncoders.Encoder()
            if self.encoders.connect(cfg.encoders_port, 57600, 0): # todo add try block
                self.update_encoders()
            else:
                encoder_port.config(text="Can't connect to port " + cfg.encoders_port)
        else:
            self.encoder_values = None

    def init_auto(self, master):
        frame = tk.Frame(master)
        frame.pack()

        self.label0 = tk.Label(frame, text="Adjust Oscillation values")
        self.label0.pack(fill=tk.X, pady=10)

        slider_frame = tk.Frame(master)
        slider_frame.pack(fill=tk.X, side=tk.TOP, pady=10)

        sframe = tk.Frame(slider_frame)
        sframe.pack(fill=tk.X, side=tk.LEFT, pady=10)
        self.min_value = tk.IntVar()
        self.min_value = tk.Scale(sframe, from_=cfg.max_pressure, to=cfg.min_pressure, resolution=50, length=200, label="Min Pressure", variable=self.min_value)
        self.min_value.pack(anchor = tk.W, padx=(6, 4))

        sframe = tk.Frame(slider_frame)
        sframe.pack(fill=tk.X, side=tk.LEFT, pady=10)
        self.max_value = tk.IntVar()
        self.max_value = tk.Scale(sframe, from_=cfg.max_pressure, to=cfg.min_pressure, resolution=50, length=200, label="Max Pressure", variable=self.max_value)
        self.max_value.pack(anchor = tk.W, padx=(6, 4))
        self.max_value.set(MAX_PRESSURE)

        sframe = tk.Frame(slider_frame)
        sframe.pack(fill=tk.X, side=tk.LEFT, pady=10)
        self.period_var = tk.IntVar()
        self.period = tk.Scale(sframe, from_=20, to=1, resolution=1, length=200, label="Period (s)", variable=self.period_var)
        self.period.pack(anchor = tk.W, padx=(6, 4))
        self.period.set(cfg.period)

        sframe = tk.Frame(slider_frame)
        sframe.pack(fill=tk.X, side=tk.LEFT, pady=10)
        self.pause_var = tk.IntVar()
        self.pause = tk.Scale(sframe, from_=20, to=0, resolution=1, length=200, label="Pause (s)", variable=self.pause_var)
        self.pause.pack(anchor = tk.W, padx=(6, 4))
        self.pause.set(cfg.pause)
 
        frame2 = tk.Frame(master)
        frame2.pack(fill=tk.X, side=tk.TOP, pady=10)

        self.enable_oscillate = tk.StringVar()
        self.enable_oscillate.set('disable')

        self.oscillate_cb = tk.Checkbutton(frame2, text="Enable Oscillation", 
                                        variable=self.enable_oscillate, onvalue='enable', offvalue='disable')
        self.oscillate_cb.pack()


    def init_orientation(self, master):
        frame = tk.Frame(master)
        frame.pack()

        label0 = tk.Label(frame, text="Adjust platform orientation")
        label0.pack(fill=tk.X, pady=20)

        slider_frame = tk.Frame(master)
        slider_frame.pack(fill=tk.X, side=tk.TOP, pady=10, padx=20)
        self.orientation_sliders = []

        sLabels = ("X", "Y", "Z", "R", "P", "Y")
        for i in range(6):
            sframe = tk.Frame(slider_frame)
            sframe.pack(fill=tk.X, side=tk.LEFT, pady=10)

            s = tk.Scale(sframe, from_=1, to=-1, resolution=0.1, length=200,
                         command=lambda g, i=i: self.set_orientation_value(i, g), label=sLabels[i])
            s.set(0)
            s.pack(anchor = tk.W, padx=(6, 4))
            self.orientation_sliders.append(s)

        frame2 = tk.Frame(master)
        frame2.pack(fill=tk.X, side=tk.TOP, pady=10)

        park_btn = tk.Button(frame2, text="Park", command=self.park)
        park_btn.pack(side=tk.LEFT, padx = 100)

        center_btn = tk.Button(frame2, text="Center", command=self.center)
        center_btn.pack(side=tk.RIGHT,  padx=100)

    def on_closing():
        print("closing")
        self.master.destroy()

    def handle_tab_changed(self, event):
        selection = event.widget.select()
        tab = event.widget.tab(selection, "text")
        if tab == '  Oscillate  ':
            pass
        elif tab == "Manual Control":
            self.enable_oscillate.set('disable')
        elif tab =='  Orientation  ':
            self.enable_oscillate.set('disable')
        else:
            print("text:", tab)

    def service(self):
        if self.enable_oscillate and self.enable_oscillate.get() == "enable":
            self.do_oscillate()
        if self.encoder_values != None:
             pass
             # todo read encoder values here
        self.master.after(20, self.service)

    def update_encoders():
        readings = self.encoders.read()
        if lenght(readings) == 6:
            for i in range(6):
                self.encoder_values[i].set(readings[i])

    def do_oscillate(self):
        if self.pause_var.get() > 0 and self.paused_time > 0:
            if time.time() - self.paused_time >= self.pause_var.get():
                self.paused_time = 0
        if self.paused_time == 0:
            steps = self.period_var.get() / self.frame_period
            delta = (self.max_value.get()-self.min_value.get()) / steps
            # print(self.min_value.get(), self.max_value.get(), steps)
            for idx, val in enumerate(self.levels):
                self.levels[idx] += int(delta * self.osc_dir)
                if self.levels[idx] <= self.min_value.get() :
                    self.levels[idx] = self.min_value.get()
                    self.osc_dir = 1
                    if self.pause_var.get() > 0:
                        self.paused_time = time.time()
                        print(format("pausing for %d seconds" % self.pause_var.get()))
                if self.levels[idx] > self.max_value.get() :
                    self.levels[idx] = self.max_value.get()
                    self.osc_dir = -1
            # print(self.levels)
            self.send(copy.copy(self.levels))

    def scale(self, val, src, dst) :   # the Arduino 'map' function written in python  
        return (val - src[0]) * (dst[1] - dst[0]) / (src[1] - src[0])  + dst[0]

    def slider_to_percent(self, val):
       val = float(val)
       return self.scale(val, (-1.0, 1.0), (0, 100))

    def slider_to_inv_percent(self, val):
       val = float(val)
       return self.scale(val, (-1.0, 1.0), (100, 0))
   
    def percent_to_pressure(self, percent):
        # todo - adjust for non linear muscle S curve
        return   self.scale(percent, (0, 100), (self.min_value.get(), self.max_value.get()))

    def move_x(self, value):
        print("todo move x")

    def move_y(self, value):
        print ("todo move y")

    def move_z(self, value):
        percent = self.slider_to_percent(value)
        for i in range(6):
            self.set_manual_slider(i, self.percent_to_pressure(percent))

    def move_roll(self, value):
        up = self.percent_to_pressure(self.slider_to_percent(value))
        self.set_manual_slider(1, up)
        self.set_manual_slider(2, up)
        mid = self.percent_to_pressure(50)
        self.set_manual_slider(0, mid)
        self.set_manual_slider(5, mid)
        down = self.percent_to_pressure(self.slider_to_inv_percent(value))
        self.set_manual_slider(3, down)
        self.set_manual_slider(4, down)

    def move_pitch(self, value):
        up = self.percent_to_pressure(self.slider_to_percent(value))
        self.set_manual_slider(1, up)
        self.set_manual_slider(2, up)
        self.set_manual_slider(3, up)
        self.set_manual_slider(4, up)
        down = self.percent_to_pressure(self.slider_to_inv_percent(value))
        self.set_manual_slider(0, down)
        self.set_manual_slider(5, down)

    def move_yaw(self, value):
        for i in range(6):
            if i % 2 == 0:
                self.set_manual_slider(i,self.percent_to_pressure(self.slider_to_percent(value)))
            else:
                self.set_manual_slider(i,self.percent_to_pressure(self.slider_to_inv_percent(value)))

    def park(self):
        self.activate_piston_flag = 1
        self.slow_move(self.levels, self.off, 2000)

    def center(self):
        print "center"
        self.slow_move(self.levels, self.mid_level, 2000)
        for s in self.orientation_sliders:
           s.set(0)

    def piston(self):
        if self.pistonState.get() == 'enable':
            self.activate_piston_flag = 1
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
            print "moving from", start, "to", end, "steps", steps
            delta = [(e - s)/steps for s, e in zip(start, end)]
            for step in xrange(steps):
                current = [x + y for x, y in zip(current, delta)]
                for idx, val in enumerate(current):
                    if current[idx] < 0 :
                        current[idx] = 0
                    self.set_manual_slider(idx,current[idx])
                # print current
                # self.send(copy.copy(current))
                time.sleep(interval / 1000.0)

    def set_manual_value(self, idx, value):
        if self.gangState.get() == "enable":
            for s in self.manual_sliders:
                s.set(value) 
        self.levels[idx] = int(value)
        if self.is_enabled:
            self.send(self.levels)

    def set_manual_slider(self, idx, value):
        self.manual_sliders[idx].set(value)
        self.levels[idx] = int(value)
        if self.is_enabled:
            self.send(self.levels)


    def set_orientation_value(self, idx, value):
        self.xyzrpy_funcs[idx](value)

    def send(self, muscle_pressures):
        try:
            msg = copy.copy(muscle_pressures)
            msg.append(self.activate_piston_flag)
            packet = easyip.Factory.send_flagword(0, msg)
            try:
                self.send_packet(packet)
                #  print "festo output:", packet, FST_port
                if cfg.SHOW_FESTO_PRESSURE:
                    self.actual_pressures = self._get_pressure()
                    if len(self.actual_pressures) >= 6:
                        for i in range(6):
                            self.pressure_readings[i].set(format("%4d" % (self.actual_pressures[i])))
                            if cfg.PRINT_PRESSURE_DELTA:
                                self.delta[i] = self.actual_pressures[i] - muscle_pressures[i]
                                if muscle_pressures != 0:
                                    self.pressure_percent[i] = int(delta[i] * 100 / muscle_pressures[i])
                                else:
                                    self.pressure_percent[i] = 0
                                print muscle_pressures, self.delta, self.pressure_percent
                        print  self.pressure_readings
                else:
                    print "Festo values:",  msg

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
            self.FSTs.sendto(data, self.FST_addr)
            if cfg.WAIT_FESTO_RESPONSE:
                #  print "in sendpacket,waiting for response..."
                data, srvaddr = self.FSTs.recvfrom(fst_bufSize)
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

def _delete_window():
    global isRunning, root
    print "Exiting"
    isRunning = False
    root.destroy()



def main():
    global root, isRunning
    festo = FestoTest()

    try:
        root = tk.Tk()
        if festo.init_gui(root) == False:
            print("init gui returned false")
            exit() 
        root.protocol("WM_DELETE_WINDOW", _delete_window)

        """
        while os.system("ping " + ("-n 1 " if  sys.platform =="win32" else "-c 1 ") + cfg.FST_ip) != 0:
           msg = cfg.FST_ip + " not responding, check network connection and try again"
           if tkMessageBox.askretrycancel("Connection Error", msg) == False:
               print(msg)
               return 
        """
    except:
        e = sys.exc_info()[0]  # report error
        s = traceback.format_exc()
        print e, s
    root.title("Michael's Festo Gui") 
    root.iconbitmap('platform_icon16.ico')
    print "starting main service loop"
    while isRunning:
        root.after(20, festo.service()) 
        root.mainloop()  


if __name__ == "__main__":
    main()


