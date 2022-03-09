"""
D_to_P_prep.py  Distance to Pressure prep routines

The module comprises routines to create the distance to pressure files 

    To use this functionality,raw data files are created by stepping the platform through the range of pressures (0-6 bar) and
    capturing the encoder distance readings over three or more cycles
    The pressure step size can be anything from 100mb to 500 millibar, somewhere between 200mb to 400mb is probably the sweat spot.
    munge_file(fname) is the method to validate this file, see the comments below for info on the expected file format
        munge_file returns up and down arrays of pressure to distance. These are passed to the method named  process_p_to_d described below

    process_p_to_d(up,down, weight, pressure_step)  uses the munged data to create tables to convert desired distance to pressure that can 
         be stored in a file suitable for runtime load_DtoP method
    
    See the test method at the end of this file for an example of the file handling process
"""
import os
import numpy as np
from scipy import interpolate

# following imports only needed to produce plots to evaluate the data
import matplotlib.pyplot as plt
from matplotlib.legend import Legend
try:
    import seaborn as sns
except:
    print("seaborn package not found, using default plot style")

NBR_DISTANCES = 200 # 0-199mm with precision of 1mm

class D_to_P_prep(object):

    def __init__(self, nbr_columns):
       self.nbr_columns = nbr_columns 
       assert (nbr_columns == NBR_DISTANCES), format("Expected %d distance values!" % NBR_DISTANCES)
       self.is_V3_chair = False  # set to true if reading files in V3 chair format

    def munge_file(self, fname):
        # Call with filename of encoder readings of stepped pressures at a given load
        # returns numpy up and down arrays of averaged pressure to distance readings for this load
        # header consists of: weight, nbr steps, step size, nbr cycles, 
        # column data from row 7 consists of: cycle, dir, step, six encoder readings (remaining columns not used here)

        if os.path.isfile(fname): 
            header = np.loadtxt(fname, delimiter=',',dtype=int, usecols=1, max_rows=4)
        else:
            print("unable to open file:", fname)
            return None, None, None, None
        weight = header[0]
        steps_per_dir =  header[1] + 1  #add one as placeholder for zero pressure
        self.step_size =  header[2]
        self.nbr_cycles = header[3]
   
        nbr_rows = (steps_per_dir * 2) * self.nbr_cycles
        nbr_columns = 6 # six actuators
        print(format("weight=%d, steps per dir=%d, nbr cycles=%d, data rows=%d\n" % (weight, steps_per_dir, self.nbr_cycles, nbr_rows)))
        if self.is_V3_chair:
            #chair file data starts from column 1
            data = np.loadtxt(fname, delimiter=',', dtype=int, usecols= (1,2,3,4,5,6), skiprows=6, max_rows=nbr_rows)
        else:
            data = np.loadtxt(fname, delimiter=',', dtype=int, usecols= (4,5,6,7,8,9), skiprows=6, max_rows=nbr_rows)
        np_array = data.reshape(self.nbr_cycles*2, steps_per_dir, nbr_columns)
        print(np_array)
        # separate up and down arrays will be used to process the data
        up = np.empty([self.nbr_cycles,steps_per_dir, nbr_columns])
        down = np.empty([self.nbr_cycles,steps_per_dir,nbr_columns])
        for i in range (self.nbr_cycles) :
            up[i] = np_array[i*2][:,0:nbr_columns] 
            # print "up:", up[i]
            down[i] = np.flipud(np_array[(i*2)+1][:,0:nbr_columns]) 
            # print "down:", down[i]
        print("up", up)
        print("down", down)
        return  up, down, weight, self.step_size


    def process_p_to_d(self, up, down, weight, pressure_step):
        # call with arrays of up and down pressure to distance values
        # returns array of distance to pressure values, row 0 is up, row 1 is down
        updevs = []  # stores standard deviations
        downdevs = []
        first_cycle = 1 # set to 1 to skip first cycle
        for a in range(6): # actuators
            updevs += [np.max(np.max(np.std(up[ first_cycle:,:,a], axis=0)))]
            downdevs += [np.max(np.max(np.std(down[ first_cycle:,:,a], axis=0)))]
        devs = [max(u,d) for u,d in zip(updevs, downdevs)]
        best_index  =  devs.index(min(devs))
        print("best index is", best_index, ", up std dev = ", updevs[best_index], "down=", downdevs[best_index])
        avg_up = np.median(up[first_cycle:,:,best_index], axis=0)
        avg_down = np.median(down[first_cycle:,:,best_index], axis=0)
        self.show_charts( up, down, weight, ["Combined", "Individual", "Std Dev"])

        up_d_to_p = self.create_distance_to_pressure_array(avg_up, pressure_step)
        down_d_to_p = self.create_distance_to_pressure_array(avg_down, pressure_step)
        return  np.vstack((up_d_to_p, down_d_to_p))


    def show_charts(self, up, down, weight, charts_to_show):
        # displays charts of up and down data
        # charts_to_show argument contains strings identifying the chart(s) to display
        # todo linestyles = ['-', '--', '-.', ':', (1,8)] # for charts
        linestyles = ['-', '--', '-.', ':','-'] # for charts
        plt.style.use('fivethirtyeight')
        plt.rcParams['figure.figsize'] = (11, 8)
        try:
            sns.set() # use seaborn style charts
        except:
            print("seaborn package not found, using default plot style")

        up_lbl = []
        down_lbl= []
        for c in range(self.nbr_cycles):
            up_lbl += ["Up cycle " + str(c)]
            down_lbl += ["Down cycle " + str(c)]

        if "Individual" in charts_to_show:
            # show each actuator on separate chart
            fig, axs = plt.subplots(3, 2)
            for a in range(6): # actuators
                up_lines = []
                down_lines = []
                for c in range(self.nbr_cycles):                     
                    up_lines += axs[a//2, a%2,].plot(up[c][:,a], linestyle=linestyles[c], color='r')
                    down_lines += axs[a//2, a%2,].plot(down[c][:,a], linestyle=linestyles[c], color='b')

                up_lines +=  axs[a//2, a%2,].plot(np.mean(up[:,:,a], axis=0), color='c')
                up_lines +=  axs[a//2, a%2,].plot(np.median(up[:,:,a], axis=0), color='black')
                down_lines +=  axs[a//2, a%2,].plot(np.mean(down[:,:,a], axis=0), color='g')
                down_lines +=  axs[a//2, a%2,].plot(np.median(down[:,:,a], axis=0), color='black')
                axs[a//2, a%2].set_title('Actuator ' + str(a))
                axs[a//2, a%2,].legend(up_lines, up_lbl +['Up mean', 'Up median'], loc='upper left', frameon=False)
                down_lgnd = Legend(axs[a//2, a%2,], down_lines, down_lbl+['Down mean', 'Down median'],  loc='lower right', frameon=False)
                axs[a//2, a%2,].add_artist(down_lgnd)


            xtick = self.step_size/10
            for ax in axs.flat:
                ax.set(xlabel='Pressure', ylabel='Distance in mm')
                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, pos: format(int(10*x*xtick))))

            # Hide x labels and tick labels for top plots and y ticks for right plots.
            for ax in axs.flat:
                ax.label_outer()
            title = format("Individual Actuator Up and Down readings at %d kg" % (weight))     
            fig.suptitle(title, fontsize=16)
            plt.show()
            
        if "Combined" in charts_to_show:
            # show all actuators on same chart
            fig, ax = plt.subplots()
            title = format("All actuator Up and Down readings at %d kg" % (weight)) 
            ylabel = "Distance in mm"
            up_lines = []
            down_lines = []

            for c in range(self.nbr_cycles):
                for a in range(6): # actuators
                    if a == 0:
                        up_lines += ax.plot(up[c][:,a], linestyle=linestyles[c], color='r' )
                        down_lines +=  ax.plot(down[c][:,a], linestyle=linestyles[c], color='b' )
                    else:
                        ax.plot(up[c], linestyle=linestyles[c], color='r' )
                        ax.plot(down[c], linestyle=linestyles[c], color='b' )

            ax.legend(up_lines, up_lbl, loc='upper left', frameon=False)
            down_lgnd = Legend(ax, down_lines, down_lbl,  loc='lower right', frameon=False)
            ax.add_artist(down_lgnd);

            xtick = self.step_size/10
            ax.set(xlabel='Pressure', ylabel='Distance in mm')
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, pos: format(int(10*x*xtick))))
            
            fig.suptitle(title, fontsize=16)

            plt.show()
            #plt.save_figures(title )

        if "Std Dev" in charts_to_show:   
            # show standard deviation of readings across repeated cycles
            fig, axs = plt.subplots(3, 2, sharey=True )
            for a in range(6): # actuators
                up_lines = []
                down_lines = []
                axs[a//2, a%2,].plot(np.std(up[:,:,a], axis=0), color='r')
                axs[a//2, a%2,].plot(np.std(down[:,:,a], axis=0), color='b')
                axs[a//2, a%2].set_title('Actuator ' + str(a))

            xtick = self.step_size/10
            for ax in axs.flat:
                ax.set(xlabel='Pressure', ylabel='Std Deviation')
                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, pos: format(int(10*x*xtick))))

            # Hide x labels and tick labels for top plots and y ticks for right plots.
            for ax in axs.flat:
                ax.label_outer()
            title = format("Std deviation of Actuator up and down readings at %d kg" % weight)
            fig.suptitle(title, fontsize=16)
            plt.show()

    def create_distance_to_pressure_array(self, p_to_d, pressure_step):
    # call with array of distances for all pressure steps 
    # pressures range is hard coded from 0 to 6000 millibars
    # returns lookup table with pressures for the range of distances
        min = int(np.amin(p_to_d, axis=0))
        max = int(round(np.amax(p_to_d, axis=0)))
        # create stepped array of pressures
        pressures = np.arange(0, p_to_d.size*pressure_step, pressure_step)

        x = pressures 
        y = p_to_d # distances
        """
        # uncomment to show distance to pressure curve
        plt.xlabel("Pressure")
        plt.ylabel("Distance")
        plt.plot(x,y) 
        plt.show()
        """
        interp_func = interpolate.interp1d(x, y,kind = 'cubic') # distance from pressure
        dist_at_each_p = np.empty([6001], dtype=float)
        for i in range(6001):
            dist_at_each_p[i] = interp_func(i)
        d_to_p  = np.empty([NBR_DISTANCES], dtype=int)

        for i in range(NBR_DISTANCES):
           # get index with closest distance
           d_to_p[i] = (np.abs(dist_at_each_p - (min+i))).argmin() 
        return d_to_p 

    def merge_d_to_p(self, infnames, outfname):
        # creates distance to pressure curves file using values from infiles
        # input file format:
        # header as:  weight=X  where X is weight in kg
        # row 1:  comma separated list of 200 up-going pressures for mm distances from 0 to 199
        # row 2:  comma separated list of 200 down-going pressures for mm distances from 0 to 199
        weights = []
        up_d_to_p = []
        down_d_to_p = []
        for fname in infnames:
            with open(fname) as fp:
                header = fp.readline()  
                if 'weight=' in header:
                    weights.append(int(header.split('=')[1]))
                    up = fp.readline()
                    values = [int(round(float(i))) for i in up.split(',')]
                    up_d_to_p.append(values)
                    down = fp.readline()
                    values = [int(round(float(i))) for i in down.split(',')]
                    down_d_to_p.append(values)

        if len(weights) > 0:
            header = '# weights,' +  ','.join(str(n) for n in weights)
            combined_d_to_p= []
            for i in range (len(weights)):
                combined_d_to_p.append(up_d_to_p[i])
            for i in range (len(weights)):
                combined_d_to_p.append(down_d_to_p[i])
            with open(outfname, "w") as fp:
                fp.write(header + '\n')
                for i in range (len(weights)*2):  # write up then down
                    fp.write( ','.join(str(n) for n in combined_d_to_p[i] ) + '\n')
        else:
           print("no valid d to p files found")

def test():
     # test harness using PtoD_40.csv, PtoD_80.csv as inputs, DtoP_40.csv, DtoP_80.csv interim outputs
    dp =  D_to_P(200)  # instantiate the D_to_P class for 200 distance values (0-199mm)
    dp.is_V3_chair = True
    if dp.is_V3_chair:
        name_fragments = ['0.csv','1.csv','2.csv','3.csv','4.csv' ] # for V3 chair data
        name_prefix = 'weight'
    else:
        name_fragments = ['40.csv','80.csv'] # weight file strings concatenated to input and output fnames
        name_prefix = 'PtoD_'
    
    # read p_to_d files and convert and save as d_to_p files
    for frag in name_fragments:
        up,down, weight, pressure_step = dp.munge_file(name_prefix + frag)
        d_to_p = dp.process_p_to_d(up,down, weight, pressure_step)
        info = format("weight=%d" % weight)        
        np.savetxt('DtoP_' + frag, d_to_p, delimiter=',', fmt='%0.1f', header= info)
    # amalgamate individual d_to_p files into a single file
    infiles = []
    for frag in name_fragments:
        infiles.append('DtoP_' + frag)
    dp.merge_d_to_p(infiles, 'DtoP_test.csv')
    if dp.load_DtoP('DtoP_test.csv'):
        print(format("using %d Distance to Pressure curves" % dp.rows))
    # At this point the system has a set of up and down curves for a range of loads
    # Each time the platform load is changed,the runtime system should apply mid pressure (say 3 bar)
    # and call the d_to_p set_index method with the pressure and encoder readings to find the closest up curve
    # and then reduce the pressure to say 2 bar and call d_to_p set_index passing the pressure and encoder readings
    # to set the down-going index.

if __name__ == "__main__": 
   test()



