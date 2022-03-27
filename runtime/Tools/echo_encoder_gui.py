import sys
import socket
import logging
import traceback
import time

log = logging.getLogger(__name__)

from common.encoders import EncoderClient
from echo_handler_gui_defs import *

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.app = app
        self.MAX_ACTUATOR_RANGE = 200
        self.encoders = None 
        self.init_echo_socket()
        self.init_gui()

    def init_echo_socket(self):
        self.echo_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.echo_sock.settimeout(.01)
        port = int(self.ui.txt_echo_port.text())
        self.echo_sock.bind(('',port ))
        # host_name = socket.gethostname() 
        #  host_ip = socket.gethostbyname(host_name) 

    def init_gui(self):
        self.actuator_bars = [self.ui.muscle_0,self.ui.muscle_1,self.ui.muscle_2,self.ui.muscle_3,self.ui.muscle_4,self.ui.muscle_5]
        self.txt_muscles = [self.ui.txt_muscle_0,self.ui.txt_muscle_1,self.ui.txt_muscle_2,self.ui.txt_muscle_3,self.ui.txt_muscle_4,self.ui.txt_muscle_5]
        self.txt_xforms = [self.ui.txt_xform_0,self.ui.txt_xform_1,self.ui.txt_xform_2,self.ui.txt_xform_3,self.ui.txt_xform_4,self.ui.txt_xform_5]
        self.encoder_bars = [self.ui.encoder_0,self.ui.encoder_1,self.ui.encoder_2,self.ui.encoder_3,self.ui.encoder_4,self.ui.encoder_5]
        self.txt_encoder_vals = [self.ui.txt_enc_0,self.ui.txt_enc_1,self.ui.txt_enc_2,self.ui.txt_enc_3,self.ui.txt_enc_4,self.ui.txt_enc_5]
        self.front_pixmap = QtGui.QPixmap('images/front.png')
        self.side_pixmap = QtGui.QPixmap('images/side.png')
        self.top_pixmap = QtGui.QPixmap('images/top.png')
        self.front_pos =  self.ui.lbl_front_view.pos()
        self.side_pos = self.ui.lbl_side_view.pos()
        self.top_pos = self.ui.lbl_top_view.pos()
        self.ui.btn_reset_encoders.clicked.connect(self.encoder_reset)
        self.ui.chk_echo_connect.stateChanged.connect(self.echo_connect_state_changed)
        self.ui.chk_encoder_connect.stateChanged.connect(self.encoder_connect_state_changed)
        for t in self.txt_muscles:
             t.setText('?')

    def echo_connect_state_changed(self):
        print "ech"

    def encoder_connect_state_changed(self):
        if self.ui.chk_encoder_connect.isChecked():
            encoder_ip = str(self.ui.txt_encoder_ip.text())
            self.encoders = EncoderClient(encoder_ip)
            self.encoders.connect()
        else:
            self.encoders.disconnect()

    def encoder_reset(self):
        if self.encoders:
            self.encoders.reset()

    def do_transform(self, widget, pixmap, pos,  x, y, angle):
        widget.move(x + pos.x(), y + pos.y())
        xform = QtGui.QTransform().rotate(angle)  # front view: roll
        xformed_pixmap = pixmap.transformed(xform, QtCore.Qt.SmoothTransformation)
        widget.setPixmap(xformed_pixmap)
        # widget.adjustSize()

    def show_transform(self, transform):
        for idx, x in enumerate(transform):
            if idx < 3:
                self.txt_xforms[idx].setText(format("%d" % x))
            else:
                angle = x * 57.3
                self.txt_xforms[idx].setText(format("%0.1f" % angle))
            
        x = int(transform[0] / 4) 
        y = int(transform[1] / 4)
        z = -int(transform[2] / 4)

        self.do_transform(self.ui.lbl_front_view, self.front_pixmap, self.front_pos, y,z, transform[3] * 57.3) # front view: roll
        self.do_transform(self.ui.lbl_side_view, self.side_pixmap, self.side_pos, x,z, transform[4] * 57.3) # side view: pitch
        self.do_transform(self.ui.lbl_top_view, self.top_pixmap, self.top_pos,  y,x, transform[5] * 57.3)  # top view: yaw

    def show_muscles(self, transform, muscles):
        for i in range(6):
           rect =  self.actuator_bars[i].rect()
           width = muscles[i] 
           rect.setWidth(width)
           self.actuator_bars[i].setFrameRect(rect)
           contraction = self.MAX_ACTUATOR_RANGE - width
           self.txt_muscles[i].setText(format("%d mm" % contraction ))
        self.show_transform(transform) 

    def show_encoders(self, distances):
        for i in range(6):
            self.txt_encoder_vals[i].setText(str(distances[i]))
            rect =  self.encoder_bars[i].rect()
            width = distances[i] 
            rect.setWidth(width)
            self.encoder_bars[i].setFrameRect(rect)

    def fields_to_list(self, fields):
        field = fields.split('=')
        data = field[1].strip('[]')
        d1 =  ','.join(data.split())
        d2 = d1.split(',')
        return [float(f) for f in d2]

    def receive(self):
        while True:
            try:
                if self.ui.chk_echo_connect.isChecked(): 
                    data, addr = self.echo_sock.recvfrom(1024) # buffer size is 1024 bytes
                    data = data.split(';')
                    transform = self.fields_to_list(data[0])
                    distance =  self.fields_to_list(data[1])
                    percent = self.fields_to_list(data[2])
                    self.show_muscles(transform, distance)
                if self.ui.chk_encoder_connect.isChecked() and self.encoders:
                    data =  self.encoders.read()
                    if data:
                        #  print data
                        self.show_encoders(data)
                self.app.processEvents()
            except socket.timeout:
                self.app.processEvents()
                continue
            except Exception as e:
                log.error("echo gateway error: %s,%s", e, traceback.format_exc())

def main():
    log.info("starting echo handler")
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow(app)
    win.show()
    win.receive()
    app.exec_() #mm added underscore

    log.info("Finishing echo handler\n")
    win.close()
    app.exit()
    sys.exit()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%H:%M:%S')
    main()
