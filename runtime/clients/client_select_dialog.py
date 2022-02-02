"""
client_select_dialog.python

This module provides a GUI for the platform_controller to select a sim
The selected information is sent by the platform_controler to a startup server
running on the PCs hosting the sim


"""

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt

from collections import namedtuple

import sys
sys.path.insert(0, 'clients')
from client_config import cfg, init_cfg

class ClientSelect(QDialog):
    def __init__(self, parent, pc_addresses):
        try:
            super().__init__(parent)
        except:
            super(QDialog, self).__init__(parent) 
        self._pc_addresses = pc_addresses

        self.setObjectName("ClientSelect")
        self.resize(485, 476)
        self.setModal(True)
        self.init_fonts()
        self.setWindowTitle("Select Experience")

        self.gb_clients = QtWidgets.QGroupBox(self)
        self.gb_clients.setGeometry(QtCore.QRect(20, 20, 421, 200))
        self.gb_clients.setFont(self.font14)
        # self.gb_clients.setTitle("Experience")
 
        self.client_rb = []
        self._client_index = 0
        init_cfg()
        y = 10
        inc = 50
        if len(cfg.clients) < 4: inc += 20
        for client in cfg.clients:
            rb = QtWidgets.QRadioButton(self.gb_clients)
            rb.setGeometry(QtCore.QRect(30, y, 361, 32))
            rb.setFont(self.font20)
            rb.setText(client.sim_name)
            rb.toggled.connect(self.toggle_radio_btn)
            self.client_rb.append(rb)
            y = y + inc
        self.client_rb[cfg.default].setChecked(True)

        self.gb_sim_pcs = QtWidgets.QGroupBox(self)
        self.gb_sim_pcs.setGeometry(QtCore.QRect(20, 240, 421, 130))
        self.gb_sim_pcs.setFont(self.font14)
        self.gb_sim_pcs.setTitle("Sim Pcs")

        self.chk_pc = []
        self.ip_addr = []

        self.lbl_info = QtWidgets.QLabel(self)
        self.lbl_info.setGeometry(QtCore.QRect(30, 385, 400, 20))
        self.lbl_info.setFont(self.font12)
        self.lbl_info.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_info.setText("To change IP address, edit file platform_config.py ")

        self.btn_continue = QtWidgets.QPushButton(self)
        self.btn_continue.setGeometry(QtCore.QRect(170, 420, 101, 31))
        self.btn_continue.setFont(self.font12)
        self.btn_continue.setText("Continue")
        self.btn_continue.clicked.connect(self.proceed)
        
        self.init_addresses()
        self.timer_start()

    def init_fonts(self):
        self.font12 = QtGui.QFont()
        self.font12.setPointSize(12)
        self.font14 = QtGui.QFont()
        self.font14.setPointSize(14)
        self.font20 = QtGui.QFont()
        self.font20.setPointSize(20)

    def init_addresses(self):
        # self._pc_addresses = ['192.168.0.1', '192.168.0.2','192.168.0.3','192.168.0.4','192.168.0.5','192.168.0.6']
        assert(len(self._pc_addresses) > 0 and len(self._pc_addresses) <= 6)
        for idx, ip_addr in enumerate(self._pc_addresses):
           x = 20 + (idx % 2) * (self.gb_sim_pcs.width()/2)
           y = 30 + (idx / 2) * 30
           self.chk_pc.append(QtWidgets.QCheckBox(self.gb_sim_pcs))
           self.chk_pc[-1].setGeometry(QtCore.QRect(x, y+7, 70, 17))
           self.chk_pc[-1].setChecked(True)
           self.ip_addr.append(QtWidgets.QLabel(self.gb_sim_pcs))
           self.ip_addr[-1].setGeometry(QtCore.QRect(x + 20, y, 121, 31))
           self.ip_addr[-1].setFont(self.font12)
           self.ip_addr[-1].setText(self._pc_addresses[idx])

    def timer_start(self):
        self.countdown = 10 # run default after 10 seconds
        self.my_qtimer = QtCore.QTimer(self)
        self.my_qtimer.timeout.connect(self.timer_timeout)
        self.my_qtimer.start(1000)

    def timer_timeout(self):
        self.countdown -= 1
        if self.countdown <= 5:
            info = format("%s will start in %d seconds" %  (self.client_name, self.countdown))
            self.lbl_info.setText(info)

        if self.countdown == 0:
            self.my_qtimer.stop()
            self.proceed()

    def toggle_radio_btn(self, value):
        rbtn = self.sender()
        if rbtn.isChecked() == True:
            self._client_name = rbtn.text()
            self._client_index = self.client_rb.index(rbtn)
            #  print "index=", self._client_index
            #  print self.client_name, cfg.clients[self._client_index].sim_name

    @property
    def pc_addresses(self):
        addresses = []
        for idx, widget in enumerate(self.chk_pc):
            if widget.isChecked(): addresses.append(str(self.ip_addr[idx].text()))
        if len(addresses ) == 0:
            return None
        else:
            return addresses

    @property
    def client_index(self):
        return self._client_index

    @property
    def client_name(self):
        return self._client_name

    @property
    def local_client_itf(self):
        return self._local_client_itf

    @property
    def remote_client(self):
        return self._remote_client
    
    def proceed(self):
        if self.pc_addresses:
            if len(self.pc_addresses) > 1:
                multi_idx = 1
            else:
                multi_idx = 0
        else:
            print("No PC selected")
            self.lbl_info.setText("You must select at least one PC")
            return
            
        client = cfg.clients[self.client_index]
        self._client_name =  client.sim_name
        self._local_client_itf = client.local_client_itf
        self._remote_client = client.remote_client
        self.accept()

if __name__ == "__main__":
    import sys
    from  platform_config import cfg
    
    app = QApplication(sys.argv)
    w = QWidget()
    
    dialog = ClientSelect(w, cfg.SIM_IP_ADDR)

    if dialog.exec_():
        print(format("pcs: %s running client %s" % (str(dialog.pc_addresses), dialog.client_name)))
        print(dialog.client_index, dialog.client_name, dialog.local_client_itf, dialog.remote_client)
    else:
        sys.exit()