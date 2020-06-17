# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'output\fstlib\festo_emulator.ui'
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
        MainWindow.resize(545, 383)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gb_actuator_percent = QtGui.QGroupBox(self.centralwidget)
        self.gb_actuator_percent.setGeometry(QtCore.QRect(30, 70, 471, 261))
        self.gb_actuator_percent.setObjectName(_fromUtf8("gb_actuator_percent"))
        self.muscle_3 = QtGui.QFrame(self.gb_actuator_percent)
        self.muscle_3.setEnabled(False)
        self.muscle_3.setGeometry(QtCore.QRect(79, 150, 300, 20))
        self.muscle_3.setFrameShadow(QtGui.QFrame.Plain)
        self.muscle_3.setLineWidth(8)
        self.muscle_3.setFrameShape(QtGui.QFrame.HLine)
        self.muscle_3.setObjectName(_fromUtf8("muscle_3"))
        self.muscle_4 = QtGui.QFrame(self.gb_actuator_percent)
        self.muscle_4.setEnabled(False)
        self.muscle_4.setGeometry(QtCore.QRect(79, 190, 300, 20))
        self.muscle_4.setFrameShadow(QtGui.QFrame.Plain)
        self.muscle_4.setLineWidth(8)
        self.muscle_4.setFrameShape(QtGui.QFrame.HLine)
        self.muscle_4.setObjectName(_fromUtf8("muscle_4"))
        self.muscle_5 = QtGui.QFrame(self.gb_actuator_percent)
        self.muscle_5.setEnabled(False)
        self.muscle_5.setGeometry(QtCore.QRect(79, 230, 300, 20))
        self.muscle_5.setFrameShadow(QtGui.QFrame.Plain)
        self.muscle_5.setLineWidth(8)
        self.muscle_5.setFrameShape(QtGui.QFrame.HLine)
        self.muscle_5.setObjectName(_fromUtf8("muscle_5"))
        self.muscle_2 = QtGui.QFrame(self.gb_actuator_percent)
        self.muscle_2.setEnabled(False)
        self.muscle_2.setGeometry(QtCore.QRect(79, 110, 300, 20))
        self.muscle_2.setFrameShadow(QtGui.QFrame.Plain)
        self.muscle_2.setLineWidth(8)
        self.muscle_2.setFrameShape(QtGui.QFrame.HLine)
        self.muscle_2.setObjectName(_fromUtf8("muscle_2"))
        self.muscle_1 = QtGui.QFrame(self.gb_actuator_percent)
        self.muscle_1.setEnabled(False)
        self.muscle_1.setGeometry(QtCore.QRect(79, 70, 300, 20))
        self.muscle_1.setFrameShadow(QtGui.QFrame.Plain)
        self.muscle_1.setLineWidth(8)
        self.muscle_1.setFrameShape(QtGui.QFrame.HLine)
        self.muscle_1.setObjectName(_fromUtf8("muscle_1"))
        self.muscle_0 = QtGui.QFrame(self.gb_actuator_percent)
        self.muscle_0.setEnabled(False)
        self.muscle_0.setGeometry(QtCore.QRect(79, 30, 300, 20))
        self.muscle_0.setFrameShadow(QtGui.QFrame.Plain)
        self.muscle_0.setLineWidth(8)
        self.muscle_0.setFrameShape(QtGui.QFrame.HLine)
        self.muscle_0.setObjectName(_fromUtf8("muscle_0"))
        self.txt_muscle_0 = QtGui.QLabel(self.gb_actuator_percent)
        self.txt_muscle_0.setGeometry(QtCore.QRect(410, 30, 46, 13))
        self.txt_muscle_0.setObjectName(_fromUtf8("txt_muscle_0"))
        self.txt_muscle_1 = QtGui.QLabel(self.gb_actuator_percent)
        self.txt_muscle_1.setGeometry(QtCore.QRect(410, 70, 46, 13))
        self.txt_muscle_1.setObjectName(_fromUtf8("txt_muscle_1"))
        self.txt_muscle_2 = QtGui.QLabel(self.gb_actuator_percent)
        self.txt_muscle_2.setGeometry(QtCore.QRect(410, 110, 46, 13))
        self.txt_muscle_2.setObjectName(_fromUtf8("txt_muscle_2"))
        self.txt_muscle_3 = QtGui.QLabel(self.gb_actuator_percent)
        self.txt_muscle_3.setGeometry(QtCore.QRect(410, 150, 46, 13))
        self.txt_muscle_3.setObjectName(_fromUtf8("txt_muscle_3"))
        self.txt_muscle_4 = QtGui.QLabel(self.gb_actuator_percent)
        self.txt_muscle_4.setGeometry(QtCore.QRect(410, 190, 46, 13))
        self.txt_muscle_4.setObjectName(_fromUtf8("txt_muscle_4"))
        self.txt_muscle_5 = QtGui.QLabel(self.gb_actuator_percent)
        self.txt_muscle_5.setGeometry(QtCore.QRect(410, 230, 46, 13))
        self.txt_muscle_5.setObjectName(_fromUtf8("txt_muscle_5"))
        self.txt_muscle_6 = QtGui.QLabel(self.gb_actuator_percent)
        self.txt_muscle_6.setGeometry(QtCore.QRect(10, 231, 46, 13))
        self.txt_muscle_6.setObjectName(_fromUtf8("txt_muscle_6"))
        self.txt_muscle_7 = QtGui.QLabel(self.gb_actuator_percent)
        self.txt_muscle_7.setGeometry(QtCore.QRect(10, 31, 46, 13))
        self.txt_muscle_7.setObjectName(_fromUtf8("txt_muscle_7"))
        self.txt_muscle_8 = QtGui.QLabel(self.gb_actuator_percent)
        self.txt_muscle_8.setGeometry(QtCore.QRect(10, 71, 46, 13))
        self.txt_muscle_8.setObjectName(_fromUtf8("txt_muscle_8"))
        self.txt_muscle_9 = QtGui.QLabel(self.gb_actuator_percent)
        self.txt_muscle_9.setGeometry(QtCore.QRect(10, 151, 46, 13))
        self.txt_muscle_9.setObjectName(_fromUtf8("txt_muscle_9"))
        self.txt_muscle_10 = QtGui.QLabel(self.gb_actuator_percent)
        self.txt_muscle_10.setGeometry(QtCore.QRect(10, 191, 46, 13))
        self.txt_muscle_10.setObjectName(_fromUtf8("txt_muscle_10"))
        self.txt_muscle_11 = QtGui.QLabel(self.gb_actuator_percent)
        self.txt_muscle_11.setGeometry(QtCore.QRect(10, 111, 46, 13))
        self.txt_muscle_11.setObjectName(_fromUtf8("txt_muscle_11"))
        self.lbl_connection = QtGui.QLabel(self.centralwidget)
        self.lbl_connection.setGeometry(QtCore.QRect(40, 30, 211, 16))
        self.lbl_connection.setObjectName(_fromUtf8("lbl_connection"))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 545, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "Festo Emulator", None))
        self.gb_actuator_percent.setTitle(_translate("MainWindow", "Valve Pressures", None))
        self.txt_muscle_0.setText(_translate("MainWindow", "Muscle 0", None))
        self.txt_muscle_1.setText(_translate("MainWindow", "Muscle 1", None))
        self.txt_muscle_2.setText(_translate("MainWindow", "Muscle 2", None))
        self.txt_muscle_3.setText(_translate("MainWindow", "Muscle 3", None))
        self.txt_muscle_4.setText(_translate("MainWindow", "Muscle 4", None))
        self.txt_muscle_5.setText(_translate("MainWindow", "Muscle 5", None))
        self.txt_muscle_6.setText(_translate("MainWindow", "Muscle 5", None))
        self.txt_muscle_7.setText(_translate("MainWindow", "Muscle 0", None))
        self.txt_muscle_8.setText(_translate("MainWindow", "Muscle 1", None))
        self.txt_muscle_9.setText(_translate("MainWindow", "Muscle 3", None))
        self.txt_muscle_10.setText(_translate("MainWindow", "Muscle 4", None))
        self.txt_muscle_11.setText(_translate("MainWindow", "Muscle 2", None))
        self.lbl_connection.setText(_translate("MainWindow", "Not connected", None))

