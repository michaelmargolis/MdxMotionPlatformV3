# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SpaceCoaster\remote_client_gui.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Frame(object):
    def setupUi(self, Frame):
        Frame.setObjectName("Frame")
        Frame.resize(800, 448)
        Frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        Frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frm_input = QtWidgets.QFrame(Frame)
        self.frm_input.setGeometry(QtCore.QRect(5, 4, 791, 351))
        self.frm_input.setStyleSheet("background-color: #f0f0f0")
        self.frm_input.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frm_input.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frm_input.setObjectName("frm_input")
        self.btn_dispatch = QtWidgets.QPushButton(self.frm_input)
        self.btn_dispatch.setGeometry(QtCore.QRect(210, 173, 111, 51))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.btn_dispatch.setFont(font)
        self.btn_dispatch.setStyleSheet("color:white;background-color: green;")
        self.btn_dispatch.setObjectName("btn_dispatch")
        self.btn_pause = QtWidgets.QPushButton(self.frm_input)
        self.btn_pause.setGeometry(QtCore.QRect(460, 173, 111, 51))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btn_pause.setFont(font)
        self.btn_pause.setStyleSheet("background-color: orange\n"
"")
        self.btn_pause.setObjectName("btn_pause")
        self.groupBox = QtWidgets.QGroupBox(self.frm_input)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 361, 131))
        self.groupBox.setObjectName("groupBox")
        self.lbl_coaster_status_1 = QtWidgets.QLabel(self.groupBox)
        self.lbl_coaster_status_1.setGeometry(QtCore.QRect(22, 30, 331, 21))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.lbl_coaster_status_1.setFont(font)
        self.lbl_coaster_status_1.setObjectName("lbl_coaster_status_1")
        self.lbl_coaster_connection_1 = QtWidgets.QLabel(self.groupBox)
        self.lbl_coaster_connection_1.setGeometry(QtCore.QRect(20, 65, 331, 19))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_coaster_connection_1.setFont(font)
        self.lbl_coaster_connection_1.setObjectName("lbl_coaster_connection_1")
        self.btn_reset_rift_1 = QtWidgets.QPushButton(self.groupBox)
        self.btn_reset_rift_1.setGeometry(QtCore.QRect(20, 100, 91, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btn_reset_rift_1.setFont(font)
        self.btn_reset_rift_1.setObjectName("btn_reset_rift_1")
        self.groupBox_3 = QtWidgets.QGroupBox(self.frm_input)
        self.groupBox_3.setGeometry(QtCore.QRect(10, 260, 761, 81))
        self.groupBox_3.setObjectName("groupBox_3")
        self.lbl_remote_status = QtWidgets.QLabel(self.groupBox_3)
        self.lbl_remote_status.setGeometry(QtCore.QRect(20, 50, 501, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_remote_status.setFont(font)
        self.lbl_remote_status.setObjectName("lbl_remote_status")
        self.lbl_intensity_status = QtWidgets.QLabel(self.groupBox_3)
        self.lbl_intensity_status.setGeometry(QtCore.QRect(20, 20, 341, 19))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_intensity_status.setFont(font)
        self.lbl_intensity_status.setObjectName("lbl_intensity_status")
        self.groupBox_4 = QtWidgets.QGroupBox(self.frm_input)
        self.groupBox_4.setGeometry(QtCore.QRect(410, 10, 361, 131))
        self.groupBox_4.setObjectName("groupBox_4")
        self.lbl_coaster_status_2 = QtWidgets.QLabel(self.groupBox_4)
        self.lbl_coaster_status_2.setGeometry(QtCore.QRect(22, 30, 331, 21))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.lbl_coaster_status_2.setFont(font)
        self.lbl_coaster_status_2.setObjectName("lbl_coaster_status_2")
        self.lbl_coaster_connection_2 = QtWidgets.QLabel(self.groupBox_4)
        self.lbl_coaster_connection_2.setGeometry(QtCore.QRect(20, 65, 331, 19))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_coaster_connection_2.setFont(font)
        self.lbl_coaster_connection_2.setObjectName("lbl_coaster_connection_2")
        self.btn_reset_rift_2 = QtWidgets.QPushButton(self.groupBox_4)
        self.btn_reset_rift_2.setGeometry(QtCore.QRect(20, 100, 91, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btn_reset_rift_2.setFont(font)
        self.btn_reset_rift_2.setObjectName("btn_reset_rift_2")

        self.retranslateUi(Frame)
        QtCore.QMetaObject.connectSlotsByName(Frame)

    def retranslateUi(self, Frame):
        _translate = QtCore.QCoreApplication.translate
        Frame.setWindowTitle(_translate("Frame", "Frame"))
        self.btn_dispatch.setText(_translate("Frame", "Dispatch"))
        self.btn_pause.setText(_translate("Frame", "Pause"))
        self.groupBox.setTitle(_translate("Frame", "Client 1"))
        self.lbl_coaster_status_1.setText(_translate("Frame", "Status"))
        self.lbl_coaster_connection_1.setText(_translate("Frame", "Connection"))
        self.btn_reset_rift_1.setText(_translate("Frame", "Reset Rift"))
        self.groupBox_3.setTitle(_translate("Frame", "System"))
        self.lbl_remote_status.setText(_translate("Frame", "Remote"))
        self.lbl_intensity_status.setText(_translate("Frame", "Intensity"))
        self.groupBox_4.setTitle(_translate("Frame", "Client 2"))
        self.lbl_coaster_status_2.setText(_translate("Frame", "Status"))
        self.lbl_coaster_connection_2.setText(_translate("Frame", "Connection"))
        self.btn_reset_rift_2.setText(_translate("Frame", "Reset Rift"))

