"""
D_to_P.py  Distance to Pressure runtime routines

The module comprises runtime routines to convert platform kinematic distances to festo pressures.
Previously obtained distance to pressure lookup tables for various loads are interrogated at runtime to determine
 the closest match to the current load.

This version only supports the new platform as the chairs do not currently have real time distance measurement capability

The D_to_P  class is instantiated with an argument specifying the number of distance values, currently 200 (for 0-199mm)

    load_DtoP(fname) loads distance to pressure lookup tables
       returns True if valid data has been loaded 
       If successful, the lookup tables are available as class attributes named d_to_p_up  and d_to_p_down.
       It is expected that each up and down table will have six to ten rows containing data for the range of working loads 
       the set_index method described below is used to determine the curve that best fits the current platform load

    set_index(self, pressure, distances, dir)
       Finds closest curve matching the current distance and pressure, or none if data available
       These curves should be passed to the festo output module for runtime conversion
       
Utility methods to create the distance to pressure files are in d_to_p_prep.py

"""
import os
import traceback
import numpy as np

NBR_DISTANCES = 200 # 0-199mm with precision of 1mm

class D_to_P(object):

    def __init__(self, nbr_columns):
       self.nbr_columns = nbr_columns 
       assert (nbr_columns == NBR_DISTANCES), format("Expected %d distance values!" % NBR_DISTANCES)
       self.d_to_p_up = None  # up-going distance to pressure curves
       self.d_to_p_down = None
       self.up_curve_idx = [0]*6  # index of the up-going curve closest to the current load
       self.down_curve_idx = [0]*6
       self.rows = 0 # number of load values in the DtoP file
       self.prev_distances = [0]*6

    def load(self, fname = 'output\DtoP.csv'):
        # initializes d_to_p arrays from data in the given file
        try:
            d_to_p = np.loadtxt(fname, delimiter=',', dtype=int)
            assert(d_to_p.shape[1] == self.nbr_columns), format("expected %d columns, found %d\n", (self.nbr_columns, d_to_p.shape[1]))
            self.d_to_p_up, self.d_to_p_down =  np.split(d_to_p,2)
            assert(self.d_to_p_up.shape[0] == self.d_to_p_down.shape[0]), "up and down DtoP rows don't match"
            self.rows = self.d_to_p_up.shape[0]
            self.nbr_distance_columns = self.d_to_p_up.shape[1]
            return True
        except Exception as e:
            print(str(e))
            raise 

    def set_index(self, pressure, distances, dir):
        # determines index for each muscle with closest up and down curves matching the given pressure and distances
        # values for each muscle are stored in the up_curve_idx and down_curve_idx lists. 
        # the integer value indicates the previously loaded d_to_p curves with highest value less than the given pressure at the given distance
        # todo - the mantissa (fractional part) indicates the ratio of the distance to the difference between the surrounding d_to_p values
        if dir == "up":
            # find distances in each curve closed to the given pressure 
            distances_in_curves = (np.abs( self.d_to_p_up - pressure)).argmin(axis=1)
            # now find the curve with the given distance closest to the value returned above
            self.up_curve_idx = []
            for i in range(6):
                self.up_curve_idx.append((np.abs(distances_in_curves - distances[i])).argmin(axis=0))
        elif dir == "down":
            distances_in_curves = (np.abs( self.d_to_p_down - pressure)).argmin(axis=1)
            # find the curve with the given distance closest to the value returned above
            self.down_curve_idx = []
            for i in range(6):
                self.down_curve_idx.append((np.abs(distances_in_curves - distances[i])).argmin(axis=0))
        else:
            print("invalid direction in set_index")

    def distance_to_pressure(self, distances):
        pressures = []
        for i in range(6):
            # todo check if we need to ignore case where distance does not change
            try: 
                if distances[i] >= self.nbr_distance_columns:
                    distances[i] = self.nbr_distance_columns-1
                if distances[i] <= self.prev_distances[i]: # moving down
                    index = self.down_curve_idx[i] 
                    curves = self.d_to_p_down
                else:
                    index = self.up_curve_idx[i]
                    curves = self.d_to_p_up
                p = self.interpolate(index, distances[i], curves) 
                pressures.append(p)
            except Exception as e:
                print("error in distance_to_pressure", e, traceback.format_exc())
                print("-> Has 'output\DtoP.csv' been loaded?")

        # print pressures
        self.prev_distances = distances
        return pressures

    def interpolate(self, index, distance, curves):
        # return the pressure for the given distance interpolated by the index value
        if index < self.rows:
            distance = int(distance)
            if index == int(index) or index >= self.rows -1:
                return curves[int(index)][distance]
            else:
                frac = index - int(index)
                #  print("idx=", index, "frac", frac, "dist", distance)
                delta = curves[int(index+1)][distance]*1.0 -  curves[int(index)][distance]
                d = curves[int(index)][distance]*1.0  + delta * frac 
                return d
        else:
            log.error("dist to pressure index value out of range")

if __name__ == "__main__":
    import logging
    log = logging.getLogger(__name__)
    logging.basicConfig(format='%(message)s', datefmt='%H:%M:%S')

    d_to_p = D_to_P(200)
    curves = [[1,2,3,4,5],[6,7,8,9,10], [11,12,13,14,15],  [21,22,23,24,25]]
    d_to_p.rows = len(curves)
    print(d_to_p.interpolate(0.9, 1, curves))
      
