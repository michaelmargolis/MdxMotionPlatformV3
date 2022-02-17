"""
RideState represents the high level state of the motion sim 
each sim must map its internal ride state to these states
added PARKED event 13 Feb 2022 mem

"""

class RideState:
    ''' Ride states: 
        DISABLED - platform is disabled and parked
        READY_FOR_DISPATCH - platform may be parked if platform state is inactive
        RUNNING - sim not paused
        PAUSED 
        EMERGENCY_STOPPED -  estop switch pressed
        NON_SIM_MODE - connected but not responsive to telemetry (was named RESETTING)
    '''
    DISABLED, READY_FOR_DISPATCH, RUNNING, PAUSED, EMERGENCY_STOPPED, NON_SIM_MODE = list(range(6))

    @staticmethod
    def str(state):
        return ("Disabled", "Ready for dispatch", "Running", "Paused", "Emergency Stopped", "Not_in_sim_mode")[state]

class RideEvent:
    ''' Ride events: 
        DISABLED - platform deactivated 
        PARKED - platform deactivated and parked
        ACTIVATED - platform activated
        PAUSED - sim commaned to pause
        UNPAUSED - sim commaned to unpause
        DISPATCHED - sim commaned to dispatch
        ESTOPPED - estop switch pressed
        AT_STATION - sim arrrived at station at end of run (was STOPPED)
        NON_SIM_MODE sim resetting or in another non-telemetry mode    (was RESETEVENT)
    '''
    DISABLED, PARKED, ACTIVATED, PAUSED, UNPAUSED, DISPATCHED, ESTOPPED, AT_STATION, NON_SIM_MODE = list(range(9))

    @staticmethod
    def str(event):
        return ("DISABLED", "PARKED",  "ACTIVATED", "PAUSED", "UNPAUSED", "DISPATCHED", "ESTOPPED", "AT_STATION", "NON_SIM_MODE")[event]

class ConnectionState:
    # NET_NOT_CONNECTED: no connection between agent proxy and agent_startup 
    # SIM_NOT_CONNECTED,: agent not connected to sim 
    # SIM_BUSY: Sim connected but not in game mode 
    
    NET_NOT_CONNECTED, SIM_NOT_CONNECTED, SIM_BUSY, SIM_CONNECTED = list(range(4))

    @staticmethod
    def err_str(state):
        return ("Net not connected", "Sim not connected", "Connected but not in game mode", "Connected")[state]