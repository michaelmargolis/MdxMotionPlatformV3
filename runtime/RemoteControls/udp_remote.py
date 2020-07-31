""" UDP remote control """

import sys, traceback
import time
import threading
import socket
try:
    from queue import Queue
except ImportError:
    from Queue import Queue


class UdpRemote(object):
    """ provide action strings associated with UDP messages."""
    auto_conn_str = "MdxRemote_V1"  # remote responds with this when promted for version

    def __init__(self, actions):
        """ Call with dictionary of action strings.

        Keys are the strings sent by the remote,
        values are the functons to be called for the given key.
        """
        self.HOST = ""
        self.PORT = 10013 # this must match TCP_UDP_REMOTE_CONTROL_PORT defined in platform config
        self.sock = None
        self.address = None
        self.inQ = Queue()
        self.actions = actions
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.HOST, self.PORT))
            # print("opening UDP remote control socket on", self.PORT)
            t = threading.Thread(target=self.listener_thread, args=(self.inQ, self.sock))
            t.daemon = True
            t.start()
        except Exception as e:
            s = traceback.format_exc()
            print(("thread init err", e, s))


    def listener_thread(self, inQ, sock):
        MAX_MSG_LEN = 80
        while True:
            try:
                msg, self.address = sock.recvfrom(MAX_MSG_LEN)
                #  print "udp remote msg:", msg
                inQ.put(msg)
            except Exception as e:
                s = traceback.format_exc()
                print(("listener err", e, s))

    def send(self, toSend):
        if self.address:
            try:
                self.sock.sendto(toSend, self.address)
            except:
                print(("unable to send to", self.address))

    def service(self):
        """ Poll to service remote control requests."""
        while not self.inQ.empty():
            msg = self.inQ.get().rstrip()
            if "intensity" in msg:
                try:
                    m,intensity = msg.split('=', 2)
                    #print m, "=", intensity
                    self.actions[m](intensity)
                except ValueError:
                    print((msg, "is invalid intensity msg"))
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
    def reset_vr():
        print("reset vr")
    def deactivate():
        print("deactivate")
    def emergency_stop():
        print("estop")
    def set_intensity(intensity):
        print(("intensity ", intensity))
            
    actions = {'detected remote': detected_remote, 'activate': activate,
               'deactivate': deactivate, 'pause': pause, 'dispatch': dispatch,
               'reset': reset, 'emergency_stop': emergency_stop, 'intensity' : set_intensity}
 
    RemoteControl = UdpRemote(actions)
    while True:
        RemoteControl.service()
        time.sleep(.1)
        # RemoteControl.send(str(time.time()))
