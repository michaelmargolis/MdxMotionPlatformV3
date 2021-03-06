# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '..\clients\remote_client\remote_client_gui.ui'
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
        self.btn_dispatch.setGeometry(QtCore.QRect(60, 183, 111, 51))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.btn_dispatch.setFont(font)
        self.btn_dispatch.setStyleSheet("color:white;background-color: green;")
        self.btn_dispatch.setObjectName("btn_dispatch")
        self.btn_pause = QtWidgets.QPushButton(self.frm_input)
        self.btn_pause.setGeometry(QtCore.QRect(250, 183, 111, 51))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btn_pause.setFont(font)
        self.btn_pause.setStyleSheet("background-color: orange\n"
"")
        self.btn_pause.setObjectName("btn_pause")
        self.groupBox_3 = QtWidgets.QGroupBox(self.frm_input)
        self.groupBox_3.setGeometry(QtCore.QRect(10, 260, 361, 81))
        self.groupBox_3.setObjectName("groupBox_3")
        self.lbl_remote_status = QtWidgets.QLabel(self.groupBox_3)
        self.lbl_remote_status.setGeometry(QtCore.QRect(20, 48, 311, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_remote_status.setFont(font)
        self.lbl_remote_status.setObjectName("lbl_remote_status")
        self.lbl_intensity_status = QtWidgets.QLabel(self.groupBox_3)
        self.lbl_intensity_status.setGeometry(QtCore.QRect(20, 26, 311, 19))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_intensity_status.setFont(font)
        self.lbl_intensity_status.setObjectName("lbl_intensity_status")
        self.lbl_item_select = QtWidgets.QLabel(self.frm_input)
        self.lbl_item_select.setGeometry(QtCore.QRect(710, 200, 101, 20))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_item_select.setFont(font)
        self.lbl_item_select.setObjectName("lbl_item_select")
        self.cmb_select_ride = QtWidgets.QComboBox(self.frm_input)
        self.cmb_select_ride.setGeometry(QtCore.QRect(420, 190, 271, 41))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.cmb_select_ride.setFont(font)
        self.cmb_select_ride.setObjectName("cmb_select_ride")
        self.lbl_coaster_status = QtWidgets.QLabel(self.frm_input)
        self.lbl_coaster_status.setGeometry(QtCore.QRect(20, 106, 711, 61))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.lbl_coaster_status.setFont(font)
        self.lbl_coaster_status.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_coaster_status.setObjectName("lbl_coaster_status")
        self.groupBox_5 = QtWidgets.QGroupBox(self.frm_input)
        self.groupBox_5.setGeometry(QtCore.QRect(410, 260, 361, 81))
        self.groupBox_5.setObjectName("groupBox_5")
        self.lbl_state_delta = QtWidgets.QLabel(self.groupBox_5)
        self.lbl_state_delta.setGeometry(QtCore.QRect(20, 48, 311, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_state_delta.setFont(font)
        self.lbl_state_delta.setObjectName("lbl_state_delta")
        self.lbl_frame_delta = QtWidgets.QLabel(self.groupBox_5)
        self.lbl_frame_delta.setGeometry(QtCore.QRect(20, 26, 311, 19))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_frame_delta.setFont(font)
        self.lbl_frame_delta.setObjectName("lbl_frame_delta")

        self.retranslateUi(Frame)
        QtCore.QMetaObject.connectSlotsByName(Frame)

    def retranslateUi(self, Frame):
        _translate = QtCore.QCoreApplication.translate
        Frame.setWindowTitle(_translate("Frame", "Frame"))
        self.btn_dispatch.setText(_translate("Frame", "Dispatch"))
        self.btn_pause.setText(_translate("Frame", "Pause"))
        self.groupBox_3.setTitle(_translate("Frame", "System"))
        self.lbl_remote_status.setText(_translate("Frame", "Remote"))
        self.lbl_intensity_status.setText(_translate("Frame", "Intensity"))
        self.lbl_item_select.setText(_translate("Frame", "Select"))
        self.lbl_coaster_status.setText(_translate("Frame", "Status"))
        self.groupBox_5.setTitle(_translate("Frame", "Client consistency"))
        self.lbl_state_delta.setText(_translate("Frame", "State delta"))
        self.lbl_frame_delta.setText(_translate("Frame", "Frame delta"))

