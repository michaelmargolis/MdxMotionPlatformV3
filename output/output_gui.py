""" output_gui
Copyright Michael Margolis, Middlesex University 2019; see LICENSE for software rights.

display muscle lengths and platform orientation
"""
SHOW_CHAIR_IMAGES = False

#  from output_gui_defs import *
from PyQt5 import QtCore, QtGui, QtWidgets
from output.output_gui_defs import Ui_Frame

import copy
# import time
from math import degrees
import platform_config as cfg

class OutputGui(object):

    def init_gui(self, frame, MIN_ACTUATOR_LEN , MAX_ACTUATOR_RANGE):
        self.ui = Ui_Frame()
        self.ui.setupUi(frame)
        self.MIN_ACTUATOR_LEN = MIN_ACTUATOR_LEN
        self.MAX_ACTUATOR_RANGE = MAX_ACTUATOR_RANGE
        # self.actuator_bars = [self.ui.pb_0,self.ui.pb_1,self.ui.pb_2,self.ui.pb_3,self.ui.pb_4,self.ui.pb_5]
        self.txt_xforms = [self.ui.txt_xform_0,self.ui.txt_xform_1,self.ui.txt_xform_2,self.ui.txt_xform_3,self.ui.txt_xform_4,self.ui.txt_xform_5]
        self.actuator_bars = [self.ui.muscle_0,self.ui.muscle_1,self.ui.muscle_2,self.ui.muscle_3,self.ui.muscle_4,self.ui.muscle_5]
        self.txt_muscles = [self.ui.txt_muscle_0,self.ui.txt_muscle_1,self.ui.txt_muscle_2,self.ui.txt_muscle_3,self.ui.txt_muscle_4,self.ui.txt_muscle_5]
        self.txt_up_indices = [self.ui.txt_up_idx_0,self.ui.txt_up_idx_1,self.ui.txt_up_idx_2,self.ui.txt_up_idx_3,self.ui.txt_up_idx_4,self.ui.txt_up_idx_5]
        self.txt_down_indices = [self.ui.txt_down_idx_0,self.ui.txt_down_idx_1,self.ui.txt_down_idx_2,self.ui.txt_down_idx_3,self.ui.txt_down_idx_4,self.ui.txt_down_idx_5]
        self.front_pixmap = QtGui.QPixmap('images/front.png')
        self.side_pixmap = QtGui.QPixmap('images/side.png')
        self.top_pixmap = QtGui.QPixmap('images/top.png')
        self.front_pos =  self.ui.lbl_front_view.pos()
        self.side_pos = self.ui.lbl_side_view.pos()
        self.top_pos = self.ui.lbl_top_view.pos()

    def encoders_is_enabled(self):
        return self.ui.rb_encoders.isChecked()

    def encoders_set_enabled(self, state):
        if state:
            self.ui.rb_encoders.setChecked(True)
        else:
            self.ui.rb_manual.setChecked(True)

    def do_transform(self, widget, pixmap, pos,  x, y, angle):
        widget.move(x + pos.x(), y + pos.y())
        xform = QtGui.QTransform().rotate(angle)  # front view: roll
        xformed_pixmap = pixmap.transformed(xform, QtCore.Qt.SmoothTransformation)
        widget.setPixmap(xformed_pixmap)
        # widget.adjustSize()

    def show_transform(self, transform):
        for idx, x in enumerate(transform):
            if idx < 3:
                self.txt_xforms[idx].setText(format("%d" % x))
            else:
                angle = x * 57.3
                self.txt_xforms[idx].setText(format("%0.1f" % angle))
            
        x = int(transform[0] / 4) 
        y = int(transform[1] / 4)
        z = -int(transform[2] / 4)

        self.do_transform(self.ui.lbl_front_view, self.front_pixmap, self.front_pos, y,z, transform[3] * 57.3) # front view: roll
        self.do_transform(self.ui.lbl_side_view, self.side_pixmap, self.side_pos, x,z, transform[4] * 57.3) # side view: pitch
        self.do_transform(self.ui.lbl_top_view, self.top_pixmap, self.top_pos,  y,x, transform[5] * 57.3)  # top view: yaw

    def show_muscles(self, transform, muscles, processing_dur):  # was passing  pressure_percent
        for i in range(6):
           rect =  self.actuator_bars[i].rect()
           width = muscles[i] 
           rect.setWidth(width)
           self.actuator_bars[i].setFrameRect(rect)
           contraction = self.MAX_ACTUATOR_RANGE - width
           self.txt_muscles[i].setText(format("%d mm" % contraction ))
        self.show_transform(transform) 
        #  processing_dur = int(time.time() % 20) # for testing, todo remove
        self.ui.txt_processing_dur.setText(str(processing_dur))
        rect =  self.ui.rect_dur.rect()
        rect.setWidth(processing_dur * 10)
        if processing_dur < 5:
            self.ui.rect_dur.setStyleSheet("color: rgb(85, 255, 127)")
        elif processing_dur < 10:
            self.ui.rect_dur.setStyleSheet("color: rgb(255, 170, 0)")
        else:
            self.ui.rect_dur.setStyleSheet("color: rgb(255, 0, 0)")
        self.ui.rect_dur.setFrameRect(rect)

        """
        for idx, m in enumerate(muscles):
            n = copy.copy(self.normalize(m))                       
            new_y1 = self.max_rectlen +((n+1) * self.max_rectlen * 0.125)
            _percent = int((n+1) * 50)
            #print m,n, _percent, new_y1
            x0, y0, x1, y1 = self.muscle_canvas.coords(self.muscle_rect[idx])           
            self.muscle_canvas.coords(self.muscle_rect[idx], x0, y0, x1, new_y1)
            info = "L %d is %-3dmm (%d)%% [P err%%=%d]" % (idx, int(m-200), _percent,  pressure_percent[idx])
            if _percent < -100 or _percent > 100:
                color = "red"
            else:
                color = "black"
            self.muscle_labels[idx].config(text=info, fg=color)

        pos = copy.copy(position_request)
        x = pos[0] / 10
        y = pos[1] / 10
        z = 50 - pos[2] / 10
        r = degrees(pos[3])
        p = degrees(pos[4])
        yaw = degrees(pos[5])
        #  print pos

        if cfg.SHOW_CHAIR_IMAGES:
            self.chair_img_canvas.delete(self.front_canvas_obj)
            self.chair_front_img = ImageTk.PhotoImage(self.chair_front.rotate(r))
            self.front_canvas_obj = self.chair_img_canvas.create_image(
                65 + y, z + self.muscle_canvas_height/2, image=self.chair_front_img)

            self.chair_img_canvas.delete(self.side_canvas_obj)
            self.chair_side_img = ImageTk.PhotoImage(self.chair_side.rotate(p))
            self.side_canvas_obj = self.chair_img_canvas.create_image(
                195 + x, z + self.muscle_canvas_height/2, image=self.chair_side_img)

            self.chair_img_canvas.delete(self.chair_top_img)
            self.chair_top_img = ImageTk.PhotoImage(self.chair_top.rotate(yaw))
            self.top_canvas_obj = self.chair_img_canvas.create_image(
                130, 50 + x, image=self.chair_top_img)
                
            self.draw_crosshair( self.chair_side_img, 25, 105)  
            self.draw_crosshair( self.chair_front_img, 155, 105)
            self.draw_crosshair( self.chair_top_img, 95, 20)

        info = "Orientation: X=%-4d Y=%-4d Z=%-4d  Roll=%-3d Pitch=%-3d Yaw=%-3d" % (pos[0], pos[1], pos[2], r, p, yaw)
        self.request_fields_lbl.config(text=info)
        
        self.master.update_idletasks()
        self.master.update()

                platform.show_muscles(position_request, self.actuator_lengths)
                percents = ((self.actuator_lengths -cfg.MIN_ACTUATOR_LEN ) / cfg.MAX_ACTUATOR_RANGE) * 100
                print "show muscles", position_request, percents , cfg.MAX_ACTUATOR_RANGE
                for i in range(6):
                   #self.actuator_bars[i].setValue(percents[i])
                   #self.actuator_bars[i].setWidth(percents[i])
                   pass
        """
        """
        platform.show_muscles(position_request, self.actuator_lengths)
        percents = ((self.actuator_lengths -cfg.MIN_ACTUATOR_LEN ) / cfg.MAX_ACTUATOR_RANGE) * 100
        print "show muscles", position_request, percents , cfg.MAX_ACTUATOR_RANGE
        for i in range(6):
           #self.actuator_bars[i].setValue(percents[i])
           #self.actuator_bars[i].setWidth(percents[i])
        """
        
    def normalize(self, item):
        i = 2 * (item - self.MIN_ACTUATOR_LEN) / (self.MAX_ACTUATOR_LEN - self.MIN_ACTUATOR_LEN)
        return i-1
