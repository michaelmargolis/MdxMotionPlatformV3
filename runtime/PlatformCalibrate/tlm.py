# telemtry raw_script

# format is: xyzrpy,time in secs
# xyz are in mm, rpy degrees
# interpolates intermediate values and produces telemetry file


# from numpy import genfromtxt
import numpy as np
import sys

telemetry = []
frame_dur = .05

def interpolate(begin, end, count):
    #print "interp",  begin,end, count
    delta = (end-begin)/ count
    #print "delta", delta
    for i in range(count):
       telemetry.append( telemetry[-1] + delta)
    

def convert(fname):
    try:
        raw = np.genfromtxt(fname+".script", delimiter=',')
        print raw
        for  l in raw:
            xyzrpy = l[:6]
            xyzrpy = xyzrpy * [1,1,1,0.0174533,0.0174533,0.0174533]
            time = l[6]
            print xyzrpy, "t=", time
            if len(telemetry) == 0:
                while time >= 0:
                    telemetry.append(xyzrpy)
                    time -= frame_dur
            else:
                if time > frame_dur:
                    interpolate(telemetry[-1],xyzrpy, int(time / frame_dur))
                else:
                    telemetry.append(xyzrpy)
    except ValueError:
        print sys.exc_info()[1]

if __name__ == '__main__':
    convert("test")
    np.savetxt('test.tlm', telemetry, delimiter=',', fmt='%0.3f')

 