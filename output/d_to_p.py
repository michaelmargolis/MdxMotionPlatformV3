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
import numpy as np

NBR_DISTANCES = 200 # 0-199mm with precision of 1mm

class D_to_P(object):

    def __init__(self, nbr_columns):
       self.nbr_columns = nbr_columns 
       assert (nbr_columns == NBR_DISTANCES), format("Expected %d distance values!" % NBR_DISTANCES)
       self.d_to_p_up = None  # up-going distance to pressure curves
       self.d_to_p_down = None
       self.up_curve_idx = None # index of the up-going curve closest to the current load
       self.down_curve_idx = None
       self.rows = 0 # number of load values in the DtoP file

    def load(self, fname = 'output\DtoP.csv'):
        # initializes d_to_p arrays from data in the given file
        try:
            d_to_p = np.loadtxt(fname, delimiter=',', dtype=int)
            assert(d_to_p.shape[1] == self.nbr_columns), format("expected %d columns, found %d\n", (self.nbr_columns, d_to_p.shape[1]))
            self.d_to_p_up, self.d_to_p_down =  np.split(d_to_p,2)
            assert(self.d_to_p_up.shape[0] == self.d_to_p_down.shape[0]), "up and down DtoP rows don't match"
            self.rows = self.d_to_p_up.shape[0]
            return True
        except Exception as e:
            print(str(e))
            raise 

    def set_index(self, pressure, distances, dir):
        # sets index to the curve closest to the given pressure and distances
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


