# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'output\output_gui.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Frame(object):
    def setupUi(self, Frame):
        Frame.setObjectName("Frame")
        Frame.resize(800, 440)
        Frame.setStyleSheet("")
        Frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        Frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frm_output = QtWidgets.QFrame(Frame)
        self.frm_output.setGeometry(QtCore.QRect(0, 0, 791, 351))
        self.frm_output.setStyleSheet("background-color: #f0f0f0")
        self.frm_output.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frm_output.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frm_output.setObjectName("frm_output")
        self.gb_actuator_percent = QtWidgets.QGroupBox(self.frm_output)
        self.gb_actuator_percent.setGeometry(QtCore.QRect(410, 10, 321, 261))
        self.gb_actuator_percent.setObjectName("gb_actuator_percent")
        self.muscle_3 = QtWidgets.QFrame(self.gb_actuator_percent)
        self.muscle_3.setEnabled(False)
        self.muscle_3.setGeometry(QtCore.QRect(20, 150, 200, 16))
        self.muscle_3.setFrameShadow(QtWidgets.QFrame.Plain)
        self.muscle_3.setLineWidth(8)
        self.muscle_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.muscle_3.setObjectName("muscle_3")
        self.muscle_4 = QtWidgets.QFrame(self.gb_actuator_percent)
        self.muscle_4.setEnabled(False)
        self.muscle_4.setGeometry(QtCore.QRect(20, 190, 200, 16))
        self.muscle_4.setFrameShadow(QtWidgets.QFrame.Plain)
        self.muscle_4.setLineWidth(8)
        self.muscle_4.setFrameShape(QtWidgets.QFrame.HLine)
        self.muscle_4.setObjectName("muscle_4")
        self.muscle_5 = QtWidgets.QFrame(self.gb_actuator_percent)
        self.muscle_5.setEnabled(False)
        self.muscle_5.setGeometry(QtCore.QRect(20, 230, 200, 16))
        self.muscle_5.setFrameShadow(QtWidgets.QFrame.Plain)
        self.muscle_5.setLineWidth(8)
        self.muscle_5.setFrameShape(QtWidgets.QFrame.HLine)
        self.muscle_5.setObjectName("muscle_5")
        self.muscle_2 = QtWidgets.QFrame(self.gb_actuator_percent)
        self.muscle_2.setEnabled(False)
        self.muscle_2.setGeometry(QtCore.QRect(20, 110, 200, 16))
        self.muscle_2.setFrameShadow(QtWidgets.QFrame.Plain)
        self.muscle_2.setLineWidth(8)
        self.muscle_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.muscle_2.setObjectName("muscle_2")
        self.muscle_1 = QtWidgets.QFrame(self.gb_actuator_percent)
        self.muscle_1.setEnabled(False)
        self.muscle_1.setGeometry(QtCore.QRect(20, 70, 200, 16))
        self.muscle_1.setFrameShadow(QtWidgets.QFrame.Plain)
        self.muscle_1.setLineWidth(8)
        self.muscle_1.setFrameShape(QtWidgets.QFrame.HLine)
        self.muscle_1.setObjectName("muscle_1")
        self.muscle_0 = QtWidgets.QFrame(self.gb_actuator_percent)
        self.muscle_0.setEnabled(False)
        self.muscle_0.setGeometry(QtCore.QRect(20, 30, 200, 16))
        self.muscle_0.setFrameShadow(QtWidgets.QFrame.Plain)
        self.muscle_0.setLineWidth(8)
        self.muscle_0.setFrameShape(QtWidgets.QFrame.HLine)
        self.muscle_0.setObjectName("muscle_0")
        self.txt_muscle_0 = QtWidgets.QLabel(self.gb_actuator_percent)
        self.txt_muscle_0.setGeometry(QtCore.QRect(240, 30, 71, 16))
        self.txt_muscle_0.setObjectName("txt_muscle_0")
        self.txt_muscle_1 = QtWidgets.QLabel(self.gb_actuator_percent)
        self.txt_muscle_1.setGeometry(QtCore.QRect(240, 70, 71, 16))
        self.txt_muscle_1.setObjectName("txt_muscle_1")
        self.txt_muscle_2 = QtWidgets.QLabel(self.gb_actuator_percent)
        self.txt_muscle_2.setGeometry(QtCore.QRect(240, 110, 71, 16))
        self.txt_muscle_2.setObjectName("txt_muscle_2")
        self.txt_muscle_3 = QtWidgets.QLabel(self.gb_actuator_percent)
        self.txt_muscle_3.setGeometry(QtCore.QRect(240, 150, 71, 16))
        self.txt_muscle_3.setObjectName("txt_muscle_3")
        self.txt_muscle_4 = QtWidgets.QLabel(self.gb_actuator_percent)
        self.txt_muscle_4.setGeometry(QtCore.QRect(240, 190, 71, 16))
        self.txt_muscle_4.setObjectName("txt_muscle_4")
        self.txt_muscle_5 = QtWidgets.QLabel(self.gb_actuator_percent)
        self.txt_muscle_5.setGeometry(QtCore.QRect(240, 230, 71, 16))
        self.txt_muscle_5.setObjectName("txt_muscle_5")
        self.grp_request = QtWidgets.QGroupBox(self.frm_output)
        self.grp_request.setGeometry(QtCore.QRect(40, 10, 311, 121))
        self.grp_request.setObjectName("grp_request")
        self.txt_xform_0 = QtWidgets.QLineEdit(self.grp_request)
        self.txt_xform_0.setGeometry(QtCore.QRect(100, 40, 51, 20))
        font = QtGui.QFont()
        font.setFamily("Verdana")
        self.txt_xform_0.setFont(font)
        self.txt_xform_0.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.txt_xform_0.setObjectName("txt_xform_0")
        self.label = QtWidgets.QLabel(self.grp_request)
        self.label.setGeometry(QtCore.QRect(10, 40, 81, 16))
        self.label.setObjectName("label")
        self.txt_xform_3 = QtWidgets.QLineEdit(self.grp_request)
        self.txt_xform_3.setGeometry(QtCore.QRect(100, 70, 51, 20))
        font = QtGui.QFont()
        font.setFamily("Verdana")
        self.txt_xform_3.setFont(font)
        self.txt_xform_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.txt_xform_3.setObjectName("txt_xform_3")
        self.label_2 = QtWidgets.QLabel(self.grp_request)
        self.label_2.setGeometry(QtCore.QRect(10, 70, 81, 16))
        self.label_2.setObjectName("label_2")
        self.txt_xform_1 = QtWidgets.QLineEdit(self.grp_request)
        self.txt_xform_1.setGeometry(QtCore.QRect(170, 40, 51, 20))
        font = QtGui.QFont()
        font.setFamily("Verdana")
        self.txt_xform_1.setFont(font)
        self.txt_xform_1.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.txt_xform_1.setObjectName("txt_xform_1")
        self.txt_xform_2 = QtWidgets.QLineEdit(self.grp_request)
        self.txt_xform_2.setGeometry(QtCore.QRect(240, 40, 51, 20))
        font = QtGui.QFont()
        font.setFamily("Verdana")
        self.txt_xform_2.setFont(font)
        self.txt_xform_2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.txt_xform_2.setObjectName("txt_xform_2")
        self.txt_xform_4 = QtWidgets.QLineEdit(self.grp_request)
        self.txt_xform_4.setGeometry(QtCore.QRect(170, 70, 51, 20))
        font = QtGui.QFont()
        font.setFamily("Verdana")
        self.txt_xform_4.setFont(font)
        self.txt_xform_4.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.txt_xform_4.setObjectName("txt_xform_4")
        self.txt_xform_5 = QtWidgets.QLineEdit(self.grp_request)
        self.txt_xform_5.setGeometry(QtCore.QRect(240, 70, 51, 20))
        font = QtGui.QFont()
        font.setFamily("Verdana")
        self.txt_xform_5.setFont(font)
        self.txt_xform_5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.txt_xform_5.setObjectName("txt_xform_5")
        self.label_3 = QtWidgets.QLabel(self.grp_request)
        self.label_3.setGeometry(QtCore.QRect(106, 94, 41, 16))
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.grp_request)
        self.label_4.setGeometry(QtCore.QRect(175, 94, 41, 16))
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(self.grp_request)
        self.label_5.setGeometry(QtCore.QRect(244, 94, 41, 16))
        self.label_5.setAlignment(QtCore.Qt.AlignCenter)
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(self.grp_request)
        self.label_6.setGeometry(QtCore.QRect(243, 18, 41, 16))
        self.label_6.setAlignment(QtCore.Qt.AlignCenter)
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(self.grp_request)
        self.label_7.setGeometry(QtCore.QRect(105, 18, 41, 16))
        self.label_7.setAlignment(QtCore.Qt.AlignCenter)
        self.label_7.setObjectName("label_7")
        self.label_8 = QtWidgets.QLabel(self.grp_request)
        self.label_8.setGeometry(QtCore.QRect(174, 18, 41, 16))
        self.label_8.setAlignment(QtCore.Qt.AlignCenter)
        self.label_8.setObjectName("label_8")
        self.frame = QtWidgets.QFrame(self.frm_output)
        self.frame.setGeometry(QtCore.QRect(40, 140, 311, 191))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.gb_processing_dur = QtWidgets.QGroupBox(self.frm_output)
        self.gb_processing_dur.setGeometry(QtCore.QRect(410, 280, 321, 51))
        self.gb_processing_dur.setObjectName("gb_processing_dur")
        self.txt_processing_dur = QtWidgets.QLabel(self.gb_processing_dur)
        self.txt_processing_dur.setGeometry(QtCore.QRect(240, 19, 71, 16))
        self.txt_processing_dur.setObjectName("txt_processing_dur")
        self.line = QtWidgets.QFrame(self.gb_processing_dur)
        self.line.setGeometry(QtCore.QRect(112, 10, 16, 21))
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.rect_dur = QtWidgets.QFrame(self.gb_processing_dur)
        self.rect_dur.setEnabled(False)
        self.rect_dur.setGeometry(QtCore.QRect(20, 20, 200, 20))
        self.rect_dur.setStyleSheet("color: rgb(85, 255, 127);")
        self.rect_dur.setFrameShadow(QtWidgets.QFrame.Plain)
        self.rect_dur.setLineWidth(8)
        self.rect_dur.setFrameShape(QtWidgets.QFrame.HLine)
        self.rect_dur.setObjectName("rect_dur")
        self.label_9 = QtWidgets.QLabel(Frame)
        self.label_9.setGeometry(QtCore.QRect(525, 315, 46, 13))
        self.label_9.setObjectName("label_9")

        self.retranslateUi(Frame)
        QtCore.QMetaObject.connectSlotsByName(Frame)

    def retranslateUi(self, Frame):
        _translate = QtCore.QCoreApplication.translate
        Frame.setWindowTitle(_translate("Frame", "Frame"))
        self.gb_actuator_percent.setTitle(_translate("Frame", "Actuators"))
        self.txt_muscle_0.setText(_translate("Frame", "Muscle 0"))
        self.txt_muscle_1.setText(_translate("Frame", "Muscle 1"))
        self.txt_muscle_2.setText(_translate("Frame", "Muscle 2"))
        self.txt_muscle_3.setText(_translate("Frame", "Muscle 3"))
        self.txt_muscle_4.setText(_translate("Frame", "Muscle 4"))
        self.txt_muscle_5.setText(_translate("Frame", "Muscle 5"))
        self.grp_request.setTitle(_translate("Frame", "Request"))
        self.txt_xform_0.setText(_translate("Frame", "000"))
        self.label.setText(_translate("Frame", "Translation"))
        self.txt_xform_3.setText(_translate("Frame", "0.00"))
        self.label_2.setText(_translate("Frame", "Rotation"))
        self.txt_xform_1.setText(_translate("Frame", "000"))
        self.txt_xform_2.setText(_translate("Frame", "000"))
        self.txt_xform_4.setText(_translate("Frame", "0.00"))
        self.txt_xform_5.setText(_translate("Frame", "0.00"))
        self.label_3.setText(_translate("Frame", "Roll"))
        self.label_4.setText(_translate("Frame", "Pitch"))
        self.label_5.setText(_translate("Frame", "Yaw"))
        self.label_6.setText(_translate("Frame", "Z"))
        self.label_7.setText(_translate("Frame", "X"))
        self.label_8.setText(_translate("Frame", "Y"))
        self.gb_processing_dur.setTitle(_translate("Frame", "Processing duration "))
        self.txt_processing_dur.setText(_translate("Frame", "0"))
        self.label_9.setText(_translate("Frame", "10 ms"))

