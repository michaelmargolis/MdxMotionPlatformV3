import sys
import socket
import logging
import traceback

import easyip
from festo_emulator_gui_defs import *

log = logging.getLogger(__name__)

class MainWindow(QtGui.QMainWindow):
    def __init__(self, app):
        QtGui.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.app = app
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.sock.settimeout(1)
        self.sock.bind(('', easyip.EASYIP_PORT))
        host_name = socket.gethostname() 
        host_ip = socket.gethostbyname(host_name) 
        self.init_gui()
        log.info("Festo emulator running on %s", host_ip)


    def init_gui(self):
        self.pressure_bars = [self.ui.muscle_0,self.ui.muscle_1,self.ui.muscle_2,self.ui.muscle_3,self.ui.muscle_4,self.ui.muscle_5]
        self.txt_muscles = [self.ui.txt_muscle_0,self.ui.txt_muscle_1,self.ui.txt_muscle_2,self.ui.txt_muscle_3,self.ui.txt_muscle_4,self.ui.txt_muscle_5]
        for t in self.txt_muscles:
             t.setText('?')

    def show_pressures(self, pressures):
        if pressures == 0:
           self.show_disconnected()
        else:
            try:
                self.display_pressure_bars(pressures)
            except TypeError as e:
                print pressures, e

    def show_disconnected(self):
        self.display_pressure_bars((0,0,0,0,0,0))
        for t in self.txt_muscles:
            t.setText('?')
        self.ui.lbl_connection.setText("Not Connected")

    def display_pressure_bars(self, pressures):
        for idx, p in enumerate(pressures):
            self.txt_muscles[idx].setText(str(p))
            rect =  self.pressure_bars[idx].rect()
            width = pressures[idx] /20
            if width <= 0: width = 1
            rect.setWidth(width)
            self.pressure_bars[idx].setFrameRect(rect)

    def receive(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(1024) # buffer size is 1024 bytes
                # if 'quit" in data:
                #     sys.exit()
                resp = easyip.Packet(data)
                values = resp.decode_payload(easyip.Packet.DIRECTION_SEND)
                # log.info("received msg %s from %s", data, addr)
                self.show_pressures(values)
                self.ui.lbl_connection.setText("Connected to " + addr[0])
                self.send_response(resp, addr)
                self.app.processEvents()
            except socket.timeout:
                log.debug("festo emulator timeout")
                self.show_disconnected()
                self.app.processEvents()
                continue
            except Exception as e:
                log.error("festo emulator recv err: %s,%s", e, traceback.format_exc())

    def send_response(self, in_packet, addr):
         packet = easyip.Factory.response(in_packet,0) # send no error
         data = packet.pack()
         self.sock.sendto(data, addr)


def main():
    log.info("starting festo emulator")
    app = QtGui.QApplication(sys.argv)
    win = MainWindow(app)
    win.show()
    win.receive()
    app.exec_() #mm added underscore

    log.info("Finishing PlatformTest\n")
    win.close()
    app.exit()
    sys.exit()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%H:%M:%S')
    main()
