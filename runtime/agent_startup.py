#!/usr/bin/env python
# coding=utf-8

"""
  agent_startup.py  # was named local_startup
  This script is run at startup on the VR PCs to select and activate the agent runtime environment and ride
"""

from common.tcp_server import TcpServer
from common.udp_tx_rx import UdpSend
from common.kb_sleep import kb_sleep
from platform_config import cfg
from agents.agent_config import AgentStartupMsg
import time
import os
import sys
import threading
import importlib
import traceback
import argparse
import socket # only used for event test
from subprocess import Popen

import logging
log = logging.getLogger(__name__)

desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')

FRAME_RATE_ms = 50

# each option comprises display followed by a colon and path to sim exe or shortcut (.lnk file)
# Vr is desktop subfolder with icon link 
sim_exe = {
            "space_coaster": os.path.join(desktop, 'Vr', 'SpaceCoaster.lnk'), 
            "nolimits_coaster": os.path.join(desktop, 'Vr', 'NoLimits 2.lnk').encode(), 
            "Test_agent": 'None'  # test agent does not have a path
          }

class AgentStartup(object):

    def __init__(self):
        self.server_address  = ('', cfg.STARTUP_SERVER_PORT)
        self.server = TcpServer(self.server_address)
        self.server.start()
        self.running = True
        self.agent = None
        self.event_sender = UdpSend()

    def startup(self, fields):
        # startup sim and agent specified in given fields
        log.info("processing startup msg for %s",  fields[1])
        msg = tuple(fields[1:6])
        msg = AgentStartupMsg._make(msg) # cast to startup namedtuple
        #  print(msg)
        if msg.sim_name != 'NONE':
            try:
                sim_path = sim_exe[msg.sim_name]
                if sim_path != 'None':
                    log.info("starting sim : %s", sim_path)
                    os.startfile(sim_path)
                agent = fields[2]
                if msg.agent_module != "NONE":
                    import_path = 'agents.' + msg.sim_name + '.' + msg.sim_name
                    event_address = (msg.ip_addr, int(msg.event_port)) # addr udp socket will send events to
                    agent = importlib.import_module(import_path).InputInterface(msg.agent_id, event_address, self.event_sender)
                    return agent
            except Exception as e:
                log.error("agent startup error %s", str(e))
                print(traceback.format_exc())
            return None

    def cmd_handler(self):
        # process commands from agent_proxy
        if self.server.available() > 0:
            name, data = self.server.get()
            if 'quit' in data:
                self.running = False
            else:
                log.info("got cmd: %s", data.strip())
                fields = data.strip().split(',')
                try:
                    if fields[0] == 'STARTUP':
                        self.agent = self.startup(fields)
                        if self.agent != None:
                             self.agent.begin()
                    elif fields[0] == 'EVENT_TEST':
                        print("event msg:", fields)
                        ip_addr = fields[1]
                        event_port = int(fields[2])
                        hostname = socket.gethostname()   
                        IPAddr = socket.gethostbyname(hostname)  
                        event_msg = format("test event from %s @ %s" % (hostname, IPAddr))
                        log.info("sending event msg: %s to %s", event_msg, str((ip_addr,event_port)))
                        self.event_sender.send(event_msg.encode('utf-8'),(ip_addr,event_port))
                    else:
                        if self.agent:
                            self.agent.handle_command(fields)
                except Exception as e:
                    print("msg format error", e)
                    print(traceback.format_exc())

    def run(self):
        log.info("Startup service at %s using TCP port %d", self.server.get_local_ip(), self.server_address[1])
        while self.running:
            while self.server.available() > 0:
                self.cmd_handler()
            if self.agent:
                self.agent.service()
            if kb_sleep(FRAME_RATE_ms * 0.001) == False:
                break

        print("exiting")
        self.server.finish()

def man():
    parser = argparse.ArgumentParser(description='Platform Controller\nAMDX motion platform control application')
    parser.add_argument("-l", "--log",
                        dest="logLevel",
                        choices=['DEBUG', 'INFO', 'WARNING'],
                        help="Set the logging level")
    return parser


if __name__ == '__main__':
    args = man().parse_args()
    if args.logLevel == 'DEBUG':
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(module)s: %(message)s',
                            datefmt='%H:%M:%S')
    elif args.logLevel == 'WARNING':
        logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)-8s  %(module)s: %(message)s',
                            datefmt='%H:%M:%S')                            
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s  %(module)s: %(message)s',
                            datefmt='%H:%M:%S')

    log.info("Python: %s", sys.version[0:5])
    log.debug("logging using debug mode")

    agent_startup = AgentStartup()
    agent_startup.run()