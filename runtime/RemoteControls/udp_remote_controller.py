"""
  udp_remote_controller.py
  
todo replace hard coded port 10013 with TCP_UDP_REMOTE_CONTROL_PORT as defined in platform config

"""

import sys, os
import socket

import threading
import time
try:
    from queue import Queue
except ImportError:
    from queue import Queue
    
import tkinter as tk
import traceback

from pc_monitor import pc_monitor_client
heartbeat = pc_monitor_client((40,60),(75,90))

if os.name == 'posix':
   import local_control_itf

colors = ["green3","orange","red"] # for warning level text

class UdpRemoteController(object):

    def __init__(self):
        self.server_address = None # address from heartbeat
        self.prev_heartbeat = 0
        self.eventQ = Queue()  # remote messages from client
        self.client_sock = None


    def init_gui(self, master):
        self.master = master
        frame = tk.Frame(master)
        frame.grid()
        spacer_frame = tk.Frame(master, pady=4)
        spacer_frame.grid(row=0, column=0)
        self.label0 = tk.Label(spacer_frame, text="").grid(row=0)

        self.dispatch_button = tk.Button(master, height=2, width=16, text="Dispatch",
                                         command=self.dispatch, underline=0)
        self.dispatch_button.grid(row=1, column=0, padx=(24, 4))

        self.pause_button = tk.Button(master, height=2, width=16, text="Prop", command=self.pause, underline=0)
        self.pause_button.grid(row=1, column=2, padx=(30))

        self.reset_button = tk.Button(master, height=2, width=16, text="Reset Rift",
                                      command=self.reset_vr, underline=0)
        self.reset_button.grid(row=1, column=3, padx=(24))

        label_frame = tk.Frame(master, pady=20)
        label_frame.grid(row=3, column=0, columnspan=4)

        self.coaster_status_label = tk.Label(label_frame, text="Waiting for Connection", font=(None, 24),)
        self.coaster_status_label.grid(row=1, columnspan=2, ipadx=16, sticky=tk.W)

        self.intensity_status_Label = tk.Label(label_frame, font=(None, 12),
                 text="Intensity", fg="orange")
        self.intensity_status_Label.grid(row=2, column=0, columnspan=2, ipadx=16, sticky=tk.W)
        
        self.coaster_connection_label = tk.Label(label_frame, fg="orange", font=(None, 12),
               text="Waiting for data from Coaster (start Coaster on PC if not started)")
        self.coaster_connection_label.grid(row=3, columnspan=2, ipadx=16, sticky=tk.W)

        self.remote_status_label = tk.Label(label_frame, font=(None, 12),
                 text="Looking for Remote Control", fg="orange")
        self.remote_status_label.grid(row=4, columnspan=2, ipadx=16, sticky=tk.W)

        self.chair_status_Label = tk.Label(label_frame, font=(None, 12),
                 text="Using Festo Controllers", fg="orange")
        self.chair_status_Label.grid(row=5, column=0, columnspan=2, ipadx=16, sticky=tk.W)
        
        self.temperature_status_Label = tk.Label(label_frame, font=(None, 12),
                 text="Attempting Connection to VR PC Server", fg="red")
        self.temperature_status_Label.grid(row=6, column=0, columnspan=2, ipadx=16, sticky=tk.W)

        bottom_frame = tk.Frame(master, pady=16)
        bottom_frame.grid(row=5, columnspan=3)

        self.is_chair_activated = tk.IntVar()
        self.is_chair_activated.set(0)  # disable by default

        self.activation_button = tk.Button(master, underline=0, command=self.activate)
        self.activation_button.grid(row=4, column=1)
        self.deactivation_button = tk.Button(master, command=self.deactivate)
        self.deactivation_button.grid(row=4, column=2)
        self.set_activation_buttons(False)

        self.close_button = tk.Button(master, text="Shut Down and Exit", command=self.quit)
        self.close_button.grid(row=4, column=3)

        self.label1 = tk.Label( bottom_frame, text="     ").grid(row=0, column=1)

        self.org_button_color = self.dispatch_button.cget("background")
        
        heartbeat.begin()
        while not self.check_heartbeat():
            self._sleep_func(0.5)

    def dispatch(self):
        print("dispatch")
        self.send("dispatch")

    def pause(self):
        print("pause")
        self.send("pause")
        
    def reset_vr(self):
        print("reset vr")
        self.send("reset")
        
    def activate(self):
        print("activate")
        self.send("activate")
         
    def deactivate(self):
       print("deactivate")
       self.send("deactivate")

    def quit(self):
        print("quit")
        self.send("quit")
        
    def send(self, msg):
        if self.client_sock and self.server_address:
            self.client_sock.sendto(msg, (self.server_address, 10013))

    def service(self):
        try:
            while self.eventQ.qsize() > 0:
                event = self.eventQ.get()
                if "state" in event:
                    event = event.split(",") 
                    print(event[1])
                    self.coaster_status_label.config(text=event[1], fg="black")
                elif "time" in event:
                    event = event.split(",")
                    percent = float(event[1]) / float(event[2])
                    print(int(percent * 100), event[1], event[2])

        except Exception as e:  
            s = traceback.format_exc()
            print("service error", e, s)

    def start_listening(self, server_address):
        try:
            print("opening socket on", "", 10013)
            self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client_sock.bind(("", 10013)) # todo make port const
            t = threading.Thread(target=self.listener_thread, args = (self.client_sock, self.eventQ,))
            t.daemon = True
            t.start()
        except Exception as e:
            s = traceback.format_exc()
            print("thread init err", e, s)


    def update_heartbeat(self):
        try:
            self.check_heartbeat()
        except Exception as e:
            s = traceback.format_exc()
            print("update heartbeat err", e, s)
       
    def check_heartbeat(self):
        addr, heartbeat_status, warning = heartbeat.read()
        # print "in check heartbeat, addr = ", addr
        if len(addr[0]) > 6: #  server sends on port 10010
            self.prev_heartbeat = time.time()
            if not self.server_address or self.server_address != addr[0]:
                self.server_address = addr[0]
                print("first time connection to server @", self.server_address)
                self.start_listening(self.server_address)
            # print format("heartbeat {%s:%s} {%s} {%s}" % (addr[0], addr[1], heartbeat_status, warning))
            self.temperature_status_Label.config( text=heartbeat_status,fg=colors[warning])
            self.coaster_connection_label.config(text="Connected to PC", fg="green3")
        duration = time.time() - self.prev_heartbeat
        #if duration > 1.2:
        #    print "heartbeat dur:", duration
        if duration > 3.2: # if no heartbeat after three seconds
            self.temperature_status_Label.config(text="Lost heartbeat with server", fg="red")
            print("Lost heartbeat with server")
            return False
        elif duration > 2.2: # if no heartbeat after two seconds
            self.temperature_status_Label.config(text="Missed Heartbeat from Server", fg="orange")
            self.coaster_connection_label.config(text="Attempting to connect to PC", fg="red")
            # self.gui.set_coaster_status_label(("Lost connection with PC", "red"))
        return True

    def _sleep_func(self, duration):
        start = time.time()
        while time.time() - start < duration:
            self.master.update_idletasks()
            self.master.update()
        
    def listener_thread(self, sock, eventQ):
        MAX_MSG_LEN = 100
        while True:
            try:
                msg = sock.recv(MAX_MSG_LEN)
                if msg is not None:
                    # print msg 
                    eventQ.put(msg)
            except Exception as e:
                s = traceback.format_exc()
                print("listener err", e, s)
                break

root = None
remote = None

def main():
    global root, remote
    root = tk.Tk()
    root.title("Basic UDP remote controller")
    remote = UdpRemoteController()
    remote.init_gui(root)
    root.after(500, poll) 
    root.mainloop()  

def poll():
    global root, remote
    remote.update_heartbeat()
    remote.service()
    root.after(500, poll)
    
if __name__ == '__main__':
    main() 