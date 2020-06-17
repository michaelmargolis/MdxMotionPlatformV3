# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'coaster\coaster_gui.ui'
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
        Frame.resize(800, 439)
        Frame.setFrameShape(QtGui.QFrame.StyledPanel)
        Frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frm_input = QtGui.QFrame(Frame)
        self.frm_input.setGeometry(QtCore.QRect(5, 4, 791, 351))
        self.frm_input.setStyleSheet(_fromUtf8("background-color: #f0f0f0"))
        self.frm_input.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frm_input.setFrameShadow(QtGui.QFrame.Raised)
        self.frm_input.setObjectName(_fromUtf8("frm_input"))
        self.btn_dispatch = QtGui.QPushButton(self.frm_input)
        self.btn_dispatch.setGeometry(QtCore.QRect(80, 80, 111, 51))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.btn_dispatch.setFont(font)
        self.btn_dispatch.setStyleSheet(_fromUtf8("color:white;background-color: green;"))
        self.btn_dispatch.setObjectName(_fromUtf8("btn_dispatch"))
        self.btn_reset_rift = QtGui.QPushButton(self.frm_input)
        self.btn_reset_rift.setGeometry(QtCore.QRect(660, 80, 91, 51))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btn_reset_rift.setFont(font)
        self.btn_reset_rift.setObjectName(_fromUtf8("btn_reset_rift"))
        self.btn_pause = QtGui.QPushButton(self.frm_input)
        self.btn_pause.setGeometry(QtCore.QRect(350, 80, 111, 51))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.btn_pause.setFont(font)
        self.btn_pause.setStyleSheet(_fromUtf8("background-color: orange\n"
""))
        self.btn_pause.setObjectName(_fromUtf8("btn_pause"))
        self.cmb_park_listbox = QtGui.QComboBox(self.frm_input)
        self.cmb_park_listbox.setGeometry(QtCore.QRect(80, 20, 271, 41))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.cmb_park_listbox.setFont(font)
        self.cmb_park_listbox.setObjectName(_fromUtf8("cmb_park_listbox"))
        self.lbl_coaster_status = QtGui.QLabel(self.frm_input)
        self.lbl_coaster_status.setGeometry(QtCore.QRect(100, 142, 631, 41))
        font = QtGui.QFont()
        font.setPointSize(24)
        self.lbl_coaster_status.setFont(font)
        self.lbl_coaster_status.setObjectName(_fromUtf8("lbl_coaster_status"))
        self.frame = QtGui.QFrame(self.frm_input)
        self.frame.setGeometry(QtCore.QRect(90, 190, 671, 131))
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.lbl_intensity_status = QtGui.QLabel(self.frame)
        self.lbl_intensity_status.setGeometry(QtCore.QRect(11, 11, 631, 19))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_intensity_status.setFont(font)
        self.lbl_intensity_status.setObjectName(_fromUtf8("lbl_intensity_status"))
        self.lbl_remote_status = QtGui.QLabel(self.frame)
        self.lbl_remote_status.setGeometry(QtCore.QRect(11, 63, 641, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_remote_status.setFont(font)
        self.lbl_remote_status.setObjectName(_fromUtf8("lbl_remote_status"))
        self.lbl_coaster_connection = QtGui.QLabel(self.frame)
        self.lbl_coaster_connection.setGeometry(QtCore.QRect(11, 38, 641, 19))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_coaster_connection.setFont(font)
        self.lbl_coaster_connection.setObjectName(_fromUtf8("lbl_coaster_connection"))
        self.lbl_temperature_status = QtGui.QLabel(self.frame)
        self.lbl_temperature_status.setGeometry(QtCore.QRect(11, 90, 641, 19))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_temperature_status.setFont(font)
        self.lbl_temperature_status.setObjectName(_fromUtf8("lbl_temperature_status"))
        self.label_7 = QtGui.QLabel(self.frm_input)
        self.label_7.setGeometry(QtCore.QRect(370, 33, 81, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_7.setFont(font)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.lbl_platform = QtGui.QLabel(self.frm_input)
        self.lbl_platform.setGeometry(QtCore.QRect(625, 32, 121, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_platform.setFont(font)
        self.lbl_platform.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lbl_platform.setObjectName(_fromUtf8("lbl_platform"))

        self.retranslateUi(Frame)
        QtCore.QMetaObject.connectSlotsByName(Frame)

    def retranslateUi(self, Frame):
        Frame.setWindowTitle(_translate("Frame", "Frame", None))
        self.btn_dispatch.setText(_translate("Frame", "Dispatch", None))
        self.btn_reset_rift.setText(_translate("Frame", "Reset Rift", None))
        self.btn_pause.setText(_translate("Frame", "Pause", None))
        self.lbl_coaster_status.setText(_translate("Frame", "Status", None))
        self.lbl_intensity_status.setText(_translate("Frame", "Intensity", None))
        self.lbl_remote_status.setText(_translate("Frame", "Remote", None))
        self.lbl_coaster_connection.setText(_translate("Frame", "Connection", None))
        self.lbl_temperature_status.setText(_translate("Frame", "Temperature", None))
        self.label_7.setText(_translate("Frame", "Parks", None))
        self.lbl_platform.setText(_translate("Frame", "Platform", None))

