#!/usr/bin/env python
# coding=utf-8

"""
  local_startup.py
  This script is run at startup on the VR PCs to select and activate the runtime environment and ride
"""

from common.tcp_server import TcpServer
from platform_config import cfg
import time
import os
import threading
from subprocess import Popen

import logging
log = logging.getLogger(__name__)

# each option comprises display followed by a colon and sim path
sim_exe = {
            "Space_Coaster": 'M:/mdx/MdxPlatformInstall/SpaceCoaster/coasterMSU.exe',
            "NoLimits_Coaster": 'D:/Program Files/NoLimits 2/64bit/nolimits2app.exe --telemetry',
            "Test_Client": ''  # test client does not have a path
          }

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%H:%M:%S')
    server_address  = ('', cfg.STARTUP_SERVER_PORT)
    server = TcpServer(server_address)
    server.start()
    running = True
    log.info("Startup service at %s using TCP port %d", server.get_local_ip(), server_address[1])
    while running:
        while server.available():
            name, data = server.get()
            if 'quit' in data:
                running = False
                break
            else:
                log.info("got cmd: %s", data.strip())
                fields = data.strip().split(',')
                if fields[0] == 'STARTUP':
                    if fields[1] != 'NONE':
                        sim_path = sim_exe[fields[1]]
                        if sim_path :
                            log.info("starting sim :  %s", sim_path)
                            Popen(sim_path)
                    local_client = fields[2]
                    if local_client and local_client != "NONE": 
                        local_client = 'python ' + os. getcwd() + '/' + local_client + '.py'
                        log.info("starting local_client: %s", local_client)
                        Popen(local_client)
            # data = str(time.clock())+ "\n"
            server.broadcast(data)
        time.sleep(.1)
    print("exiting")
    server.finish()


"""
import win32file, msvcrt
import os, sys, time
import traceback
from subprocess import Popen

import logging
log = logging.getLogger(__name__)

runtime_path = 'D:/Dropbox/Mdx/MDXeMotionV3/'

infrastructure = []
infrastructure.append('common/encoders.py')

rides = {}
rides.update({'SpaceCoaster' : 'M:\mdx\MdxPlatformInstall\SpaceCoaster\coasterMSU.exe'})
rides.update({'NoLimits' : 'D:\Program Files\NoLimits 2\64bit\nolimits2app.exe' --telemetry})

clients = {}
clients.update({'SpaceCoaster' : "D:\Dropbox\Mdx\MDXeMotionV3\SpaceCoaster\space_coaster.py"})


def main():
    from common.kbhit  import KBHit
    logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')
    kb = KBHit()

    for prog in infrastructure:
        prog = runtime_path + prog
        log.info('starting %s', prog)
        try:
            pass # Popen('t.bat ' + prog)
        except Exception as e:
            print e,  traceback.format_exc()
            exit()
    target = 'SpaceCoaster'
    ride = rides.get(target)
    if ride:
        log.info('starting ride: %s', ride)
        try:
            Popen('t.bat ' + ride)
        except Exception as e:
            print e,  traceback.format_exc()
            exit()

    client = clients.get(target)
    if client:
        log.info('starting client: %s', client)
        try:
            Popen('t.bat ' + client)
        except Exception as e:
            print e,  traceback.format_exc()
            exit()


                
    else:
        log.error("ride: %s not recognized", target)
"""
if __name__ == '__main__':
    main() 