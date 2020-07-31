"""
client_select_dialog.python

This module provides a GUI for the platform_controller to select a sim
The selected information is sent by the platform_controler to a startup server
running on the PCs hosting the sim and Rift

Fixme - perhaps simplify by having same local and remote clients irrespective of number of users
"""

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt

from collections import namedtuple


Client = namedtuple('Client',
                        ['sim_name', # key used by remote PC startup to lookup executable file path to run
                         # the following are lists: [value for single PC, value for multiple PCs]
                        'local_client_itf', # python interface to execute on PC running sim
                        'remote_client']) # python client to be imported and used by platform controller

clients = []
clients.append(Client('Space_Coaster', ['clients/SpaceCoaster/space_coaster', 'clients/SpaceCoaster/space_coaster'],
                                       [ 'clients.remote_client.remote_client', 'clients.remote_client.remote_client']))
clients.append(Client('NoLimits_Coaster', ['NONE', 'todo'], ['clients.coaster.coaster_client', 'clients.remote_client.remote_client']))
clients.append(Client('Test_Client', ['NONE', 'NONE'],[ 'clients.test_client.simple_input', '']))

client_rb = []

class ClientSelect(QDialog):
    def __init__(self, parent, pc_addresses):
        try:
            super().__init__(parent)
        except:
            super(QDialog, self).__init__(parent) 
        self._pc_addresses = pc_addresses

        self.setObjectName("ClientSelect")
        self.resize(485, 454)
        self.setModal(True)
        self.init_fonts()
        self.setWindowTitle("Select Experience")

        self.gb_clients = QtWidgets.QGroupBox(self)
        self.gb_clients.setGeometry(QtCore.QRect(30, 20, 421, 231))
        self.gb_clients.setFont(self.font14)
        self.gb_clients.setTitle("Experience")
 
        self.rb_client_0 = QtWidgets.QRadioButton(self.gb_clients)
        self.rb_client_0.setGeometry(QtCore.QRect(30, 40, 361, 32))
        self.rb_client_0.setFont(self.font20)
        self.rb_client_0.setChecked(True)
        self.rb_client_0.setText("Space Coaster")
        client_rb.append(self.rb_client_0)
        
        self.rb_client_1 = QtWidgets.QRadioButton(self.gb_clients)
        self.rb_client_1.setGeometry(QtCore.QRect(30, 100, 381, 32))
        self.rb_client_1.setFont(self.font20)
        self.rb_client_1.setText("NoLimits Coaster")
        client_rb.append(self.rb_client_1)

        self.rb_client_2 = QtWidgets.QRadioButton(self.gb_clients)
        self.rb_client_2.setGeometry(QtCore.QRect(30, 160, 82, 32))
        self.rb_client_2.setFont(self.font20)
        self.rb_client_2.setText("Test")
        client_rb.append(self.rb_client_2)

        self.btn_continue = QtWidgets.QPushButton(self)
        self.btn_continue.setGeometry(QtCore.QRect(170, 400, 101, 31))
        self.btn_continue.setFont(self.font12)
        self.btn_continue.setText("Continue")
        self.btn_continue.clicked.connect(self.proceed)

        self.gb_sim_pcs = QtWidgets.QGroupBox(self)
        self.gb_sim_pcs.setGeometry(QtCore.QRect(30, 270, 421, 81))
        self.gb_sim_pcs.setFont(self.font14)
        self.gb_sim_pcs.setTitle("Sim Pcs")

        self.chk_pc_0 = QtWidgets.QCheckBox(self.gb_sim_pcs)
        self.chk_pc_0.setGeometry(QtCore.QRect(50, 40, 70, 17))
        
        self.ip_addr_0 = QtWidgets.QLineEdit(self.gb_sim_pcs)
        self.ip_addr_0.setGeometry(QtCore.QRect(80, 30, 121, 31))
        self.ip_addr_0.setFont(self.font12)

        self.chk_pc_1 = QtWidgets.QCheckBox(self.gb_sim_pcs)
        self.chk_pc_1.setGeometry(QtCore.QRect(250, 40, 70, 17))

        self.ip_addr_1 = QtWidgets.QLineEdit(self.gb_sim_pcs)
        self.ip_addr_1.setGeometry(QtCore.QRect(280, 30, 121, 31))
        self.ip_addr_1.setFont(self.font12)
        
        self.lbl_info = QtWidgets.QLabel(self)
        self.lbl_info.setGeometry(QtCore.QRect(30, 360, 411, 20))
        self.lbl_info.setFont(self.font12)
        self.lbl_info.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_info.setText("To change IP address, edit file platform_config.py ")

        self.init_addresses()

    def init_fonts(self):
        self.font12 = QtGui.QFont()
        self.font12.setPointSize(12)
        self.font14 = QtGui.QFont()
        self.font14.setPointSize(14)
        self.font20 = QtGui.QFont()
        self.font20.setPointSize(20)

    def init_addresses(self):
        assert(len(self._pc_addresses) > 0)
        self.ip_addr_0.setText(self._pc_addresses[0])
        self.chk_pc_0.setChecked(True)
        if len(self._pc_addresses) > 1:
            self.ip_addr_1.setText(self._pc_addresses[1])
            self.chk_pc_1.setChecked(True)

    @property
    def pc_addresses(self):
        addresses = []
        if self.chk_pc_0.isChecked(): addresses.append(self._pc_addresses[0])
        if self.chk_pc_1.isChecked(): addresses.append(self._pc_addresses[1])
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
        for idx, client in enumerate(client_rb):
            if client.isChecked():
                self._client_index = idx
                break

        if self.pc_addresses:
            if len(self.pc_addresses) > 1:
                multi_idx = 1
            else:
                multi_idx = 0
        else:
            print("No PC selected")
            self.lbl_info.setText("You must select at least one PC")
            return
            
        client = clients[self.client_index]
        self._client_name =  client.sim_name
        self._local_client_itf = client.local_client_itf[multi_idx]
        self._remote_client = client.remote_client[multi_idx] 
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