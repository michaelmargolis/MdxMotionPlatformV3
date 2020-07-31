"""
  oscillate.py

  Steps all muscles up and down through full range of pressures
  Pauses at each pressure, reads sensor then adds distance for that pressure into an array
  Updates array of min and max values for each pressure
  Prints message when no min or max values change within a complete cycle
  
"""


import sys
import time
import socket
import traceback
from LaserRangefinder import Laser

LASER_COM_PORT = "COM7"

MIDDLEWARE_IP = "127.0.0.1"
MIDDLEWARE_PORT = 10013
MIN_PRESSURE = 0
MAX_PRESSURE = 6000
STEP_SIZE = 1000  # millibars per step
NBR_STEPS =  1 + ((MAX_PRESSURE - MIN_PRESSURE) / STEP_SIZE)
INTERVAL = 0.01 # 1.0 # seconds between steps
NBR_CYCLES = 3

# create empty list of lists for the data arrays
up_values = [[0] * NBR_STEPS for i in range(NBR_CYCLES)]
down_values = [[0] * NBR_STEPS for i in range(NBR_CYCLES)]

# create arrays to be updated by reading outside the min or max values
up_min_values = [1000] * NBR_STEPS   # init to an impossibly large distance 
up_max_values = [0] * NBR_STEPS      # init to an impossibly small distance
down_min_values = [1000] * NBR_STEPS   # init to an impossibly large distance 
down_max_values = [0] * NBR_STEPS      # init to an impossibly small distance

laser = Laser()  # instantiate laser rangefinder object

def get_distance():
    if laser.read(3):
        return laser.distance
    else:
        return 0

def info_reporter(info):
    print info

def move(pressure):
    data = '"' + str(pressure) + '"'
    for i in range(5):
       data += ',"' + str(pressure) + '"'
    # print data
    msg = '"step":[' + data + ']\n'
    # print msg
    #sock.sendto(msg, (UDP_IP, UDP_PORT))
    
def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    laser.set_info_reporter(info_reporter)
    if laser.connect(LASER_COM_PORT) == False:
        print "unable to connect to laser on: ", LASER_COM_PORT
        exit()

    
    for cycle in range (NBR_CYCLES):
        print "\ncycle", cycle
        print("moving up")
        for i in range (NBR_STEPS):
            time.sleep(INTERVAL)
            distance = get_distance()
            print distance
            up_values[cycle][i] = distance
            if distance < up_min_values[i]:
               up_min_values[i] = distance
               if cycle > 0: 
                  print format("min value updated for pressure %d in cycle %d" % (i * STEP_SIZE, cycle))
            if distance > up_max_values[i]:
               up_max_values[i] = distance
               if cycle > 0: 
                  print format("max value updated for pressure %d in cycle %d" % (i * STEP_SIZE, cycle))
        print("\nmoving down")
        for i in range (NBR_STEPS):
            move(MAX_PRESSURE - i*STEP_SIZE)
            time.sleep(INTERVAL)
            distance = get_distance()
            print distance
            down_values[cycle][i] = distance
            if distance < down_min_values[i]:
               down_min_values[i] = distance
               if cycle > 0: 
                  print format("min value updated for pressure %d in cycle %d" % (i * STEP_SIZE, cycle))
            if distance > down_max_values[i]:
               down_max_values[i] = distance
               if cycle > 0: 
                  print format("max value updated for pressure %d in cycle %d" % (i * STEP_SIZE, cycle))
    
    print "up values\n", up_values
    print "down values\n", down_values
    print "down min values\n", down_min_values
    print "down min values\n", down_max_values
    print "up min valus\n", up_min_values
    print "up max values\n", up_max_values



if __name__ == "__main__":
    main()

    
"""
def calibrate():
    minMaxTable = [[0 for x in range(2)] for y in range(sensorCount)]
    upTable = [[0 for x in range(sensorCount)] for y in range(stepCount)]
    downTable = [[0 for x in range(sensorCount)] for y in range(stepCount)]
    
   
    for sensor in range(sensorCount):
        FST_sendRaw(minPressure, sensor) # chair at max distance
    time.sleep(3)
    
    data = getSensorData()  
    for i in range(sensorCount):
        minMaxTable[i][1] = data[i]  #store max distances  
    
    #step up through pressure ranges
    for step in range(stepCount):  
         pressure = indexToPressure(step)
         for i in range(sensorCount):
             FST_sendRaw(pressure, i) 
         time.sleep(2)
         upTable[step] = getSensorData()
         print step, upTable[step]		 
    print upTable
    
    # the actuators are now at minimum distance
    data = getSensorData()  
    for i in range(sensorCount):         
        minMaxTable[i][0] = data[i]
    
    #step down through pressure ranges
    for s in range(stepCount):  
         step = stepCount-s-1
         pressure =  indexToPressure(step)              
         for i in range(sensorCount):
             FST_sendRaw(pressure, i) 
         time.sleep(2)
         downTable[step] = getSensorData()                 
    print downTable
    print "minMaxTable", minMaxTable

    with open(csvFname, 'wb') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr.writerow( ('Min and Max Heights',) )
        wr.writerows(minMaxTable)
        wr.writerow( ('Table of Upgoing Heights',stepCount) )
        wr.writerows(upTable)
        wr.writerow( ('Table of Downgoing Heights',stepCount) )
        wr.writerows(downTable)  

            
#returns the pressure at a given index            
def indexToPressure(index):
    return   index * stepSize + minPressure     
    
def getSensorData():
    SIMULATE_SENSORS = False #True
    if SIMULATE_SENSORS:
        msg = [700,701,702,703,704,705]
           
    else:
        while not sensorQ.empty(): 
            msg = sensorQ.get(False)
        msg = sensorQ.get(True) #wait for next message (todo timeout needed)
    #print "got q msg: ", msg 
    return msg[:]
     
            
    
def scale( val, src, dst) :   # the Arduino 'map' function written in python  
  return (val - src[0]) * (dst[1] - dst[0]) / (src[1] - src[0])  + dst[0]
   
def FST_sendRaw(pressure, index):
    try:
        command = "maw"+str(64+index)+"="+str(pressure)
        print command,
        command = command +"\r\n"
        try:
            FSTs.sendto(command,(FST_ip, FST_port))
        except:
            print "Error sending to Festo"
        if index == sensorCount-1:
            print "\n"
		
    except: 
        e = sys.exc_info()[0]
        print e        

#  sensor message socket
class MyTCPHandler(SocketServer.StreamRequestHandler):
        
    def handle(self): 
        global sensorQ
        self.queue = sensorQ        
        while True:
            if kbhit():
                c = getch()                
                if ord(c) == 27: # ESC
                    sys.exit([0])        
            try:         
                json_str = self.rfile.readline() #.strip()[1:]
                if json_str != None:                          
                    #print json_str                  
                    #print "{} wrote:".format(self.client_address[0])       
                    try:                 
                        j = json.loads(json_str)                
                        #print "got:", j                                                  
                        if j['method'] == 'sensorEvent':                                              #
                           #for n in j['distanceArgs']:                         
                              #print j['distanceArgs'], n     
                           self.queue.put(j['distanceArgs'])                                                                                                           
                    except ValueError:
                        print "nothing decoded", "got:", json_str
                        continue
                    except socket.timeout:
                        print "socket timeout" 
                        continue                          
            except : 
                  print "Connection broken"
                  break;                   
            
if __name__ == "__main__":    
    
    # setup the UDP Socket  
    TESTING = False #True
    if TESTING: 
        FST_ip = 'localhost'
        FST_port = 991 
    else:  
       FST_ip = '192.168.10.10'
       FST_port = 991 
    print "Calibrate script opening festo socket on ", FST_port
    FSTs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # start the sensor message receiver server 
    HOST, PORT = '', 10009  

    # Create the server, binding to localhost on port effector port
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)
    remote_server_thread = threading.Thread(target=server.serve_forever)
    remote_server_thread.daemon = True
    remote_server_thread.start()
    print "Calibrate ready to receive sensor data on port ",PORT   
    #server.serve_forever()
    calibrate()     
"""