# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'space_coaster\remote_client_gui.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Frame(object):
    def setupUi(self, Frame):
        Frame.setObjectName(_fromUtf8("Frame"))
        Frame.resize(800, 448)
        Frame.setFrameShape(QtGui.QFrame.StyledPanel)
        Frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frm_input = QtGui.QFrame(Frame)
        self.frm_input.setGeometry(QtCore.QRect(5, 4, 791, 351))
        self.frm_input.setStyleSheet(_fromUtf8("background-color: #f0f0f0"))
        self.frm_input.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frm_input.setFrameShadow(QtGui.QFrame.Raised)
        self.frm_input.setObjectName(_fromUtf8("frm_input"))
        self.btn_dispatch = QtGui.QPushButton(self.frm_input)
        self.btn_dispatch.setGeometry(QtCore.QRect(210, 173, 111, 51))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.btn_dispatch.setFont(font)
        self.btn_dispatch.setStyleSheet(_fromUtf8("color:white;background-color: green;"))
        self.btn_dispatch.setObjectName(_fromUtf8("btn_dispatch"))
        self.btn_pause = QtGui.QPushButton(self.frm_input)
        self.btn_pause.setGeometry(QtCore.QRect(460, 173, 111, 51))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btn_pause.setFont(font)
        self.btn_pause.setStyleSheet(_fromUtf8("background-color: orange\n"
""))
        self.btn_pause.setObjectName(_fromUtf8("btn_pause"))
        self.groupBox = QtGui.QGroupBox(self.frm_input)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 361, 131))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.lbl_coaster_status_1 = QtGui.QLabel(self.groupBox)
        self.lbl_coaster_status_1.setGeometry(QtCore.QRect(22, 30, 331, 21))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.lbl_coaster_status_1.setFont(font)
        self.lbl_coaster_status_1.setObjectName(_fromUtf8("lbl_coaster_status_1"))
        self.lbl_coaster_connection_1 = QtGui.QLabel(self.groupBox)
        self.lbl_coaster_connection_1.setGeometry(QtCore.QRect(20, 65, 331, 19))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_coaster_connection_1.setFont(font)
        self.lbl_coaster_connection_1.setObjectName(_fromUtf8("lbl_coaster_connection_1"))
        self.btn_reset_rift_1 = QtGui.QPushButton(self.groupBox)
        self.btn_reset_rift_1.setGeometry(QtCore.QRect(20, 100, 91, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btn_reset_rift_1.setFont(font)
        self.btn_reset_rift_1.setObjectName(_fromUtf8("btn_reset_rift_1"))
        self.groupBox_3 = QtGui.QGroupBox(self.frm_input)
        self.groupBox_3.setGeometry(QtCore.QRect(10, 260, 761, 81))
        self.groupBox_3.setObjectName(_fromUtf8("groupBox_3"))
        self.lbl_remote_status = QtGui.QLabel(self.groupBox_3)
        self.lbl_remote_status.setGeometry(QtCore.QRect(20, 50, 501, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_remote_status.setFont(font)
        self.lbl_remote_status.setObjectName(_fromUtf8("lbl_remote_status"))
        self.lbl_intensity_status = QtGui.QLabel(self.groupBox_3)
        self.lbl_intensity_status.setGeometry(QtCore.QRect(20, 20, 341, 19))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_intensity_status.setFont(font)
        self.lbl_intensity_status.setObjectName(_fromUtf8("lbl_intensity_status"))
        self.groupBox_4 = QtGui.QGroupBox(self.frm_input)
        self.groupBox_4.setGeometry(QtCore.QRect(410, 10, 361, 131))
        self.groupBox_4.setObjectName(_fromUtf8("groupBox_4"))
        self.lbl_coaster_status_2 = QtGui.QLabel(self.groupBox_4)
        self.lbl_coaster_status_2.setGeometry(QtCore.QRect(22, 30, 331, 21))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.lbl_coaster_status_2.setFont(font)
        self.lbl_coaster_status_2.setObjectName(_fromUtf8("lbl_coaster_status_2"))
        self.lbl_coaster_connection_2 = QtGui.QLabel(self.groupBox_4)
        self.lbl_coaster_connection_2.setGeometry(QtCore.QRect(20, 65, 331, 19))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_coaster_connection_2.setFont(font)
        self.lbl_coaster_connection_2.setObjectName(_fromUtf8("lbl_coaster_connection_2"))
        self.btn_reset_rift_2 = QtGui.QPushButton(self.groupBox_4)
        self.btn_reset_rift_2.setGeometry(QtCore.QRect(20, 100, 91, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btn_reset_rift_2.setFont(font)
        self.btn_reset_rift_2.setObjectName(_fromUtf8("btn_reset_rift_2"))

        self.retranslateUi(Frame)
        QtCore.QMetaObject.connectSlotsByName(Frame)

    def retranslateUi(self, Frame):
        Frame.setWindowTitle(_translate("Frame", "Frame", None))
        self.btn_dispatch.setText(_translate("Frame", "Dispatch", None))
        self.btn_pause.setText(_translate("Frame", "Pause", None))
        self.groupBox.setTitle(_translate("Frame", "Client 1", None))
        self.lbl_coaster_status_1.setText(_translate("Frame", "Status", None))
        self.lbl_coaster_connection_1.setText(_translate("Frame", "Connection", None))
        self.btn_reset_rift_1.setText(_translate("Frame", "Reset Rift", None))
        self.groupBox_3.setTitle(_translate("Frame", "System", None))
        self.lbl_remote_status.setText(_translate("Frame", "Remote", None))
        self.lbl_intensity_status.setText(_translate("Frame", "Intensity", None))
        self.groupBox_4.setTitle(_translate("Frame", "Client 2", None))
        self.lbl_coaster_status_2.setText(_translate("Frame", "Status", None))
        self.lbl_coaster_connection_2.setText(_translate("Frame", "Connection", None))
        self.btn_reset_rift_2.setText(_translate("Frame", "Reset Rift", None))

