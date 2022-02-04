"""
agent_base.py   (was client_api.py)
  
Base Class for Mdx platform agent 
all but the most basic agents will override these methods 


"""
from collections import namedtuple

AgentEvt = namedtuple('AgentMsg', ['agent_id', 'ridetime', 'frame', 'state', 'is_paused',
                                   'transform', 'ride_status_str', 'sim_connection_state_str'])

# sim_connection_state_str :  'waiting sim connection', 'sim connected', 'sim not connected'

class RemoteMsgProtocol(object):  # AgentEventProtocol  was RemoteMsgProtocol in previous version

    EvtMsgHeader = 'AgentEvent'

    @staticmethod
    def encode(agent_id, ridetime, frame, state, is_paused, transform, ride_status_str, sim_connection_state_str):
        xform =  ','.join('%0.4f' % item for item in transform) 
        return format("%s,%s,%d,%d,%d,%d;%s;%s;%s\n" % (RemoteMsgProtocol.EvtMsgHeader, agent_id,  ridetime, frame, state,
                                                     is_paused, xform, ride_status_str, sim_connection_state_str))

    @staticmethod
    def decode(remote_msg):
        if remote_msg[:len(RemoteMsgProtocol.EvtMsgHeader)] == RemoteMsgProtocol.EvtMsgHeader:
            fields = remote_msg.split(';')
            context = fields[0].split(',')
            agent_id = int(context[1])
            ridetime = int(context[2])
            frame = int(context[3])
            state = int(context[4])
            is_paused = int(context[5])
            transform_str =  fields[1].split(',')
            transform = [float(x) for x in transform_str]
            ride_status_str = fields[2]
            sim_connection_state_str = fields[3]
            return  AgentEvt(agent_id, ridetime, frame, state, is_paused, transform, ride_status_str, sim_connection_state_str)
        else:
            return None # this was not an agent event msg

class AgentBase(object):  # was ClientApi
 
    def __init__(self, instance_id, event_address, event_sender):
        """Constructor.  May be extended, do not override."""
        self.instance_id = instance_id
        self.event_address = event_address
        self.event_sender = event_sender
        # orientation is: x, y, z translations, roll, pitch , yaw
        self.transform = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.is_normalized = True  # set to false if agent provides real world orientation values
        self.state = 999
        self.ride_state = None
        self.is_connected = False
        self.gui = None


    def activate(self):
        """code to execute in agent when platform is activated goes here"""
        pass

    def deactivate(self):
        """code to execute in agent when platform is deactivated goes here"""
        pass

    def get_transform(self):
        """return list of xyzrpy float levels"""
        return self.transform

    def set_transform(self, transform):
        """set xyzrpy float levels"""
        self.transform = transform

    def get_ride_state(self):
        """return ride state"""
        return self.ride_state

    def set_ride_state(self, state):
        self.ride_state= state

    def service(self):
        """code to execute each frame prior to sending data to the platform"""  
        pass

    def reset_vr(self):
        """override this with code to reset vr headset"""
        pass

    def begin(self, cmd_func, move_func, limits, remote_addresses=None):
        """code to start the agent goes here"""
        pass

    def connect(self):
        #  address must be set prior to connect
        return is_connected

    def is_connected(self):
        return is_connected

    def detected_remote(self):
        pass

    def fin(self):
        """agent exit code goes here"""
        pass

            
if __name__ == "__main__":
    state = 1
    frame = 2
    is_paused = 1
    transform = '0,0,0,0,0,0'
    ride_status_str  = "ride status string"
    sim_connection_state_str  = "Waiting connection"
    msg =  RemoteMsgProtocol.encode(state, frame, is_paused, transform, ride_status_str, sim_connection_state_str)
    m = RemoteMsgProtocol()
    m.decode(msg)
    print(format("%d,%d,%d;%s;%s;%s" % (m.state, m.frame, m.is_paused,
                             m.transform, m.ride_status_str, m.sim_connection_state_str)))
