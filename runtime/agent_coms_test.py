# agent_coms_test.py

from  platform_config import cfg
from agents.agent_config import AgentStartupMsg
from common.tcp_client import TcpClient
from common.udp_tx_rx import UdpReceive

import time

import subprocess # for ping
import platform
 
def ping_ip(current_ip_address):
    try:
        output = subprocess.check_output("ping -{} 1 {}".format('n' if platform.system().lower(
        ) == "windows" else 'c', current_ip_address ), shell=True, universal_newlines=True)
        if 'unreachable' in output:
            return False
        else:
            return True
    except Exception:
            return False
                
import logging
log = logging.getLogger(__name__)

class AgentComsTest():
    def __init__(self, address_list, startup_cmd_port, first_event_port):
        self.addresses = address_list  # (ipaddr, port),
        self.nbr_agents = len(address_list)
        self.nbr_connected = 0
        self.conn = [None] * self.nbr_agents
        self.is_connected = [False] * self.nbr_agents
        self.event_ports = [None] * self.nbr_agents  # ports to receive telemetry for each agent
        self.event_receiver = [None] * self.nbr_agents # upd receiver objects for each agent

        for idx, addr in enumerate(self.addresses):
            log.info("Initialising socket for comms to agent at %s:%d",addr, startup_cmd_port) 
            self.conn[idx] = TcpClient(addr, startup_cmd_port)
        self.controller_ip = self.conn[0].get_local_ip()
        for i in range(len(self.event_receiver)):
            self.event_ports[i] = first_event_port + i
            self.event_receiver[i] = UdpReceive(self.event_ports[i])
            log.info("creating UDP event receiver on port %d for agent at %s", self.event_ports[i], self.addresses[i])

    def connect(self):
        for idx, addr in enumerate(self.addresses):
            if self.is_connected[idx] == False:
                log.info("Attempting to connect to agent at %s", str(addr))
                if self.conn[idx].connect():
                    log.info("Connected to Agent at %s",str(addr))
                    self.is_connected[idx] = True
                    self.nbr_connected += 1
                else:
                    if ping_ip(addr):
                        log.error("---> Found pc at %s but failed to connect to agent, is agent_startup running on that PC?", str(addr))
                    else:
                        log.error("----> PC at %s UNREACHABLE via ping", str(addr))

    def send_event_test(self, idx):
        event_test_msg = format('EVENT_TEST,%s,%d' % (self.controller_ip, self.event_ports[idx]))
        log.info("Sending agent at %s event request test msg: %s", str(self.addresses[idx]), event_test_msg)
        self.conn[idx].send(event_test_msg + '\n')

        start = time.time()         
        timeout = 2
        while( time.time() < start  + timeout): # listen for two seconds
            rx  = self.event_receiver[idx]
            if rx.available():
                log.info("GOT: %s from %s", rx.get(), self.addresses[idx])
                return
        log.error("--> No event received from %s after %d seconds", self.addresses[idx], timeout) 

    def disconnect(self):
        for idx, addr in enumerate(self.addresses):
            if self.is_connected[idx]:
                log.info("disconnecting pc at %s", str(self.addresses[idx]))
                self.conn[idx].disconnect()



if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%H:%M:%S')
    log.setLevel('DEBUG')
    log.info("starting comms test")
    addresses = cfg.SIM_IP_ADDR
    agents = AgentComsTest(addresses, cfg.STARTUP_SERVER_PORT, cfg.FIRST_AGENT_PROXY_EVENT_PORT)
    for addr in addresses:
        addr = (addr, cfg.STARTUP_SERVER_PORT) # append port to addresses
    agents.connect()
    log.info("%d of %d agents connected", agents.nbr_connected, agents.nbr_agents)
    repeats = 2
    if agents.nbr_agents > 0:
        for iter in range(repeats):
            for idx, conn in enumerate(agents.conn):
                if agents.is_connected[idx]:
                    agents.send_event_test(idx)
        input("press enter to quit")
        agents.disconnect()
    else:
        log.error("no agents connected")