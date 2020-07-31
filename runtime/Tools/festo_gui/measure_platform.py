"""
measure_platform.py

steps platform and captures sensor data
steps and com ports defined in the file config.py

"""

import sys
import socket
import traceback
import math
import time
import msvcrt
import config as cfg
from LaserRangefinderP2 import Laser

sys.path.insert(0, '..')
from fstlib import easyip

REQUEST_ACTUAL_PRESSURES = False # True requests pressure values from Festo

# Set the socket parameters for festo requests
FST_ip = '192.168.0.10'
FST_port = easyip.EASYIP_PORT
bufSize = 1024

# 3 lasers per board on two boards
if cfg.number_of_lasers < 3:
    lasers_1to3 = Laser(cfg.number_of_lasers)
    lasers_4to6 = Laser(0)
else:
    lasers_1to3 = Laser(3)
    lasers_4to6 = Laser(cfg.number_of_lasers-3)
    
abort_flag = False

def main():
    # create festo client
    steps_per_half_cycle = (1+((cfg.end_pressure-cfg.start_pressure)/cfg.step_size))
    print format("%d cycles with %d Pressure steps from %d to %d in %d mb steps" % 
        (cfg.number_of_cycles, steps_per_half_cycle, cfg.start_pressure, cfg.end_pressure, cfg.step_size)) 
    print format("%.1f second delay after move before measuring" % cfg.delay_before_measuring)
    print format("lasers 1-3 on %s, 4-6 on %s" % (cfg.boardA_port, cfg.boardB_port))
    
    global FSTs,FST_addr
    try:
        FSTs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        FST_addr = (FST_ip, FST_port)
        FSTs.bind(('0.0.0.0', 0))
        FSTs.settimeout(1)  # timout after 1 second if no response
        print "Using Festo controller socket at",  FST_ip, FST_port
        
        if lasers_1to3.connect(cfg.boardA_port) == False:
            print "Unable to connect to laser board A on", cfg.boardA_port, ", exiting!"
            exit(1)
        lasers_1to3.set_info_reporter(info_reporter)
        if cfg.number_of_lasers > 3:
            if lasers_4to6.connect(cfg.boardB_port) == False:
                print "Unable to connect to laser board B on", cfg.boardB_port, ", exiting!"
                exit(1)
        lasers_4to6.set_info_reporter(info_reporter)
        
    except Exception as e:
        s = traceback.format_exc()
        print(str(e), s)
        
    pressures = range(cfg.start_pressure, cfg.end_pressure+cfg.step_size, cfg.step_size)+ range(cfg.end_pressure,cfg.start_pressure-cfg.step_size,-cfg.step_size)
    global abort_flag
    for i in range (10): # create no more than 10 files
        if abort_flag:
            break
        with open(format("weight%d.csv" % i), 'w+') as fh:
            input = raw_input("\nEnter a weight from 0 to 100kg (or -1 quit) ")
            if input == '-1':
                abort_flag = True
                break
            try:
                weight = float(input)
            except:
               break
            write_header(fh, weight, steps_per_half_cycle*2)
            if cycles(cfg.number_of_cycles, fh, pressures) == False:
                break #user abort
    print "\n Done" 
    FSTs.close()
 
def cycles(nbr_cycles, fh, pressures):
    # reads and writes data for all cycles to the given file handle
    # returns false if user aborts because of invalid data
    global abort_flag
    for cycle in range(nbr_cycles):
        for p in pressures:
            p_list = [p]*6
            send_pressures(p_list)
            row = measure(p)
            if abort_flag:
                return False
            actuals = read_pressure(p_list)
            print '\r{0}'.format("cycle %d: %s" % (cycle, row[:-1])),
            #  print format("cycle %d: %s" % (cycle, row[:-1])),
            if row == "":
                abort_flag = True
                return False
            if actuals != None:
               diff = [act - req for req, act in zip(p_list, actuals)]
               # print ','.'join(format("%d" % p) for p in actuals))
               diff_str = "," +  ','.join(format("%d" % p) for p in diff)
               print diff_str,
            else:
              diff_str = ""
            fh.write(row + diff_str + '\n' )
    return True

def measure(p):
    time.sleep(cfg.delay_before_measuring)
    if check_abort():
        return ""
    distA, qA = lasers_1to3.group_multi_read(cfg.samples_per_step)
    distB, qB = lasers_4to6.group_multi_read(cfg.samples_per_step)
    while validate(distA + distB, 5) ==  False:
        # reread if any value not within 5 percent of averate
        distA, qA = lasers_1to3.group_multi_read(cfg.samples_per_step)
        distB, qB = lasers_4to6.group_multi_read(cfg.samples_per_step)
    a = ','.join(format("%0.1f" % f) for f in distA)
    b= ','.join(format("%0.1f" % f) for f in distB) 
    return format("%d,%s,%s" % (p, a, b))

def validate(data, tolerance):
    # if average data values not within tolerence, q to quit, r to retry, s to skip
    tolerance = tolerance *.01
    mean = sum(data)/ cfg.number_of_lasers
    is_ok = True 
    global abort_flag
    if mean == 0:
        is_ok = False
    else:
        for idx, d in enumerate(data):
            if idx <  cfg.number_of_lasers and abs((d-mean)/mean) > tolerance:
                print format("laser  %d is out of tolerance with reading of %.1f" % (idx+1, d))
                is_ok = False
    if is_ok:
        return True
    else:
        while True:
            action = raw_input("q to quit, r to retry, s to skip ")
            if action == 's':
                return True
            elif action == 'r':
                return False  
            elif action  == 'q':
                abort_flag = True;
                return True # the program will exit      

def  write_header(fh, weight, steps_per_cycle): 
    fh.write(format("WEIGHT,%d\n" % weight))
    fh.write(format("STEP_SIZE,%d\n" % cfg.step_size))
    fh.write(format("STEPS_PER_CYCLE,%d\n" % (steps_per_cycle)))
    fh.write(format("CYCLES,%d\n" % cfg.number_of_cycles))
    fh.write(format("DATA_ROW,%d\n" % 8))
    fh.write(",\n")
    fh.write("Pressure (mbar)")
    for i in range(6):  # sensor column labels
         fh.write(format(",LRF %d (mm)" % i))
    if REQUEST_ACTUAL_PRESSURES:
        for i in range(6):  # Actual pressures column labels
            fh.write(format(",delta mb %d" % i))
    fh.write("\n")
 
def check_abort():
    if msvcrt.kbhit():
        c = msvcrt.getch()
        if ord(c) == 27: # ESC
            print "press escape again to exit, any other key to continue"
            c = msvcrt.getch()
            if ord(c) == 27: # ESC
                return True
        else:
            print "press any key to continue"
            c = msvcrt.getch()
    return False

def info_reporter(info):
    print info
    
def send_pressures(muscle_pressures):
    try:
        # print "sending pressures:", muscle_pressures
        packet = easyip.Factory.send_flagword(0, muscle_pressures)
        try:
            output_festo_packet(packet)
            # print "festo output:", packet, FST_port
        except socket.timeout:
            print "timeout waiting for replay from", FST_addr
    except:
        e = sys.exc_info()[0]
        s = traceback.format_exc()
        print "error sending to Festo", e, s
        
def read_pressure(muscle_pressures):
    if REQUEST_ACTUAL_PRESSURES:
        try:
            actual_pressures = get_festo_pressure()
            diff = [act - req for req, act in zip(muscle_pressures, actual_pressures)]
            # pressure_percent = [int(d * 100 / req) for d, req in zip(diff, muscle_pressures)]
            #print muscle_pressures, diff
            return actual_pressures
        except socket.timeout:
            print "timeout waiting for replay from", FST_addr
    return None

def output_festo_packet(packet):
    data = packet.pack()
    #  print "sending to", FST_addr
    global FSTs, FST_addr
    FSTs.sendto(data, FST_addr)
    if REQUEST_ACTUAL_PRESSURES:
        #  print "in sendpacket,waiting for response..."
        data, srvaddr = FSTs.recvfrom(bufSize)
        resp = easyip.Packet(data)
        #  print "in senddpacket, response from Festo", resp
        if packet.response_errors(resp) is not None:
            print "errors=%r" % packet.response_errors(resp)
    else:
        resp = None
    return resp

def get_festo_pressure():
    # first arg is the number of requests you'r making. Leave it as 1 always
    # Second arg is number of words you are requesting (probably 6, or 16)
    # third arg is the offset.  (pressure values are expected from offset 10)
    # words 0-5 are what you sent it.
    # words 6-9 are not used
    # words 10-15 are the current values of the presures
    # packet = easyip.Factory.req_flagword(1, nbr registers, register index)
    #print "attempting to get pressure"
    try:
        packet = easyip.Factory.req_flagword(1, 6, 10)
        resp = output_festo_packet(packet)
        values = resp.decode_payload(easyip.Packet.DIRECTION_REQ)
        #  print list(values)
        return list(values)
    except socket.timeout:
        print "timeout waiting for Pressures from Festo"
    return [0,0,0,0,0,0]


if __name__ == '__main__':
    main() 
