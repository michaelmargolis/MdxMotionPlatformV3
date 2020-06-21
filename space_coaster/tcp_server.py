"""
tcp_server.py

"""

import sys
import socket
import select
import time
import threading
try:
    from queue import Queue
except ImportError:
    from queue import Queue 

import logging
log = logging.getLogger(__name__)

class SockServer(threading.Thread):
    def __init__(self, host = '', port = 10015,  max_clients=1, timeout=1):
        """ Initialize the server with host and port to listen to, input and output queues. """
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = host
        self.port = port
        self.max_clients = max_clients # how many simultaneous connections are allowed
        self.sock.bind((host, port))
        self.sock.listen(max_clients)
        self.sock.settimeout(timeout)
        self.in_queue = Queue()
        self.out_queue = Queue()
        self.lock = threading.Lock()
        self.nbr_clients = [0] # count of number of connected clients
        log.info('Starting socket server (host %s, port %d)', self.host, self.port)
        self.sock_threads = []

    def close(self):
        """ Close the client socket threads and server socket if they exists. """
        log.info('Closing server socket (host %s, port %d)', self.host, self.port)

        for thr in self.sock_threads:
            thr.stop()
            thr.join()

        if self.sock:
            self.sock.close()
            self.sock = None
            
    def connected_clients(self):
        return self.nbr_clients[0]
        
    def get_local_ip(self):
        # returns primary ip address of this pc
        host_name = socket.gethostname() 
        host_ip = socket.gethostbyname(host_name) 
        return host_ip
        # following not used
        try:
            # doesn't even have to be reachable
            self.sock.connect(('10.255.255.255', 1))
            IP = self.sock.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        log.info("IP address of this pc is %s", IP)
        return IP

    def send(self, msg):
        log.debug("sending: %s", msg)
        self.out_queue.put(msg)

    def available(self):
        return self.in_queue.qsize()
 
    def receive(self):
        if self.available():
            return self.in_queue.get()
        else:
            return None
    
    def service(self):
        # listen for incoming connection and start a new SockServerThread to handle the communication
        if self.nbr_clients[0] <  self.max_clients: 
            # here if we can accept a new connection
            try:
                client_sock, client_addr = self.sock.accept()
            except socket.timeout:
                client_sock = None

            if client_sock:
                self.nbr_clients[0] +=1
                client_thr = SockServerThread(client_sock, client_addr, self.in_queue, self.out_queue, self.lock, self.nbr_clients)
                self.sock_threads.append(client_thr)
                client_thr.start()

    def stop(self):
        self.close()

class SockServerThread(threading.Thread):
    def __init__(self, client_sock, client_addr, in_queue, out_queue, lock, nbr_clients):
        self.id = nbr_clients[0] # use client count as a convenient thread identifier
        threading.Thread.__init__(self)
        self.client_sock = client_sock
        self.client_addr = client_addr
        self.in_queue = in_queue # received data can be returned in this queue
        self.out_queue = out_queue # data to be sent can be written to this queue
        self.lock = lock
        self.nbr_clients = nbr_clients

    def run(self):
        log.info("Socket server thread %d starting with client %s", self.id, self.client_addr)
        self.__stop = False
        while not self.__stop:
            if self.client_sock:
                # Check if the client is still connected and if data is available:
                try:
                    rdy_read, rdy_write, sock_err = select.select([self.client_sock,], [self.client_sock,], [], 5)
                except select.error as err:
                    log.info('Thread %d Select() failed on socket with %s', self.id,self.client_addr)
                    self.stop()
                    return

                if len(rdy_read) > 0:
                    try:
                        read_data = self.client_sock.recv(255)
                        # Check if socket has been closed
                        if len(read_data) == 0:
                            log.info('thread %d closed the socket on %s.',  self.id, self.client_addr)
                            self.stop()
                        else:
                            try:
                                self.in_queue.put(read_data)
                            except:
                                log.debug("unable to append to tcp in_queue")
                            # Strip newlines just for output clarity
                            log.debug('thread %d Received %s',  self.id, read_data.rstrip())
                    except socket.error as error:
                        if error.errno == socket.errno.WSAECONNRESET:
                            log.error("got disconnect error on connection to %s", self.client_addr)
                            self.stop() 
                            
                while self.out_queue.qsize() > 0:
                    to_send = self.out_queue.get()
                    try:
                        self.client_sock.sendall(to_send)
                    except Exception as e:
                        log.error("error sending %s",e)
            else:
                log.error("thread %d: No client is connected, SocketServer can't receive data", self.id)
                self.stop()
        self.close()
        with self.lock:
            self.nbr_clients[0] -=1

    def stop(self):
        self.__stop = True

    def close(self):
        """ Close connection with the client socket. """
        if self.client_sock:
            log.info('thread %d Closing connection with %s', self.id, self.client_addr)
            self.client_sock.close()
            
###################  test code run from main ##################

def main():
    import msvcrt # for kbhit

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%H:%M:%S')

    server = SockServer(port=10015)
    server.start()
    is_running = True
    while is_running:
        server.service()
        #out_queue.append(time.asctime()+'\n')
        if server.available():
            try:
                msg = server.receive()
                if msg:
                    server.send(msg) # echo the message
            except Exception as e:
                log.error("Error reading server que %s", e)
        if msvcrt.kbhit():  
            if ord(msvcrt.getch()) == 27: # esc
                break
    server.close()
    server.join()
    print('End.')

    
if __name__ == "__main__":
    main()