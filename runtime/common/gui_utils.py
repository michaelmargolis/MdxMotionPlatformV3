# gui_utils
from PyQt5 import QtCore


class CustomButton(object):
    def __init__(self, button, unchecked_colors, checked_colors, radius=0, border=0):    
        self.button = button
        self.unchecked_colors = unchecked_colors # (text color, background color)
        self.checked_colors = checked_colors
        self.radius = radius
        self.border = border

    def set_checked(self, is_checked):
        if is_checked:
            ss = format("QPushButton{color: %s; background-color : %s; border-radius:%dpx; border: %dpx}" %
                        (self.checked_colors[0], self.checked_colors[1], self.radius, self.border)) 
        else:
            ss = format("QPushButton{color: %s; background-color : %s; border-radius:%dpx; border: %dpx}" %
                        (self.unchecked_colors[0], self.unchecked_colors[1], self.radius, self.border))
        self.button.setStyleSheet(ss)

    def set_enabled(self, is_enabled):
        self.button.setEnabled(is_enabled)
        
    def set_attributes(self, is_enabled, is_checked, text=None):
        self.set_enabled(is_enabled)
        self.set_checked(is_checked)
        if text != None:
           self.button.setText(text)
        

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
    loop = QtCore.QEventLoop()
    timer = QtCore.QTimer()
    timer.setInterval(delay*1000)
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start()
    loop.exec_()