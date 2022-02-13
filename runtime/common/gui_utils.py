# gui_utils - some useful pyqt high level functions

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt


class CustomButton(object):
    def __init__(self, button, unchecked_colors, checked_colors, radius=0, border=0):    
        self.button = button
        self.unchecked_colors = unchecked_colors # (text color, background color)
        self.checked_colors = checked_colors
        self.radius = radius
        self.border = border

    def set_checked(self, is_checked):
        """ ignore border radius
        if is_checked:
            ss = format("QPushButton{color: %s; background-color : %s; border-radius:%dpx; border: %dpx}" %
                        (self.checked_colors[0], self.checked_colors[1], self.radius, self.border)) 
        else:
            ss = format("QPushButton{color: %s; background-color : %s; border-radius:%dpx; border: %dpx}" %
                        (self.unchecked_colors[0], self.unchecked_colors[1], self.radius, self.border))                        
        """
        if is_checked:
            ss = format("QPushButton{color: %s; background-color : %s }" %
                        (self.checked_colors[0], self.checked_colors[1])) 
        else:
            ss = format("QPushButton{color: %s; background-color : %s}" %
                        (self.unchecked_colors[0], self.unchecked_colors[1]))    
        self.button.setStyleSheet(ss)

    def set_enabled(self, is_enabled):
        self.button.setEnabled(is_enabled)
        
    def set_attributes(self, is_enabled, is_checked, text=None):
        self.set_enabled(is_enabled)
        self.set_checked(is_checked)
        if text != None:
           self.button.setText(text)
 
class ToggleSwitch(QtWidgets.QPushButton):
    def __init__(self, parent = None, on_label = "ON", off_label = "OFF"):
        super().__init__(parent)
        self.setCheckable(True)
        self.fontmetrics = QtGui.QFontMetrics(self.font())
        self.textsize = self.fontmetrics.size(0, max(on_label,off_label))
        self.setMinimumWidth(self.textsize.width())
        self.setMinimumHeight(self.textsize.height())
        self.on_label = on_label
        self.off_label = off_label

    def paintEvent(self, event):
        label = self.on_label if self.isChecked() else self.off_label
        bg_color = Qt.green if self.isChecked() else Qt.red

        radius = self.textsize.height()
        width = self.textsize.width() + radius*2 # add some padding
        center = self.rect().center()

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.translate(center)
        painter.setBrush(QtGui.QColor(0,0,0))

        pen = QtGui.QPen(Qt.black)
        pen.setWidth(2)
        painter.setPen(pen)

        painter.drawRoundedRect(QtCore.QRect(-width, -radius, 2*width, 2*radius), radius, radius)
        painter.setBrush(QtGui.QBrush(bg_color))
        sw_rect = QtCore.QRect(-radius, -radius, width + radius, 2*radius)
        if not self.isChecked():
            sw_rect.moveLeft(-width)
        painter.drawRoundedRect(sw_rect, radius, radius)
        painter.drawText(sw_rect, Qt.AlignCenter, label)
        painter.drawText(sw_rect, Qt.AlignCenter, label)
        

def set_text(widget, text, color= None):
    widget.setText(text)
    if color != None:
        widget.setStyleSheet("color: " + color)


def set_button_style(object, is_enabled, is_checked=None, text=None, checked_color=None):
    if text != None:
       object.setText(text)
    if is_checked!= None:
        object.setCheckable(True)
        object.setChecked(is_checked)
        if is_checked and checked_color != None:
           object.setStyleSheet("background-color:" + checked_color) 
        else:
           object.setStyleSheet("background-color: silver")
    if is_enabled != None:
       object.setEnabled(is_enabled)

def sleep_qt(delay):
    # delay is time in seconds to sleep
    loop = QtCore.QEventLoop()
    timer = QtCore.QTimer()
    timer.setInterval(int(delay*1000))
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start()
    loop.exec_()