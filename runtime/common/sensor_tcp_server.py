import argparse
import select
import socket
import threading
import socketserver
import traceback
import signal

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

import logging
log = logging.getLogger(__name__)

class SensorServer(socketserver.ThreadingTCPServer, object):

    def __init__(self, server_address, request_handler_class, in_q):
        """Initialize the server and keep a set of registered clients."""
        super(SensorServer, self).__init__(server_address, request_handler_class, True)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        self.in_q = in_q
        self.create_listen_socket()
        #  self.mutex = threading.Lock()
        self.clients = set()

    def add_client(self, client):
        self.clients.add(client)
        log.info("adding client %s", client.name)

    def create_listen_socket(self): # for commands via UDP back channel
        listen_address = (self.server_address[0], self.server_address[1] + 1)
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.listen_sock.bind(listen_address)
        t = threading.Thread(target=self.listener_thread, args= (self.listen_sock, self.in_q))
        t.daemon = True
        log.debug("sensor server listening on port %d", listen_address[1])
        t.start()

    def listener_thread(self, listen_sock, in_q ):
        MAX_MSG_LEN = 256
        while True:
            try:
                msg, addr = listen_sock.recvfrom(MAX_MSG_LEN)
                #  print addr, msg
                msg = msg.rstrip()
                self.in_q.put((addr, msg))
            except Exception as e:
                print("back channel error", e)

    def broadcast(self, data):
        """Send data to all clients """
        for client in tuple(self.clients):
            client.schedule(data)

    def remove_client(self, client):
        log.info("removing client %s", client.name)
        try:
            self.clients.remove(client)
        except KeyError:
            pass  # client already removed?
        except Exception as e:
           raise

class CustomHandler(socketserver.BaseRequestHandler, object):

    """Forwards queued data to all registered clients."""

    def __init__(self, request, client_address, server):
        """Initialize the handler with a store for future date streams."""
        self.out_q = Queue()
        super(CustomHandler, self).__init__(request, client_address, server)

    def setup(self):
        """Register self with the set of server clients."""
        super(CustomHandler, self).setup()
        self.server.add_client(self)
        self.is_running = True

    def handle(self):
        """message pump to send queued data to all clients and check for input."""
        try:
            while self.is_running:
                self.service_queues()
            log.info("exiting handler for client %s", self.request.getpeername())
        except KeyError:
            pass
        except Exception as e:
            print("exception in custom handler: ", e)    #  (ConnectionResetError, EOFError):

    def service_queues(self):
        """Transfer outgoing sensor data to clients, print any incoming data."""
        while not self.out_q.empty():
            outgoing = self.out_q.get_nowait()
            if outgoing:
                self.request.sendall(outgoing)
        """
        if self.readable:
            incoming = self.request.recv(512)
            if incoming != '':
                # self.server.mutex.acquire() 
                self.server.in_q.put_nowait((self.name, incoming))
                # self.server.mutex.release()
            else:
                self.finish()
        """

    @property
    def readable(self):
        """Check if the client's connection can be read without blocking."""
        return self.request in select.select((self.request,), (), (), 0.001)[0]

    @property
    def name(self):
        """Get the client's address to which the server is connected."""
        return self.request.getpeername()

    def schedule(self, data):
        """Arrange for a data packet to be transmitted to the client."""
        self.out_q.put_nowait(data)

    def finish(self):
        """Remove the client's registration from the server before closing."""
        self.server.remove_client(self)
        self.is_running = False
        super(CustomHandler, self).finish()



def main():
    import time
    
    parser = argparse.ArgumentParser(description='Execute sensor server test.')
    parser.add_argument('port', type=int, help='port for server to listen on')
    # note: sends on port+1
    arguments = parser.parse_args()

    server_address = '', arguments.port
    signal.signal(signal.SIGINT, signal.SIG_DFL) # keyboard interrupt handler
    in_q = Queue()
    server = SensorServer(server_address, CustomHandler, in_q)
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    t.start()
    dummy_data = 0

    running = True
    while running:
        while not in_q.empty():
            name, data = in_q.get_nowait()
            if 'quit' in data:
                running = False
                break
            else:
                print "got cmd:", data
        data = str(time.clock())+ "\n"
        server.broadcast(data) # echo incoming to all clients 
        time.sleep(.01)
    print "exiting"
    server.shutdown()
    server.server_close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')
    main()