# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gui.ui'
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

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1028, 959)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.groupBox = QtGui.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(20, 4, 271, 61))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.btn_open = QtGui.QPushButton(self.groupBox)
        self.btn_open.setGeometry(QtCore.QRect(12, 20, 61, 23))
        self.btn_open.setObjectName(_fromUtf8("btn_open"))
        self.cmb_video_fname = QtGui.QComboBox(self.groupBox)
        self.cmb_video_fname.setGeometry(QtCore.QRect(80, 20, 111, 22))
        self.cmb_video_fname.setObjectName(_fromUtf8("cmb_video_fname"))
        self.txt_fps = QtGui.QLineEdit(self.groupBox)
        self.txt_fps.setGeometry(QtCore.QRect(232, 22, 31, 20))
        self.txt_fps.setObjectName(_fromUtf8("txt_fps"))
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setGeometry(QtCore.QRect(206, 24, 21, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.groupBox_2 = QtGui.QGroupBox(self.centralwidget)
        self.groupBox_2.setGeometry(QtCore.QRect(90, 65, 471, 81))
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.btn_play = QtGui.QPushButton(self.groupBox_2)
        self.btn_play.setGeometry(QtCore.QRect(11, 21, 61, 23))
        self.btn_play.setObjectName(_fromUtf8("btn_play"))
        self.btn_pause = QtGui.QPushButton(self.groupBox_2)
        self.btn_pause.setGeometry(QtCore.QRect(90, 21, 61, 23))
        self.btn_pause.setObjectName(_fromUtf8("btn_pause"))
        self.btn_goto_frame = QtGui.QPushButton(self.groupBox_2)
        self.btn_goto_frame.setGeometry(QtCore.QRect(182, 21, 71, 23))
        self.btn_goto_frame.setObjectName(_fromUtf8("btn_goto_frame"))
        self.txt_frame = QtGui.QLineEdit(self.groupBox_2)
        self.txt_frame.setGeometry(QtCore.QRect(260, 23, 51, 20))
        self.txt_frame.setObjectName(_fromUtf8("txt_frame"))
        self.txt_time = QtGui.QLineEdit(self.groupBox_2)
        self.txt_time.setGeometry(QtCore.QRect(410, 23, 51, 20))
        self.txt_time.setObjectName(_fromUtf8("txt_time"))
        self.sld_course_pos = QtGui.QSlider(self.groupBox_2)
        self.sld_course_pos.setGeometry(QtCore.QRect(10, 53, 391, 22))
        self.sld_course_pos.setOrientation(QtCore.Qt.Horizontal)
        self.sld_course_pos.setObjectName(_fromUtf8("sld_course_pos"))
        self.btn_rev = QtGui.QPushButton(self.groupBox_2)
        self.btn_rev.setGeometry(QtCore.QRect(410, 52, 21, 23))
        self.btn_rev.setObjectName(_fromUtf8("btn_rev"))
        self.btn_fwd = QtGui.QPushButton(self.groupBox_2)
        self.btn_fwd.setGeometry(QtCore.QRect(440, 52, 21, 23))
        self.btn_fwd.setObjectName(_fromUtf8("btn_fwd"))
        self.btn_goto_time = QtGui.QPushButton(self.groupBox_2)
        self.btn_goto_time.setGeometry(QtCore.QRect(332, 21, 71, 23))
        self.btn_goto_time.setObjectName(_fromUtf8("btn_goto_time"))
        self.groupBox_3 = QtGui.QGroupBox(self.centralwidget)
        self.groupBox_3.setGeometry(QtCore.QRect(570, 4, 431, 141))
        self.groupBox_3.setObjectName(_fromUtf8("groupBox_3"))
        self.frame = QtGui.QFrame(self.groupBox_3)
        self.frame.setGeometry(QtCore.QRect(10, 17, 411, 121))
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.frame_2 = QtGui.QFrame(self.frame)
        self.frame_2.setGeometry(QtCore.QRect(140, -5, 131, 121))
        self.frame_2.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtGui.QFrame.Raised)
        self.frame_2.setObjectName(_fromUtf8("frame_2"))
        self.label_10 = QtGui.QLabel(self.frame_2)
        self.label_10.setGeometry(QtCore.QRect(10, 6, 47, 20))
        self.label_10.setFrameShape(QtGui.QFrame.NoFrame)
        self.label_10.setObjectName(_fromUtf8("label_10"))
        self.txt_intensity = QtGui.QLineEdit(self.frame_2)
        self.txt_intensity.setGeometry(QtCore.QRect(60, 6, 31, 20))
        self.txt_intensity.setObjectName(_fromUtf8("txt_intensity"))
        self.txt_roll = QtGui.QLineEdit(self.frame_2)
        self.txt_roll.setGeometry(QtCore.QRect(60, 42, 61, 20))
        self.txt_roll.setObjectName(_fromUtf8("txt_roll"))
        self.lbl_roll = QtGui.QLabel(self.frame_2)
        self.lbl_roll.setGeometry(QtCore.QRect(10, 42, 31, 16))
        self.lbl_roll.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_roll.setObjectName(_fromUtf8("lbl_roll"))
        self.lbl_yaw = QtGui.QLabel(self.frame_2)
        self.lbl_yaw.setGeometry(QtCore.QRect(10, 90, 31, 16))
        self.lbl_yaw.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_yaw.setObjectName(_fromUtf8("lbl_yaw"))
        self.txt_pitch = QtGui.QLineEdit(self.frame_2)
        self.txt_pitch.setGeometry(QtCore.QRect(60, 66, 61, 20))
        self.txt_pitch.setObjectName(_fromUtf8("txt_pitch"))
        self.lbl_pitch = QtGui.QLabel(self.frame_2)
        self.lbl_pitch.setGeometry(QtCore.QRect(10, 66, 31, 16))
        self.lbl_pitch.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_pitch.setObjectName(_fromUtf8("lbl_pitch"))
        self.txt_yaw = QtGui.QLineEdit(self.frame_2)
        self.txt_yaw.setGeometry(QtCore.QRect(60, 90, 61, 20))
        self.txt_yaw.setObjectName(_fromUtf8("txt_yaw"))
        self.frame_3 = QtGui.QFrame(self.frame)
        self.frame_3.setGeometry(QtCore.QRect(7, 5, 121, 111))
        self.frame_3.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QtGui.QFrame.Raised)
        self.frame_3.setObjectName(_fromUtf8("frame_3"))
        self.label_6 = QtGui.QLabel(self.frame_3)
        self.label_6.setGeometry(QtCore.QRect(10, 10, 47, 13))
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.txt_speed = QtGui.QLineEdit(self.frame_3)
        self.txt_speed.setGeometry(QtCore.QRect(50, 10, 61, 20))
        self.txt_speed.setObjectName(_fromUtf8("txt_speed"))
        self.txt_x = QtGui.QLineEdit(self.frame_3)
        self.txt_x.setGeometry(QtCore.QRect(50, 34, 61, 20))
        self.txt_x.setObjectName(_fromUtf8("txt_x"))
        self.lbl_x = QtGui.QLabel(self.frame_3)
        self.lbl_x.setGeometry(QtCore.QRect(20, 34, 16, 16))
        self.lbl_x.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_x.setObjectName(_fromUtf8("lbl_x"))
        self.lbl_z = QtGui.QLabel(self.frame_3)
        self.lbl_z.setGeometry(QtCore.QRect(20, 82, 16, 16))
        self.lbl_z.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_z.setObjectName(_fromUtf8("lbl_z"))
        self.txt_y = QtGui.QLineEdit(self.frame_3)
        self.txt_y.setGeometry(QtCore.QRect(50, 58, 61, 20))
        self.txt_y.setObjectName(_fromUtf8("txt_y"))
        self.lbl_y = QtGui.QLabel(self.frame_3)
        self.lbl_y.setGeometry(QtCore.QRect(20, 58, 16, 16))
        self.lbl_y.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_y.setObjectName(_fromUtf8("lbl_y"))
        self.txt_z = QtGui.QLineEdit(self.frame_3)
        self.txt_z.setGeometry(QtCore.QRect(50, 82, 61, 20))
        self.txt_z.setObjectName(_fromUtf8("txt_z"))
        self.frame_5 = QtGui.QFrame(self.frame)
        self.frame_5.setGeometry(QtCore.QRect(280, 5, 121, 111))
        self.frame_5.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame_5.setFrameShadow(QtGui.QFrame.Raised)
        self.frame_5.setObjectName(_fromUtf8("frame_5"))
        self.label_14 = QtGui.QLabel(self.frame_5)
        self.label_14.setGeometry(QtCore.QRect(13, 10, 21, 16))
        self.label_14.setObjectName(_fromUtf8("label_14"))
        self.txt_heading = QtGui.QLineEdit(self.frame_5)
        self.txt_heading.setGeometry(QtCore.QRect(45, 10, 61, 20))
        self.txt_heading.setObjectName(_fromUtf8("txt_heading"))
        self.txt_ax = QtGui.QLineEdit(self.frame_5)
        self.txt_ax.setGeometry(QtCore.QRect(45, 34, 61, 20))
        self.txt_ax.setObjectName(_fromUtf8("txt_ax"))
        self.label_15 = QtGui.QLabel(self.frame_5)
        self.label_15.setGeometry(QtCore.QRect(15, 34, 21, 16))
        self.label_15.setObjectName(_fromUtf8("label_15"))
        self.label_16 = QtGui.QLabel(self.frame_5)
        self.label_16.setGeometry(QtCore.QRect(15, 82, 21, 16))
        self.label_16.setObjectName(_fromUtf8("label_16"))
        self.txt_ay = QtGui.QLineEdit(self.frame_5)
        self.txt_ay.setGeometry(QtCore.QRect(45, 58, 61, 20))
        self.txt_ay.setObjectName(_fromUtf8("txt_ay"))
        self.label_17 = QtGui.QLabel(self.frame_5)
        self.label_17.setGeometry(QtCore.QRect(15, 58, 21, 16))
        self.label_17.setObjectName(_fromUtf8("label_17"))
        self.txt_az = QtGui.QLineEdit(self.frame_5)
        self.txt_az.setGeometry(QtCore.QRect(45, 82, 61, 20))
        self.txt_az.setObjectName(_fromUtf8("txt_az"))
        self.frame_4 = QtGui.QFrame(self.centralwidget)
        self.frame_4.setGeometry(QtCore.QRect(20, 357, 981, 561))
        self.frame_4.setFrameShape(QtGui.QFrame.Box)
        self.frame_4.setFrameShadow(QtGui.QFrame.Raised)
        self.frame_4.setObjectName(_fromUtf8("frame_4"))
        self.lbl_video_frame = QtGui.QLabel(self.frame_4)
        self.lbl_video_frame.setGeometry(QtCore.QRect(10, 12, 960, 540))
        self.lbl_video_frame.setMinimumSize(QtCore.QSize(960, 540))
        self.lbl_video_frame.setMaximumSize(QtCore.QSize(960, 540))
        self.lbl_video_frame.setFrameShape(QtGui.QFrame.NoFrame)
        self.lbl_video_frame.setText(_fromUtf8(""))
        self.lbl_video_frame.setObjectName(_fromUtf8("lbl_video_frame"))
        self.lbl_chair_top = QtGui.QLabel(self.frame_4)
        self.lbl_chair_top.setGeometry(QtCore.QRect(890, 9, 81, 91))
        self.lbl_chair_top.setFrameShadow(QtGui.QFrame.Plain)
        self.lbl_chair_top.setLineWidth(1)
        self.lbl_chair_top.setMidLineWidth(0)
        self.lbl_chair_top.setText(_fromUtf8(""))
        self.lbl_chair_top.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_chair_top.setObjectName(_fromUtf8("lbl_chair_top"))
        self.groupBox_4 = QtGui.QGroupBox(self.centralwidget)
        self.groupBox_4.setGeometry(QtCore.QRect(20, 150, 981, 201))
        self.groupBox_4.setObjectName(_fromUtf8("groupBox_4"))
        self.plotWidget = PlotWidget(self.groupBox_4)
        self.plotWidget.setGeometry(QtCore.QRect(3, 20, 971, 171))
        self.plotWidget.setObjectName(_fromUtf8("plotWidget"))
        self.groupBox_5 = QtGui.QGroupBox(self.centralwidget)
        self.groupBox_5.setGeometry(QtCore.QRect(300, 5, 261, 61))
        self.groupBox_5.setObjectName(_fromUtf8("groupBox_5"))
        self.btn_serial_connect = QtGui.QPushButton(self.groupBox_5)
        self.btn_serial_connect.setGeometry(QtCore.QRect(10, 29, 61, 23))
        self.btn_serial_connect.setObjectName(_fromUtf8("btn_serial_connect"))
        self.cmb_model_port = QtGui.QComboBox(self.groupBox_5)
        self.cmb_model_port.setGeometry(QtCore.QRect(180, 30, 71, 22))
        self.cmb_model_port.setObjectName(_fromUtf8("cmb_model_port"))
        self.lbl_model = QtGui.QLabel(self.groupBox_5)
        self.lbl_model.setGeometry(QtCore.QRect(200, 10, 31, 16))
        self.lbl_model.setObjectName(_fromUtf8("lbl_model"))
        self.lbl_encoders = QtGui.QLabel(self.groupBox_5)
        self.lbl_encoders.setGeometry(QtCore.QRect(101, 10, 51, 16))
        self.lbl_encoders.setObjectName(_fromUtf8("lbl_encoders"))
        self.cmb_encoder_port = QtGui.QComboBox(self.groupBox_5)
        self.cmb_encoder_port.setGeometry(QtCore.QRect(90, 30, 71, 22))
        self.cmb_encoder_port.setObjectName(_fromUtf8("cmb_encoder_port"))
        self.gb_adjust = QtGui.QGroupBox(self.centralwidget)
        self.gb_adjust.setGeometry(QtCore.QRect(20, 65, 61, 81))
        self.gb_adjust.setObjectName(_fromUtf8("gb_adjust"))
        self.btn_load_adjust = QtGui.QPushButton(self.gb_adjust)
        self.btn_load_adjust.setGeometry(QtCore.QRect(10, 20, 41, 23))
        self.btn_load_adjust.setObjectName(_fromUtf8("btn_load_adjust"))
        self.chk_delta_capture = QtGui.QCheckBox(self.gb_adjust)
        self.chk_delta_capture.setGeometry(QtCore.QRect(6, 50, 51, 17))
        self.chk_delta_capture.setObjectName(_fromUtf8("chk_delta_capture"))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1028, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.groupBox.setTitle(_translate("MainWindow", "Video File", None))
        self.btn_open.setText(_translate("MainWindow", "Open", None))
        self.label.setText(_translate("MainWindow", "FPS", None))
        self.groupBox_2.setTitle(_translate("MainWindow", "Control", None))
        self.btn_play.setText(_translate("MainWindow", "Play", None))
        self.btn_pause.setText(_translate("MainWindow", "Pause", None))
        self.btn_goto_frame.setText(_translate("MainWindow", "Goto Frame", None))
        self.btn_rev.setText(_translate("MainWindow", "<", None))
        self.btn_fwd.setText(_translate("MainWindow", ">", None))
        self.btn_goto_time.setText(_translate("MainWindow", "Goto Time", None))
        self.groupBox_3.setTitle(_translate("MainWindow", "Telemetry", None))
        self.label_10.setText(_translate("MainWindow", "Intensity", None))
        self.lbl_roll.setText(_translate("MainWindow", "Roll", None))
        self.lbl_yaw.setText(_translate("MainWindow", "Yaw", None))
        self.lbl_pitch.setText(_translate("MainWindow", "Pitch", None))
        self.label_6.setText(_translate("MainWindow", "Speed", None))
        self.lbl_x.setText(_translate("MainWindow", "X", None))
        self.lbl_z.setText(_translate("MainWindow", "Z", None))
        self.lbl_y.setText(_translate("MainWindow", "Y", None))
        self.label_14.setText(_translate("MainWindow", "Hdg", None))
        self.label_15.setText(_translate("MainWindow", "aX", None))
        self.label_16.setText(_translate("MainWindow", "aZ", None))
        self.label_17.setText(_translate("MainWindow", "aY", None))
        self.groupBox_4.setTitle(_translate("MainWindow", "Plot", None))
        self.groupBox_5.setTitle(_translate("MainWindow", "Serial", None))
        self.btn_serial_connect.setText(_translate("MainWindow", "Connect", None))
        self.lbl_model.setText(_translate("MainWindow", "Model", None))
        self.lbl_encoders.setText(_translate("MainWindow", "Encoders", None))
        self.gb_adjust.setTitle(_translate("MainWindow", "Load", None))
        self.btn_load_adjust.setText(_translate("MainWindow", "Adjust", None))
        self.chk_delta_capture.setText(_translate("MainWindow", "Deltas", None))

from pyqtgraph import PlotWidget
