"""
RideState represents the high level state of the motion sim 

"""

class RideState:
    DISABLED, READY_FOR_DISPATCH, RUNNING, PAUSED, EMERGENCY_STOPPED, RESETTING = list(range(6))

    @staticmethod
    def str(state):
        return ("Disabled", "Ready for dispatch", "Running", "Paused", "Emergency Stopped", "Resetting")[state]
