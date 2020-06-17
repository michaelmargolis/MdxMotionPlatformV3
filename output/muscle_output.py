"""
muscle_output.py
  percents are movement of the actuators:
    0 is the actuator position with no pressure
    100 is the position with max pressure.
  The non-linear relationship between pressure and movement is 
    adjusted using previously collected data
    
  Supports Festo controllers using easyip port
     see: https://github.com/kmpm/fstlib
"""
import sys
import time
import festo_itf
import gui_sleep

import numpy as np
import traceback

import logging
log = logging.getLogger(__name__)

PRINT_MUSCLES = True # for testing

class MuscleOutput(object):
    def __init__(self, FST_ip = '192.168.0.10'):
        self.festo = festo_itf.Festo(FST_ip)
        self.in_pressures = [0]*6
        self.echo_method = None  # if set, percents passed to this method
        self.UPDATE_FRAME_RATE = 50  # ms between updates
        self.up_indices = [0]*6
        self.up_curves = None
        self.down_indices = [0]*6
        self.down_curves = None
        self.progress_callback = None
        self.prev_distances = [0]*6
        self.percent_factor = 2 #  divide distance by this factor to get percent
        log.warning("TODO, replace hard coded percent divisor in muscle_output")
        log.info("muscle_output started with %d ms frame rate", self.UPDATE_FRAME_RATE )

    def set_d_to_p_curves(self, up_curves, down_curves):
        self.up_curves = up_curves
        self.down_curves = down_curves
        self.nbr_distance_columns = up_curves.shape[1]

    def set_d_to_p_indices(self, up_indices, down_indices):
        self.up_indices = up_indices
        self.down_indices = down_indices
        up_str = ','.join("%d" % i for i in up_indices)
        down_str = ','.join("%d" % i for i in down_indices)
        log.info("Dist to Pressure up idx = %s, down = %s", up_str, down_str)

    def set_echo_method(self, echo): 
        # if provided, the output request message is echoed to this method
        self.echo_method = echo

    def set_progress_callback(self, cb):
        self.progress_callback = cb

    def send_pressures(self, pressures):
        self.festo.send_pressures(pressures)
        
    def brake(self):
        # enables brakes on sliders to avoid unintended movement
        print "todo brake"

    def get_pressures(self):
        self.in_pressures = self.festo.get_pressure()
        return  self.in_pressures

    def set_wait(self, state):
        self.festo.set_wait(state)
        log.debug("output module wait for festo pressure set to %d", state)

    def set_pistion_flag(self, state):
        if state:
            self.activate_piston_flag = 1
        else:
            self.activate_piston_flag = 0

    def set_payload(self, payload_kg):
        #  set total weight in killograms
        self.loaded_weight = payload_kg

    def get_output_status(self):
        #  return string describing output status
        if self.festo.wait:
            if not self.festo.netlink_ok:
                return ("Error: check Festo power and LAN", "red")
            else:
                return (format("Festo network ok (latency=%d ms)" % self.festo.msg_latency), "green")
        else:
           return ("Festo msgs not checked", "orange")
        
        if False:  # enable this to check festo pressures
            ###self._get_pressure()
            if not self.festo.netlink_ok:
                return ("Festo network error (check ethernet cable and festo power)", "red")
            else:    
                bad = []
                in_pressures = self.festo.get_pressure()
                if 0 in in_pressures:
                    for idx, v in enumerate(in_pressures):
                       if v == 0:
                          bad.append(idx)
                    if len(bad) == 6:
                       return ("Festo Pressure Zero on all muscles", "red")
                    else:
                       bad_str = ','.join(map(str, bad))                   
                       return ("Festo Pressure Zero on muscles: " + bad_str, "red")
                elif any(p < 10 for p in self.pressure_percent):
                    return ("Festo Pressure is Low", "orange")
                elif any(p < 10 for p in self.pressure_percent):
                    return ("Festo Pressure is High", "orange")
                else:
                    return ("Festo Pressure is Good", "green")  # todo, also check if pressure is low
        else:        
            return ("Festo controller responses not being used", "orange")

    def prepare_ride_start(self):
        pass

    def prepare_ride_end(self):
        pass

    def move_distance(self, distances):
        for idx, d in enumerate(distances):
            distances[idx] = int(round(d))
        # print "in move distances", distances
        try:
            out_pressures = self.distance_to_pressure(distances)
            # print "pressures in move_distance", out_pressures
            self.festo.send_pressures(out_pressures)
            if self.echo_method != None:
                percents = []
                for d in distances:
                     percents.append(d / self.percent_factor)
                self.echo_method(percents)
        except:
            print "error in move distance", sys.exc_info()[0], traceback.format_exc(),distances
            log.error("error in move_distancet %s", sys.exc_info()[0])

    def move_percent(self, percents):
        self.move_distance(percents * self.percent_factor) 
   
    def distance_to_pressure(self, distances):
        pressures = []
        for i in range(6):
            # todo check if we need to ignore case where distance does not change
            # self.distances[i] = int(round(np.clip(2*percent[i],0,199)))  # todo improve accuracy of percent to distance
            try: 
                if distances[i] >= self.nbr_distance_columns:
                    distances[i] = self.nbr_distance_columns-1
                if distances[i] <= self.prev_distances[i]: # moving down
                    # print self.down_indices[i], self.down_curves[self.down_indices[i]][distance]
                    p = self.down_curves[self.down_indices[i]][int(distances[i])]
                else:  # moving up
                    p = self.up_curves[self.up_indices[i]][int(distances[i])]
                pressures.append(p)
            except:
                print "error in distance_to_pressure", sys.exc_info()[0], traceback.format_exc()
                print distances, "\ni=", i

        # print pressures
        self.prev_distances = distances
        return pressures

        
    def calibrate(self):
        # moves platform to mid pressure to determine best d_to_p files
        self.slow_pressure_move(0,3000, 1000)

    def slow_move(self, start, end, rate_cm_per_s):
        # moves from the given start lengths/percents to the end values at the given duration       
        #  caution, this moves even if disabled
        log.debug("in slow move, max dist in cm = %d",  max(end-start)/10)
        interval = 50  # time between steps in ms
        steps = (max(end-start)/10) / interval
        if steps < 1:
            self.move_distance(end)
        else:
            current = start
            print "moving from", start, "to", end, "steps", steps
            # print "percent", (end[0]/start[0]) * 100
            delta = [float(e - s)/steps for s, e in zip(start, end)]
            print "move_func todo in step!!!!!!!!!!!"
            for step in xrange(steps):
                current = [x + y for x, y in zip(current, delta)]
                self.move_distance(current)
                gui_sleep.sleep(interval / 1000.0)
                
    def slow_pressure_move(self, start_pressure, end_pressure, duration_ms):
        #  caution, this moves even if disabled
        interval = 50  # time between steps in ms
        steps = duration_ms / interval
        if steps < 1:
            self.send_pressures([end_pressure]*6)
        else:            
            current = [start_pressure]*6
            print "moving from", start_pressure, "to", end_pressure, "steps", steps
            delta = float(end_pressure - start_pressure)/steps
            print "delta = ", delta
            for step in range(steps):
                current  =  [p+delta for p in current]
                print current
                time.sleep(interval / 1000.0)
                if self.progress_callback:
                    self.progress_callback(100 * step/steps)


    """
    ##### legacy code for chairs
    def _legacy_move_to(self, lengths):
        #  print "lengths:\t ", ",".join('  %d' % item for item in lengths)
        load_per_muscle = self.loaded_weight / 6  # if needed we could calculate individual muscle loads
        pressure = []
        for idx, len in enumerate(lengths):
            pressure.append(int(1000*self._convert_MM_to_pressure(idx, len-self.fixed_len, load_per_muscle)))
        self.send_pressures(pressure)
   
    def set_platform_params(self, min_actuator_len, max_actuator_len, fixed_len):
        #  paramaters for a conventional (normal or inverted) stewart platform
        print "todo temp remove and do the percent calc in kinematics"
        self.min_actuator_len = min_actuator_len
        self.max_actuator_len = max_actuator_len
        self.fixed_len = fixed_len
        self.prev_pos = [0, 0, 0, 0, 0, 0]  # fixme requested distances stored here 

   
    def _convert_MM_to_pressure(self, idx, muscle_len, load):
        #  returns pressure in bar
        #  calculate the percent of muscle contraction to give the desired distance
        percent = (self.max_actuator_len - self.fixed_len - muscle_len) / float(self.max_actuator_len - self.fixed_len)
        #  check for range between 0 and .25
        print "muscle Len =", muscle_len, "percent =", percent
        distDelta = muscle_len-self.prev_pos[idx]  # the change in length from the previous position
        if distDelta < 0:
            #  pressure = 30 * percent*percent + 12 * percent + .01  # assume 25 Newtons for now
            pressure = 35 * percent*percent + 15 * percent + .03  # assume 25 Newtons for now
            if PRINT_MUSCLES:
                print("muscle %d contracting %.1f mm to %.1f, pressure is %.2f"
                      % (idx, distDelta, muscle_len, pressure))
        else:
            pressure = 35 * percent*percent + 15 * percent + .03  # assume 25 Newtons for now
            if PRINT_MUSCLES:
                print("muscle %d expanding %.1f mm to %.1f, pressure is %.2f"
                      % (idx, distDelta, muscle_len, pressure))

        self.prev_pos[idx] = muscle_len  # store the muscle len
        MAX_PRESSURE = 6.0 
        MIN_PRESSURE = .05  # 50 millibar is minimin pressure
        pressure = max(min(MAX_PRESSURE, pressure), MIN_PRESSURE)  # limit range 
        return pressure
    """
    
if __name__ == "__main__":
    log_level = logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%H:%M:%S')
    out = MuscleOutput()
    out.slow_pressure_move(0,3000, 1000)
    out.slow_pressure_move(3000, 2000,  1000)
