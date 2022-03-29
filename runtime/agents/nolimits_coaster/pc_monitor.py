"""
pc_monitor

returns address if HARD_CODED_IP is defined

else receives UDP hearbeat messages from the server
containing CPU and GPU temperatires in degrees CPU
"""

# note to self, modified to remove port from read message (also changed in coaster client)

import sys
import socket
import threading
import time
try:
    from queue import Queue
except ImportError:
    from Queue import Queue
import os
import traceback

import logging
log = logging.getLogger(__name__)

from  system_config import cfg

deg = u"\N{DEGREE SIGN}"

if cfg.HARD_CODED_IP:
    class pc_monitor_client():
        def __init__(self, cpu_thresholds, gpu_thresholds): # thresholds are ignored
            self.HOST = cfg.HARD_CODED_IP
            log.info("NoLimits running on pc @ %s", self.HOST)
            
        def begin(self):
            pass

        def fin(self):
            pass
            
        def read(self):
            return  self.HOST, "NoLimits PC: " + self.HOST, 0
else:
    class pc_monitor_client():
        def __init__(self, cpu_thresholds, gpu_thresholds): 
            self.cpu_threshold = cpu_thresholds
            self.gpu_threshold = gpu_thresholds
            self.PORT = cfg.PC_MONITOR_PORT
            self.inQ = Queue()
            self.is_running = False
            
        def begin(self):
            self.is_running = True
            self.thread = threading.Thread(target=self.listener_thread)
            if self.thread:
               self.thread.daemon = True
               self.thread.start()
               log.info("Started pc monitor  heartbeat thread")
               return True
            else:
                log.error("Failed to start pc monitor  heartbeat thread")
                return False

        def read(self):
            # returns tuple of: IP address of server, temperature strings, warning level(0-2) 
            # IP address will be "" if no heartbeat available
            payload = None
            status = "?"
            addr = ("", 0)
            warning_level = 0
            # throw away all but most recent message
            #   print "in read()"
            while not self.inQ.empty():
                payload = self.inQ.get()
            try:
                # todo remove messages that do not contain valid payload, for now just ignore
                if payload != None:
                    # print "payload", payload
                    data = payload[0].rstrip()
                    addr = payload[1].strip("'()")
                    addr = addr.split(',')
                    addr[0] = addr[0].strip("'")
                    # print(format("data {%s}, addr [%s] [%s]" % (data, addr[0], addr[1])))
                    try:
                        if 'GPU' in data:
                            vals = data.split(',',1)
                            d = dict(v.split('=') for v in vals)
                            if 'CPU' in d and d['CPU'].isdigit():
                                cpu = int(d['CPU'])
                                cpu_string = format("CPU temperature %d%sC, " % (cpu, deg))
                                status = cpu_string                  
                                if cpu > self.cpu_threshold[1]:
                                     warning_level = 2
                                elif cpu > self.cpu_threshold[0]:
                                     warning_level = max(warning_level,1)
                            else:
                                cpu_string = "CPU Temperature ??   "
                                warning_level = 1
                            if 'GPU' in d and  d['GPU'].isdigit():
                                gpu = int(d['GPU'])
                                gpu_string = format(" GPU: %d%sC" % (gpu, deg))
                                if gpu > self.gpu_threshold[1]:
                                    warning_level = 2
                                elif gpu > self.gpu_threshold[0]:
                                    warning_level = max(warning_level,1)
                            else:
                                gpu_string = "GPU ??"
                            status += gpu_string
                            pi = self.pi_temperature()
                            if pi > 0:
                                status +=  format(", Pi: %d%sC" % (pi, deg))
                                if pi > 70:
                                    warning_level = 2
                                elif pi > 50:
                                    warning_level = max(warning_level,1)
                            #  print status
                        else:
                            print("ignored monitor payload:", data)
                            pass
                            # MEng test data would come in here
                    except ValueError:
                       e = sys.exc_info()[0]
                       print(e)
                       print(format("pc monitor data {%s}, addr [%s] [%s]" % (data, addr[0], addr[1])))
                    #  print format("In pc monitor, heartbeat {%s:%s} {%s} {%d}" % (addr[0], addr[1], data, warning_level))
                #  print("pc monitor read:",addr, status, warning_level)
                return addr[0], status, warning_level
            except Exception as e:
                #  print error if input not a string or cannot be converted into valid request
                s = traceback.format_exc()
                print(e, s)
                return ("", 0), "Error", 2

        def fin(self):
            self.is_running = False # set flag to close heartbeat thread

        def pi_temperature(self):
            if os.name == 'posix':
                # for now assumes running on raspberry pi
                res = os.popen('vcgencmd measure_temp').readline()
                t = res.replace("temp=","").replace("'C\n","")
                return float(t)
                # return format(", Pi: %s%sC" % (t, deg))
            else:
                 #return ""
                 return 0

        def get_ip(self):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # doesn't even have to be reachable
                s.connect(('10.255.255.255', 1))
                IP = s.getsockname()[0]
            except:
                IP = '127.0.0.1'
            finally:
                s.close()
            return IP
    
        def listener_thread(self):
            try:
                MAX_MSG_LEN = 255
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                if os.name == 'nt':
                   host = self.get_ip()
                   # host = '127.0.0.1'
                else:
                    host = ''
                log.info("pc monitor socket binding to %s:%d", host, self.PORT)
                sock.bind((host, self.PORT))
                time.sleep(1)
                while self.is_running:
                    try:
                        msg, addr = sock.recvfrom(MAX_MSG_LEN)
                        self.inQ.put((str(msg),str(addr)))
                    except Exception as e:
                        s = traceback.format_exc()
                        print("listener err", e, s)
                        time.sleep(.5)
            except Exception as e:
                s = traceback.format_exc()
                log.info("pc monitor thread init error %s", e)
                print("thread init err", e, s)
                print("IS ANOTHER INSTANCE ALREADY RUNNING?")
            sock.close()
            log.debug("heartbeat thread terminated")

if __name__ == "__main__":
    heartbeat = pc_monitor_client((40,60),(75,90))
    heartbeat.begin()
    while input("press enter to show status, q to quit") != 'q':
        addr, heartbeat_status, warning = heartbeat.read()
        print(addr, heartbeat_status, warning)
        time.sleep(1)
    heartbeat.fin()
    time.sleep(1)
    