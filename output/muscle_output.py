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
import numpy as np
import traceback

import output.festo_itf as festo_itf
import common.gui_utils as gutil

import logging
log = logging.getLogger(__name__)

class MuscleOutput(object):
    def __init__(self, d_to_p_func, FST_ip = '192.168.0.10', max_actuator_range = 200):
        self.distance_to_pressure = d_to_p_func
        self.festo = festo_itf.Festo(FST_ip)
        self.max_actuator_range = max_actuator_range # max contraction in mm
        self.in_pressures = [0]*6
        self.progress_callback = None
        self.percent_factor = self.max_actuator_range / 100 #  divide distance by this factor to get percent
        log.warning("TODO, replace hard coded percent divisor in muscle_output")

    def set_progress_callback(self, cb):
        self.progress_callback = cb

    def send_pressures(self, pressures):
        self.festo.send_pressures(pressures)
        
    def brake(self):
        # enables brakes on sliders to avoid unintended movement
        print("todo brake")

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
        #  set total weight in kilograms
        #  Todo - was used on platforms without encoders, not yet supported in V3
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
            self.percents = []
            for d in distances:
                self.percents.append(d / self.percent_factor)
        except Exception as e:
            print("error in move distance", str(e), traceback.format_exc(),distances)
            log.error("error in move_distance %s, %s", e, sys.exc_info()[0])

    def move_percent(self, percents):
        self.move_distance(percents * self.percent_factor) 

    def calibrate(self):
        # moves platform to mid pressure to determine best d_to_p files
        self.slow_pressure_move(0,3000, 1000)

    def slow_move(self, start, end, rate_cm_per_s):
        # moves from the given start to end lengths at the given duration
        #  caution, this moves even if disabled
        rate_mm = rate_cm_per_s *10
        interval = .05  # ms between steps
        distance = max(end - start, key=abs)
        # print("max distance=", distance)
        dur = abs(distance) / rate_mm
        steps = int(dur / interval)
        #print("steps", steps, type(steps))
        if steps < 1:
            self.move_distance(end)
        else:
            current = start
            print("moving from", start, "to", end, "steps", steps)
            # print "percent", (end[0]/start[0]) * 100
            delta = [float(e - s)/steps for s, e in zip(start, end)]
            for step in range(steps):
                current = [x + y for x, y in zip(current, delta)]
                current = np.clip(current, 0, 6000)
                self.move_distance(current)
                gutil.sleep_qt(interval)

    def slow_pressure_move(self, start_pressure, end_pressure, duration_ms):
        #  caution, this moves even if disabled
        interval = 50  # time between steps in ms
        steps = duration_ms / interval
        if steps < 1:
            self.send_pressures([end_pressure]*6)
        else:            
            current = [start_pressure]*6
            print("moving from", start_pressure, "to", end_pressure, "steps", steps)
            delta = float(end_pressure - start_pressure)/steps
            print("delta = ", delta)
            for step in range(steps):
                current  =  [p+delta for p in current]
                print(current)
                gutil.sleep_qt(interval / 1000.0)
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
            if False # PRINT_MUSCLES:
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
