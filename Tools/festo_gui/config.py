# config file for tests

# Set festo parameters
FST_ip = '192.168.0.10' # default IP
fst_bufSize = 1024
WAIT_FESTO_RESPONSE = False # waits for response from festo messages
SHOW_FESTO_PRESSURE = False # above must also be set to True
PRINT_PRESSURE_DELTA = False; # todo fix div when pressure is zero

min_pressure = 0
max_pressure = 6000
period = 10
pause = 1
encoders_port = ""  # "COM28"
