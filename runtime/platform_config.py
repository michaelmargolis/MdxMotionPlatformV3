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

    PI_PIN_DEFINES = 'dual_reset_pcb_pins' #  'single_reset_pcb_pins'   'wired_switch_pins'     

    #software network address assignments
    SIM_IP_ADDR =  ('192.168.1.109','192.168.1.166') #('192.168.0.183',) #('192.168.0.38',) #('192.168.1.24', '192.168.1.9') # first addr provides telemetry and encoder data
    ECHO_IP_ADDR = '127.0.0.1' # transform and platform output echoed to this address using PLATFORM_ECHO_PORT
    # software network port assignments:
    FIRST_AGENT_PROXY_EVENT_PORT = 10000
    # RESERVER THE NEXT 7 PORTS
    STARTUP_SERVER_PORT =   10008
    SPACE_COASTER_PORT = 10009
    PC_MONITOR_PORT = 10010
    TCP_UDP_REMOTE_CONTROL_PORT = 10013
    # no longer used REMOTE_CLIENT_PORT = 10015 # remote client connection to local clients on PC
    ENCODER_IP_ADDR = SIM_IP_ADDR[0] # Encoder server running on first sim PC 
    ENCODER_SERVER_PORT = 10016 # encoder data broadcasted on this port
    ENCODER_SERVER_CMD_PORT = ENCODER_SERVER_PORT+1  #10017
    REMOTE_SCALE_PORT = 10018
    REMOTE_IMU_PORT = 10019
    PLATFORM_ECHO_PORT = 10020