# platform_config.py

"""
Uncomment one of the above to select the client
"""
#  client_selection = 'coaster.coaster_client'  # for NoLimits2
#  client_selection = 'SpaceCoaster.space_coaster'
client_selection = 'SpaceCoaster.remote_client'
#  client_selection = 'flight_sim.flight_sim_client'
#  client_selection = 'client.simple_input'    # simple gui test 

"""
Uncomment one of the following to select the platform configuration
"""
#  platform_selection = 'output.ConfigV3'
platform_selection = 'output.configNextgen'

"""
The following default values should be changed only if you know what you are doing
"""
class cfg(object):
    Festo_IP_ADDR = '192.168.0.10'  #  Festo Port is 995

    # set the following to None if using auto discovery of NoLimits, otherwise set to static address of NoLimits PC
    HARD_CODED_IP = None  # default addr is '192.168.0.4'
    # note the default addr for optional computer running control software is 192.168.0.2

    USE_PI_SWITCHES = True # uses hardware switches on Pi if set true, ignored if controller is not running on Pi

    #software network address assignments
    SIM_IP_ADDR = ['192.168.1.16',] #  '192.168.1.16'] # first addr provides telemetry and encoder data
    ECHO_IP_ADDR = '127.0.0.1' # transform and platform output echoed to this address using PLATFORM_ECHO_PORT
    # software network port assignments:
    SPACE_COASTER_PORT = 10009
    PC_MONITOR_PORT = 10010
    TCP_UDP_REMOTE_CONTROL_PORT = 10013
    REMOTE_CLIENT_PORT = 10015 # space coaster remote client connection
    REMOTE_ENCODERS_PORT = 10016

    REMOTE_SCALE_PORT = 10018
    REMOTE_IMU_PORT = 10019
    PLATFORM_ECHO_PORT = 10020