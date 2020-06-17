"""
Simple kinematics for the nextgen platform
percents are movement of the actuators:
  0 is the actuator position with no pressure
  100 is the position with max pressure.
  The non-linear relationship between pressure and movement is 
    adjusted using previouly collected data 
"""
import sys
import time
import festo_itf

import csv
import numpy as np

 #function to scale a value, range is a list containing: (from_min, from_max, to_min, to_max)
def map(self, value, range):
    if value > range[1]:  # limit max
        return range[3]
    if value < range[0]:  # limit min
        return range[2]       
    if range[1] == range[0]:
        return range[2] #avoid div by zero error
    else:      
        return ( (value - range[0]) / (range[1] - range[0]) ) * (range[3] - range[2]) + range[2]
            
FULL_SPEED = 0 

class MuscleOutput(object):
    def __init__(self):
        self.festo = festo_itf.Festo() 
        self.current_percents = [50]*6 
        self.target_percents = [0]*6
        self.in_pressures = [0]*6
        self.percent_step =  [0]*6 # used for slow move when percents != target
        self.SLOW_MOVE_TIMER_DUR = 50  # ms between updates
        self.is_slow_moving = False
        self.pause_timer = 0
        self.is_paused = False
        self.echo_method = None  # if set, percents passed to this method

        self.actions = {'moveX':self.moveX, 'moveY':self.moveY, 'moveZ':self.moveZ,
               'roll':self.roll, 'pitch':self.pitch, 'yaw':self.yaw, 'pause':self.pause}
        
        self.action_names = ['moveX','moveY','moveZ','roll','pitch','yaw','pause']
        self.cmd = [self.moveX, self.moveY,self.moveZ,self.roll,self.pitch,self.yaw,self.pause]


    def service(self):
        if self.is_slow_moving:
            for i in range(6):
                if self.current_percents[i] < self.target_percents[i]:
                    self.current_percents[i] += self.percent_step[i]
                    if self.current_percents[i] > self.target_percents[i]:
                        self.current_percents[i] = self.target_percents[i]
                elif self.current_percents[i] > self.target_percents[i]:
                    self.current_percents[i] += self.percent_step[i]
                    if self.current_percents[i] < self.target_percents[i]:
                        self.current_percents[i] = self.target_percents[i]
                self.current_percents = np.clip(self.current_percents,0,100)
                # print "current % =", self.current_percents, ", target %=", self.target_percents
            self.move_percent(self.current_percents)
            if self.current_percents == self.target_percents:
                self.is_slow_moving = False
                # print "End of slow move"
        if self.is_paused and self.pause_timer <= time.time():
            self.is_paused = False
            # print "End of pause"
        
    def set_echo_method(self, echo): 
        self.echo_method = echo

    def info_reporter(self, info_txt):
        print info_txt 

    def send_pressures(self, pressures):
        self.festo.send_pressures(pressures)

    def get_pressures(self):
        self.in_pressures = self.festo.get_pressure()
        return  self.in_pressures

    def set_wait(self, state):
        self.festo.set_wait(state)

    """ move percent args range from -100 to +100, 0 has the platform centered and level
       move args are translated into actuator percents from 0 to 100
    
    """
    def moveX(self, percent,interval=FULL_SPEED):
        percent = int((percent + 100)/2)
        percents = [50]*6 # default values
        percents[2] =  percents[5] = map(percent, [0, 100, EXTENT, 0])
        percents[0] =  percents[1] = map(percent, [0, 100, 0, EXTENT])
        if percent >= 50:
           percents[3] =  percents[4] = map(percent, [50, 100, EXTENT / 2, EXTENT / 3])
        
        elif percent < 50:
           percents[3] =  percents[4] = map(percent, [50, 0, EXTENT / 2, EXTENT / 3])
        self.move_percent(percents)

    def moveY(self, percent,interval=FULL_SPEED):
        percent = int((percent + 100)/2)
        percents = [50]*6 # default values
        percents[4] = percents[5] = map(percent, [0, 100, 0, EXTENT])
        percents[3] = map(percent, [0, 100, EXTENT, 0])
        if percent >= 50:
            percents[0] =  percents[1] = percents[2] = map(percent, [50, 100, EXTENT / 2, EXTENT / 3])
        elif percent < 50:
            percents[0] = percents[1] = percents[2] = map(percent, [50, 0, EXTENT / 2, EXTENT / 3])
        self.move_percent(percents)

    def moveZ(self, percent,interval=FULL_SPEED):
        if interval == FULL_SPEED:
            self.info_reporter(format("moveZ %d percent" % (percent)))
        else:
            self.info_reporter(format("moveZ %d percent over %.2f seconds" % (percent, interval)))
        percent = int((percent + 100)/2)
        for i in range(6):
            if interval != FULL_SPEED:
                self.percent_step[i] =  (percent-self.current_percents[i]) / (interval/self.SLOW_MOVE_TIMER_DUR*1000)
                #  print "percent calc:", interval/self.SLOW_MOVE_TIMER_DUR*1000,  (percent-self.current_percents[i]), (percent-self.current_percents[i])  / (interval/self.SLOW_MOVE_TIMER_DUR*1000)
                self.is_slow_moving = True
            else:
                self.percent_step[i] = percent

            self.current_percents[i] += self.percent_step[i]
            self.target_percents[i] = percent  
        self.move_percent(self.current_percents)

    def roll(self, percent,interval=FULL_SPEED):
        percent = int((percent + 100)/2)
        # self.info_reporter(format("roll %d percent over %.2f seconds" % (percent, interval)))
        dur = (interval/self.SLOW_MOVE_TIMER_DUR*1000)
        self.target_percents[0] = self.target_percents[5] = 50
        self.target_percents[1] = self.target_percents[2] = percent
        self.target_percents[3] = self.target_percents[4] = 100-percent
        if interval != FULL_SPEED:
            for i in range(6):
                self.percent_step[i] =  (self.target_percents[i] - self.current_percents[i]) / dur
            self.is_slow_moving = True
        else:
            self.move_percent(self.target_percents)

        print "Roll: target, step",  self.target_percents, self.percent_step 


    def pitch(self, percent,interval=FULL_SPEED):
        percent = int((percent + 100)/2)
        # self.info_reporter(format("pitch %d percent over %.2f seconds" % (percent, interval)))
        dur = (interval/self.SLOW_MOVE_TIMER_DUR*1000)
        self.target_percents[0] = self.target_percents[2] = self.target_percents[3] = self.target_percents[5] = 100-percent
        self.target_percents[1] = self.target_percents[4] = percent
        if interval != FULL_SPEED:
            for i in range(6):
                self.percent_step[i] =  (self.target_percents[i] - self.current_percents[i]) / dur
            self.is_slow_moving = True
        else:
            self.move_percent(self.target_percents)

    def yaw(self, percent,interval=FULL_SPEED):
        percent = int((percent + 100)/2)
        # self.info_reporter(format("yaw %d percent over %.2f seconds" % (percent, interval)))
        dur = (interval/self.SLOW_MOVE_TIMER_DUR*1000)
        self.target_percents[0] = self.target_percents[2] = self.target_percents[4] = percent
        self.target_percents[1] = self.target_percents[3] = self.target_percents[5] = 100-percent
        if interval != FULL_SPEED:
            for i in range(6):
                self.percent_step[i] =  (self.target_percents[i] - self.current_percents[i]) / dur
            self.is_slow_moving = True
        else:
            self.move_percent(self.target_percents)

    def pause(self, ignore, interval):
        self.info_reporter(format("pause %.2f seconds" % (interval)))
        self.pause_timer = time.time() + interval
        self.is_paused = True
        

    def move_percent(self, values):
        values = [ int(round(val)) for val in values ]
        out_pressures = self.percent_to_pressure(values, self.current_percents)
        self.current_percents = values 
        self.festo.send_pressures(out_pressures)
        if self.echo_method != None:
            self.echo_method(values)

    def percent_to_pressure(self, percent, prev_percent):
        pressures = []
        for i in range(6):
            # todo check if we need to ignore case where percent does not change
            distance = int(round(np.clip(2*percent[i],0,199)))  # todo improve accuracy of percent to distance
            if percent[i] <= prev_percent[i]: # moving down
                p = int(self.DownDtoP[distance])
            else:  # moving up
                p = int(self.UpDtoP[distance])
            pressures.append(p)
        return pressures
        
    def configure_distance_csv(self):
        try:
            self.UpDtoP = np.loadtxt('UpDtoP.csv')
        except:
            print "error opening UpDtoP.csv file", sys.exc_info()[0]
            
        try:
            self.DownDtoP = np.loadtxt('DownDtoP.csv')           
        except:
            print "error opening DownDtoP.csv file", sys.exc_info()[0]      