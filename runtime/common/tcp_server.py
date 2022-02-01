"""
 tcp_server.py
 
 A threaded TCP server. See main method at bottom of this file for example usage
"""

import argparse
import select
import socket
import threading
import traceback
import signal

try:
    #  python 3.x
    from queue import Queue
    import socketserver as socketserver
except ImportError:
    #  python 2.7
    from Queue import Queue
    import SocketServer as socketserver

import logging
log = logging.getLogger(__name__)

class TcpServer(socketserver.ThreadingTCPServer, object):

    def __init__(self, server_address):
        """Initialize the server and keep a set of registered clients."""
        super(TcpServer, self).__init__(server_address, CustomHandler, True)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        self.in_q = Queue()
        #  self.mutex = threading.Lock()
        self.clients = set()

    def available(self):
        return self.in_q.qsize()
 
    def get(self):
        if self.available():
            return self.in_q.get_nowait()
        else:
            return None

    def send(self, address, data):
        #  address must be one of the connected clients
        for client in tuple(self.clients):
            if sender == client.name: # todo test this!
                client.schedule(data)
                break
            else:
                log.warning("No match for client address %s", address)

    def broadcast(self, data):
        """Send data to all clients """
        for client in tuple(self.clients):
            client.schedule(data)

    def start(self):
        t = threading.Thread(target=self.serve_forever)
        t.daemon = True
        t.start()

    def finish(self):
        for client in tuple(self.clients):
            client.finish()
            self._remove_client(client)
            
    def _add_client(self, client):
        self.clients.add(client)
        log.info("adding client %s", client.name)

    def _remove_client(self, client):
        log.info("removing client %s", client.name)
        try:
            self.clients.remove(client)
        except KeyError:
            pass  # client already removed?
        except Exception as e:
           raise

    def connected_clients(self):
        return len(self.clients)
        
    def get_local_ip(self):
        # returns primary ip address of this pc
        host_name = socket.gethostname() 
        host_ip = socket.gethostbyname(host_name) 
        return host_ip

class CustomHandler(socketserver.BaseRequestHandler, object):

    """Forwards queued data to all registered clients."""

    def __init__(self, request, client_address, server):
        """Initialize the handler with a store for future date streams."""
        self.out_q = Queue()
        self.in_buffer = ''
        super(CustomHandler, self).__init__(request, client_address, server)

    def setup(self):
        """Register self with the set of server clients."""
        super(CustomHandler, self).setup()
        self.server._add_client(self)
        self.is_running = True

    def handle(self):
        """message pump to send queued data to all clients and check for input."""
        try:
            while self.is_running:
                self.service_queues()
            log.info("exiting handler for client %s", self.request.getpeername())
        except KeyError:
            pass
        except Exception:
            log.info("client %s disconnected", self.request.getpeername() )
        except Exception as e:
            print("exception in custom handler: ", e)    #  (except Exception as e:, EOFError):

    def service_queues(self):
        """Transfer outgoing sensor data to clients, print any incoming data."""
        while not self.out_q.empty():
            outgoing = self.out_q.get_nowait()
            if outgoing:
                self.request.sendall(outgoing)

        if self.readable:
            incoming = self.request.recv(512).decode('utf-8')
            if incoming != '':
                self.in_buffer += incoming
                while True:
                    line, sep, self.in_buffer = self.in_buffer.partition('\n')
                    if len(line):
                        self.server.in_q.put_nowait((self.name, line))
                    else:
                        break
            else:
                self.finish()
 

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
        self.server._remove_client(self)
        self.is_running = False
        super(CustomHandler, self).finish()



def main():
    import time
    
    parser = argparse.ArgumentParser(description='TCP server test.')
    parser.add_argument('port', type=int, help='port for server to listen on')
    parser.add_argument("-l", "--log", dest="logLevel", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    # note: sends on port+1
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')
    if args.logLevel: log.setLevel(args.logLevel)
    server_address = '', args.port
    signal.signal(signal.SIGINT, signal.SIG_DFL) # keyboard interrupt handler
    server = TcpServer(server_address)
    server.start()
    dummy_data = 0

    running = True
    print("started tcp server on port " + str(server_address[1]))
    while running:
        while server.available():
            name, data = server.get()
            if 'quit' in data:
                running = False
                break
            else:
                log.debug("got cmd: %s", data)
            # data = str(time.clock())+ "\n"
            server.broadcast(data) # echo incoming to all clients 
        time.sleep(.01)
    print("exiting")
    server.finish()


if __name__ == '__main__':
    main()