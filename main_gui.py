# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main_gui.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(804, 476)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(0, 0, 801, 371))
        self.tabWidget.setStyleSheet("background-color: #f0f0f0")
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.frm_input = QtWidgets.QFrame(self.tab)
        self.frm_input.setGeometry(QtCore.QRect(4, 0, 791, 401))
        self.frm_input.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frm_input.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frm_input.setObjectName("frm_input")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.frm_dynamics = QtWidgets.QFrame(self.tab_2)
        self.frm_dynamics.setGeometry(QtCore.QRect(0, 0, 801, 411))
        self.frm_dynamics.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frm_dynamics.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frm_dynamics.setObjectName("frm_dynamics")
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.frm_output = QtWidgets.QFrame(self.tab_3)
        self.frm_output.setGeometry(QtCore.QRect(0, 0, 801, 351))
        self.frm_output.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frm_output.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frm_output.setObjectName("frm_output")
        self.frm_output_2 = QtWidgets.QFrame(self.frm_output)
        self.frm_output_2.setGeometry(QtCore.QRect(0, 0, 801, 361))
        self.frm_output_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frm_output_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frm_output_2.setObjectName("frm_output_2")
        self.lbl_platform_2 = QtWidgets.QLabel(self.frm_output)
        self.lbl_platform_2.setGeometry(QtCore.QRect(402, 388, 241, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_platform_2.setFont(font)
        self.lbl_platform_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.lbl_platform_2.setObjectName("lbl_platform_2")
        self.tabWidget.addTab(self.tab_3, "")
        self.lbl_client = QtWidgets.QLabel(self.centralwidget)
        self.lbl_client.setGeometry(QtCore.QRect(50, 409, 251, 19))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_client.setFont(font)
        self.lbl_client.setObjectName("lbl_client")
        self.btn_exit = QtWidgets.QPushButton(self.centralwidget)
        self.btn_exit.setGeometry(QtCore.QRect(710, 412, 75, 23))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btn_exit.setFont(font)
        self.btn_exit.setObjectName("btn_exit")
        self.lbl_platform = QtWidgets.QLabel(self.centralwidget)
        self.lbl_platform.setGeometry(QtCore.QRect(370, 410, 241, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_platform.setFont(font)
        self.lbl_platform.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.lbl_platform.setObjectName("lbl_platform")
        self.frame_3 = QtWidgets.QFrame(self.centralwidget)
        self.frame_3.setGeometry(QtCore.QRect(7, 370, 791, 41))
        self.frame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_3.setObjectName("frame_3")
        self.btn_activate = QtWidgets.QPushButton(self.frame_3)
        self.btn_activate.setGeometry(QtCore.QRect(30, 10, 101, 23))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btn_activate.setFont(font)
        self.btn_activate.setObjectName("btn_activate")
        self.btn_deactivate = QtWidgets.QPushButton(self.frame_3)
        self.btn_deactivate.setGeometry(QtCore.QRect(180, 10, 101, 23))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btn_deactivate.setFont(font)
        self.btn_deactivate.setObjectName("btn_deactivate")
        self.lbl_festo_status = QtWidgets.QLabel(self.frame_3)
        self.lbl_festo_status.setGeometry(QtCore.QRect(480, 8, 291, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_festo_status.setFont(font)
        self.lbl_festo_status.setText("")
        self.lbl_festo_status.setObjectName("lbl_festo_status")
        self.chk_festo_wait = QtWidgets.QCheckBox(self.frame_3)
        self.chk_festo_wait.setGeometry(QtCore.QRect(318, 10, 161, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.chk_festo_wait.setFont(font)
        self.chk_festo_wait.setObjectName("chk_festo_wait")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 804, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Input"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Intensity"))
        self.lbl_platform_2.setText(_translate("MainWindow", "Platform"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("MainWindow", "Output"))
        self.lbl_client.setText(_translate("MainWindow", "Client"))
        self.btn_exit.setText(_translate("MainWindow", "Exit"))
        self.lbl_platform.setText(_translate("MainWindow", "Platform"))
        self.btn_activate.setText(_translate("MainWindow", "Activate"))
        self.btn_deactivate.setText(_translate("MainWindow", "Deactivated"))
        self.chk_festo_wait.setText(_translate("MainWindow", "Festo Msg Check"))

