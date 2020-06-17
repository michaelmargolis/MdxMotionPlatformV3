import csv
import time
import sys
import socket
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--filename', required=True, help='foo help')
parser.add_argument('--ip', required=True, help='foo help')
parser.add_argument('--port', type=int, required=True, help='foo help')

args = parser.parse_args()

def millis():
    return int(round(time.time() * 1000))

framerate = 25;
msPerFrame = 1000 / framerate;

sock =socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = (args.ip, args.port)
sock.connect(server_address)

with open(args.filename, 'rb') as csvfile:
    rows = csv.reader(csvfile, delimiter=',');
    rowcount = 0;

    msStart = millis() # we place this here, as it needs to go after the file read - and before the loop.
    for row in rows:
        rowcount = rowcount +1;
        while (msStart + (msPerFrame * rowcount) > millis()):
            # wait until the frame/time is correct
            pass
        message = ','.join(row)
        sock.sendall("xyzrpy,"+message)
        print( rowcount, message )
        if(rowcount >= 10000):
            print 'elapsed: ' + str( millis() - msStart);
            sock.close();
            sys.exit();
        
