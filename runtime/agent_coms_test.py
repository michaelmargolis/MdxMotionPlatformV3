# agent_coms_test.py

from  platform_config import cfg
from agents.agent_config import AgentStartupMsg
from common.tcp_client import TcpClient
from common.udp_tx_rx import UdpReceive

import time
import logging
log = logging.getLogger(__name__)

class AgentComsTest():
    def __init__(self, address_list, startup_cmd_port, first_event_port):
        self.addresses = address_list  # (ipaddr, port),
        self.nbr_agents = len(address_list)
        self.conn = [None] * self.nbr_agents
        self.is_connected = [False] * self.nbr_agents
        self.event_ports = [None] * self.nbr_agents  # ports to receive telemetry for each agent
        self.event_receiver = [None] * self.nbr_agents # upd receiver objects for each agent

        for idx, addr in enumerate(self.addresses):
            print(format("creating agent for %s, %d" % (addr, startup_cmd_port))) 
            self.conn[idx] = TcpClient(addr, startup_cmd_port)
        for i in range(len(self.event_receiver)):
            self.event_ports[i] = first_event_port + i
            self.event_receiver[i] = UdpReceive(self.event_ports[i])
            print(format("creating UDP event receiver on port %d for PC at %s" % (self.event_ports[i], self.addresses[i])))

    def connect(self):
        for idx, addr in enumerate(self.addresses):
            if self.is_connected[idx] == False:
                print(format("connecting to agent at %s"% (str(addr))))
                if self.conn[idx].connect():
                    print(format("Connected to PC at %s" % (str(addr))))
                    self.is_connected[idx] = True
                else:
                    print(format("failed to connect to %s: is agent running on that PC?" % (str(addr))))
        if None in self.is_connected:
            return False
        return True

    def send_event_test(self):
        self.host_ip = self.conn[0].get_local_ip()
        for idx, conn in  enumerate(self.conn):
            event_test_msg = format('EVENT_TEST,%s,%d' % (self.host_ip, self.event_ports[idx]))
            print(format("Sending pc at %s event test  msg: %s" % (str(self.addresses[idx]), event_test_msg)))
            conn.send(event_test_msg + '\n')
            time.sleep(.01)
            conn.send(event_test_msg + '\n')

        start = time.time()         
        while( time.time() < start  + 2): # listen for two seconds
            for idx, rx in  enumerate(self.event_receiver):
                if rx.available():
                    print(rx.get(), "from", self.addresses[idx])

    def disconnect(self):
        for idx, addr in enumerate(self.addresses):
            if self.is_connected[idx]:
                print("disconnecting pc at", str(self.addresses[idx]))
                self.conn[idx].disconnect()



if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%H:%M:%S')
    log.setLevel('DEBUG')
    print('\n')
    log.info("starting comms test")
    addresses = cfg.SIM_IP_ADDR
    agents = AgentComsTest(addresses, cfg.STARTUP_SERVER_PORT, cfg.FIRST_AGENT_PROXY_EVENT_PORT)
    for addr in addresses:
        addr = (addr, cfg.STARTUP_SERVER_PORT) # append port to addresses
    if agents.connect():
        agents.send_event_test()
        input("press enter to quit")
        agents.disconnect()