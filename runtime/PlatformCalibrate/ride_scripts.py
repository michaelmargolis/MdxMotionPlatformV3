# ride_script

# format is: motion,percent,duration
# percent ranges from -100 to 100, duration is in seconds

import time # only for debug

class RideMacros(object):
    def __init__(self, muscle_output):
       self.muscle_output = muscle_output
       self.ride = []
       self.action_index = 0
       self.is_running = False
       self.total_dur = 0.0
       self.elapsed_dur = 0.0

    def read(self, fname):
        with open(fname) as f:
            f.readline()
            self.ride = []
            self.total_dur = 0.0
            for line in f:
                ln = line.rstrip('\n').split(',') 
                dur = float(ln[2])
                self.total_dur += dur
                self.ride.append([ln[0],int(ln[1]), dur])


    def start(self,  fname):
        self.read(fname)
        self.action_index = 0
        action = self.ride[0]
        self.is_running = True
        self.muscle_output.actions[action[0]](action[1], action[2])
        self.elapsed_dur = 0.0
        return self.total_dur

    def abort(self):
        self.is_running = False
        print("Ride stopped")

    def percent_completed(self):
        if  self.total_dur == 0:
            return 0
        else:
            return int(100 * (self.elapsed_dur / self.total_dur ))

    def service(self):
        if self.is_running:
            if self.muscle_output.is_slow_moving or self.muscle_output.is_paused: 
                pass # self.muscle_output.service()
            else:
                self.action_index += 1
                if self.action_index < len(self.ride):
                    action = self.ride[self.action_index]
                    # print "playing action", self.action_index,
                    self.elapsed_dur += self.ride[self.action_index][2]
                    #  print action
                    self.muscle_output.actions[action[0]](action[1], action[2])
                else:
                    self.elapsed_dur = self.total_dur
                    # print "End of ride"

    def get_current_action(self):
        if self.is_running and self.action_index < len(self.ride):
            return self.ride[self.action_index]
        else:
            return None
    
if __name__ == '__main__':

    from muscle_output import MuscleOutput

    muscle_output = muscle_output.MuscleOutput()  
    muscle_output.configure_distance_csv()
    ride = RideMacros(muscle_output)
    ride.start("test.ride")
    while ride.is_running:
        ride.service()
        time.sleep(muscle_output.SLOW_MOVE_TIMER_DUR/1000.0)

