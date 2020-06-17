"""
local_client_itf listens on a tcp socket for client requests
control requests return client status
telemetry requests return current status and telemetry values
"""

import time
import sys
import tcp_server
from threading import Thread, Lock
from Queue import Queue
import traceback

import logging
log = logging.getLogger(__name__)


def cmd_func(cmd):
    print cmd
    
def move_func(value):
    print value

import logging.handlers
import logging as log

def start_logging(level):
    log_format = log.Formatter('%(asctime)s,%(levelname)s,%(message)s')
    logger = log.getLogger()
    logger.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler("local_client.log", maxBytes=(10240 * 5), backupCount=2)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    console_handler = log.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)   

def main():
    start_logging(log.INFO)
    queue = Queue()
    lock = Lock()
    server = tcp_server.SocketServer(port=10015, queue=queue, lock=lock)
    server.start()
    is_running = True
    while is_running:
        server.service()
        while queue.qsize() > 0:
            msg = queue.get()
            if 'quit' in msg:
                is_running = False
                break;            
            event = msg.split("\n")
            for e in event:
                print e
        time.sleep(.05)
    server.close()
    server.join()



# method for testing is called
if __name__ == "__main__":
    main()