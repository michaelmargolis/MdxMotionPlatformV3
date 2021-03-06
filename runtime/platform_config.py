# platform_config.py

"""
Platform_config.py - select platform type and ip address default values
"""

"""
Uncomment one of the following to select the platform configuration
"""
#  platform_selection = 'output.ConfigV3'
platform_selection = 'output.configNextgen'

"""
The following default values should be changed only if you know what you are doing
"""
class cfg:
    Festo_IP_ADDR = '192.168.0.10'  #  Festo Port is 995

    # set the following to None if using auto discovery of NoLimits, otherwise set to static address of NoLimits PC
    HARD_CODED_IP = None  # default addr is '192.168.0.4'
    # note the default addr for optional computer running control software is 192.168.0.2

    USE_PI_SWITCHES = True # uses hardware switches on Pi if set true, ignored if controller is not running on Pi

    #software network address assignments
    SIM_IP_ADDR = ['192.168.1.16', '192.168.1.23'] # first addr provides telemetry and encoder data
    ECHO_IP_ADDR = '127.0.0.1' # transform and platform output echoed to this address using PLATFORM_ECHO_PORT
    ENCODER_IP_ADDR = SIM_IP_ADDR[0] # Encoder server running on first sim PC 
    # software network port assignments:
    STARTUP_SERVER_PORT =   10008
    SPACE_COASTER_PORT = 10009
    PC_MONITOR_PORT = 10010
    TCP_UDP_REMOTE_CONTROL_PORT = 10013
    REMOTE_CLIENT_PORT = 10015 # remote client connection to local clients on PC
    ENCODER_SERVER_PORT = 10016 # encoder data broadcasted on this port
    ENCODER_SERVER_CMD_PORT = ENCODER_SERVER_PORT+1  #10017
    REMOTE_SCALE_PORT = 10018
    REMOTE_IMU_PORT = 10019
    PLATFORM_ECHO_PORT = 10020