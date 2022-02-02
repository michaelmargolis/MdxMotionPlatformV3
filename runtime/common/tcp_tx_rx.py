import socket
import binascii
import logging

log = logging.getLogger(__name__)

class TcpTxRx():
    """
    non-threaded TCP client
    """

    def __init__(self, server_address = ('127.0.0.1', 15151), timeout = 0.5):
        self.tcp_address = server_address
        self.timeout = timeout
        self.sck = None
        self.is_connected = False

    def connect(self):
        log.debug('Attempting to connect to %s:%d', self.tcp_address[0], self.tcp_address[1])
        self.sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sck.settimeout(self.timeout)
        try:
            self.sck = socket.create_connection(self.tcp_address,1) # timeout after one second 
            self.is_connected = True
            log.debug('Connected to %s:%d',  self.tcp_address[0], self.tcp_address[1])
            return True
        except Exception as e:
            raise e
        return False

    def send(self, msg):
        if self.is_connected:
            try:
                # log.debug('Attempting to send %s', str(msg))
                self.sck.sendall(msg)
            except socket.error as error:
                if error.errno == socket.errno.WSAECONNRESET:
                    log.error("got disconnect error on connection to %s", self.ip_addr)
                elif error.errno == 10057:
                    log.warning("socket not connected, is target running")
                else:
                   log.error("error in client socket send")
        else:
            log.debug("unable to send because not connected ->%s ", msg)
   
    def receive(self, buffer_size=128):
        if self.sck is None:
            return None
        try:
            return self.sck.recv(buffer_size)
        except socket.timeout:
            log.warning("timeout in receive")
            print("timeout in receive")
        except socket.error as e: 
            log.error("socket error in thread %s", e)
            self.is_connected = False
        except Exception as e:
            log.error("unhandled listener thread err %s", e)

    def close(self):
        self.sck.close()
        print("connection closed")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(module)s: %(message)s',
                            datefmt='%H:%M:%S')
    log.info("Python: %s", sys.version[0:5])
    log.debug("logging using debug mode")
    
    nl2 = TcpTxRx()
    if nl2.connect():
        print("do tests here")
    else:
        print("error connecting")