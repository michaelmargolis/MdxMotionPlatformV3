# agent_proxy.py (todo? rename to agent_hub)

from agents.ride_state import RideState
from agents.agent_config import AgentStartupMsg
from agents.agent_base import RemoteMsgProtocol
from common.tcp_client import TcpClient
from common.udp_tx_rx import UdpReceive
import importlib
import logging
log = logging.getLogger(__name__)

TIME_DELTA_THRESHOLD = .2 # max time deviation across agents before errors are logged

class AgentProxy():
    def __init__(self, address_list, startup_cmd_port, event_port): 
        self.addresses = address_list  # (ipaddr, port),
        self.nbr_agents = len(address_list)
        self.conn = [None] * self.nbr_agents
        self.is_connected = [False] * self.nbr_agents
        self.event_port = event_port
        self.event_receiver = UdpReceive(self.event_port)
        self.states = [RideState.DISABLED] * self.nbr_agents  # the agent ride state
        self.ridetime = [0] * self.nbr_agents # the time since ride was dispatched
        
        self.is_normalized = True  # set to false if agent provides real world orientation values
        # orientation is: x, y, z translations, roll, pitch , yaw
        self._transform = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.is_platform_activated = False
        self.gui = None
        
        for idx, addr in enumerate(self.addresses):
            log.debug("creating agent for %s, %d", addr, startup_cmd_port) 
            self.conn[idx] = TcpClient(addr, startup_cmd_port)
        
    def fin(self):
        pass

    def connect(self):
        for idx, addr in enumerate(self.addresses):
            if self.is_connected[idx] == False:
                log.info("connecting to agent at %s", str(addr))
                if self.conn[idx].connect():
                    log.info("Connected to PC at %s", str(addr))
                    self.is_connected[idx] = True
                else:
                    log.info("failed to connect to %s: is agent running on that PC?", str(addr))
        if None in self.is_connected:
            return False
        return True
    
    def init_gui(self, agent_gui, frame):
        gui_module = importlib.import_module(agent_gui)
        self.gui = gui_module.AgentGui(frame, self)
        self.gui.select_ride_callback(self.select_ride)

    def send_startup(self, agent_name, agent_module):
        self.host_ip = self.conn[0].get_local_ip()
        for idx, conn in  enumerate(self.conn):
            body = AgentStartupMsg(agent_name, agent_module, self.host_ip, str(self.event_port), str(idx)) 
            startup_msg = "STARTUP," + ','.join(str(s) for s in body)
            log.info("Sending startup msg: %s", startup_msg)
            conn.send(startup_msg + '\n') 

    def command(self, msg):
        log.info("Sending msg: %s", msg)
        for conn in  self.conn:
            conn.send(msg + '\n') 

    def activate(self):
        self.is_platform_activated = True
        self.gui.show_activated(self.states[0])
        self.command("activate")

    def deactivate(self):
        self.is_platform_activated = False
        self.gui.show_deactivated(self.states[0])
        self.command("deactivate")
        
    def get_transform(self):
        # returns transform
        return self._transform 
        
    def get_ride_state(self):
        # returns ride state
        pass
        
    def get_timestamps(self):
        # returns tuple of timestamps of most recent agent messages
        pass

    def dispatch_pressed(self):
        if self.is_platform_activated:
            self.command("dispatch")
        else:
            log.info("dispatch ignored because platform not activated")

    def pause_pressed(self):
        self.command("pause")

    def reset_vr(self):
        log.info("reset all rifts")
        self.command('reset\n')

    def reset1(self):
        # fixme these resets are pc specific so need routing logic
        log.info("reset rift 1")
        self.command('reset1\n')

    def reset2(self):
        log.info("reset rift 2")
        self.command('reset2\n')

    def emergency_stop(self):
        log.info("emergency stop todo ")

    def set_intensity(self, intensity_msg):
        log.info("set intensity todo")

    def select_ride(self, is_paused, park, seat):
        self.command(format('ride_select,%s,%d\n' % (park, int(seat))))

    def remote_info(self):
        log.warning("remote request for info not supported")

    def show_agent_sync_status(self):
        if len(self.states) == 1:
            return # nothing to show if only one agent 
        elif None in self.states:
            self.gui.report_sync_status("All agent events not received", 'orange')
        elif self.states.count(self.states[0])==len(self.states):
            # here if all states are same
            if not None in self.ridetime:
                min_t =  min(self.ridetime)
                max_t  = max(self.ridetime)
                delta  = max_t - min_t
                if delta > TIME_DELTA_THRESHOLD:
                    self.gui.report_sync_status("Agent sync error".format(" %d ms", delta), 'red')
                else:
                    self.gui.report_sync_status("Agent sync delta".format(" %d ms", delta), 'green')
            else: 
                self.gui.report_sync_status(" ", 'green')
        else:
            self.gui.report_sync_status("agent states are not in sync", 'red')

    def service(self):
        for idx, agent_conn in enumerate(self.conn):
            pc_str = format("PC at %s " % (agent_conn.ip_addr)) # label for conn status reporting
            if agent_conn.status.is_connected:
                status_str = pc_str + " is connected"
            else:
                # here if not connected to agent
                if self.is_connected[idx] == True: # check if previously connected
                    log.error("Agent at %s is no longer connected", agent_conn.ip_addr)
                self.is_connected[idx] = False
                status_str = 'not connected'
                # self.show_connection_status(idx, pc_str, False, status_str)
                self.gui.report_connection_status(idx, pc_str, 'not connected!red')

        while self.event_receiver.available():
            addr, msg = self.event_receiver.get()  
            msg = RemoteMsgProtocol.decode(msg)
            if msg:
                # print(msg.sim_connection_state_str, msg.ride_status_str)
                idx = msg.agent_id
                self.states[idx] = msg.state
                self.ridetime[idx] = msg.ridetime
                # self.show_connection_status(idx, pc_str, True, msg.sim_connection_state_str)
                self.gui.report_connection_status(idx, pc_str, msg.sim_connection_state_str)
                if idx == 0: # respond to the first agents events
                    self.gui.report_coaster_status(msg.ride_status_str)
                    self._transform  = msg.transform
                # todo add cpu!gpu temperatures to msg and check limits (40, 60), (75, 90))
            else:
                #self.show_connection_status(idx, pc_str, True, "waiting for event")
                self.gui.report_connection_status(idx, pc_str, 'waiting for event!orange')



