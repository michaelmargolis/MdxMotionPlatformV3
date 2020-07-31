from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt

class ModelessDialog(QDialog):
    def __init__(self, parent):
        try:
            super().__init__(parent)
        except:
            super(QDialog, self).__init__(parent) 
        self.resize(506, 91)
        self.txt_info = QLabel(self)
        self.txt_info.setGeometry(QtCore.QRect(30, 30, 451, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.txt_info.setFont(font)
        self.txt_info.setTextFormat(QtCore.Qt.PlainText)
        self.txt_info.setAlignment(QtCore.Qt.AlignCenter)
        self.txt_info.setObjectName("txt_info")

        # QtCore.QMetaObject.connectSlotsByName(Dialog)



    def setText(self, text):
        self.txt_info.setText("Dialog", "Flip Emergency Stop Switch down to proceed")
