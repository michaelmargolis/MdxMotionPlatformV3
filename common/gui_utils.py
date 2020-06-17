# gui_utils

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