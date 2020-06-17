""" output_gui
Copyright Michael Margolis, Middlesex University 2019; see LICENSE for software rights.

display muscle lengths and platform orientation
"""

SHOW_CHAIR_IMAGES = False

from output_gui_defs import *

import copy
from math import degrees
import platform_config as cfg

class OutputGui(object):

    def init_gui(self, frame, MIN_ACTUATOR_LEN , MAX_ACTUATOR_RANGE):
        self.ui = Ui_Frame()
        self.ui.setupUi(frame)
        self.MIN_ACTUATOR_LEN = MIN_ACTUATOR_LEN
        self.MAX_ACTUATOR_RANGE = MAX_ACTUATOR_RANGE
        # self.actuator_bars = [self.ui.pb_0,self.ui.pb_1,self.ui.pb_2,self.ui.pb_3,self.ui.pb_4,self.ui.pb_5]
        self.actuator_bars = [self.ui.muscle_0,self.ui.muscle_1,self.ui.muscle_2,self.ui.muscle_3,self.ui.muscle_4,self.ui.muscle_5]
        self.txt_muscles = [self.ui.txt_muscle_0,self.ui.txt_muscle_1,self.ui.txt_muscle_2,self.ui.txt_muscle_3,self.ui.txt_muscle_4,self.ui.txt_muscle_5]

        
        """
        info_frame = tk.Frame(master, relief=tk.SUNKEN, borderwidth=1)
        info_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.request_fields_lbl = tk.Label(info_frame, text="request fields", anchor=tk.W, font="consolas")

        self.request_fields_lbl.pack(side=tk.LEFT, fill=tk.X)
        output_frame = tk.Frame(master)
        output_frame.pack(side=tk.LEFT)
        self.muscle_canvas_height = 250
        self.muscle_canvas = tk.Canvas(output_frame, width=100, height=self.muscle_canvas_height)
        self.muscle_canvas.pack()

        margin = int(self.muscle_canvas_height / 10)
        self.max_rectlen = self.muscle_canvas_height - 2.5 * margin
        width = 5
        background = self.muscle_canvas["background"]
        self.muscle_rect = []
        for idx in range(6):
            x0 = 16 + idx * 16
            y1 = self.max_rectlen
            r = self.muscle_canvas.create_rectangle(x0, margin,
                x0+width, y1, fill="black")
            self.muscle_rect.append(r)

        muscle_info_frame = tk.Frame(master)
        muscle_info_frame.pack(side=tk.LEFT)
        self.muscle_labels = []
        for i in range(6):
            lbl = tk.Label(muscle_info_frame, text="Actuator" + str(i), anchor=tk.W, relief=tk.SUNKEN)
            #              font="-weight bold", anchor=tk.W)
            lbl.pack(side=tk.TOP, fill=tk.X, padx=(20, 0), pady=(6, 6))
            self.muscle_labels.append(lbl)

        self.chair_img_canvas = tk.Canvas(master, width=260)
        self.chair_img_canvas.pack(side=tk.RIGHT)
        if cfg.SHOW_CHAIR_IMAGES:
            self.chair_front = Image.open("images/ChairFrontViewSmaller.png")

            self.chair_front_img = ImageTk.PhotoImage(self.chair_front.rotate(0))
            self.front_canvas_obj = self.chair_img_canvas.create_image(
                    195, 40 + self.muscle_canvas_height/2, image=self.chair_front_img)

            self.chair_side = Image.open("images/ChairSideViewSmaller.png")
            self.chair_side_img = ImageTk.PhotoImage(self.chair_side.rotate(0))
            self.side_canvas_obj = self.chair_img_canvas.create_image(
                    65, 40 + self.muscle_canvas_height/2, image=self.chair_side_img)

            self.chair_top = Image.open("images/ChairTopViewSmaller.png")
            self.chair_top_img = ImageTk.PhotoImage(self.chair_top.rotate(0))
            self.top_canvas_obj = self.chair_img_canvas.create_image(
                    130, 50, image=self.chair_top_img)
            
            self.draw_crosshair( self.chair_side_img, 25, 105)  
            self.draw_crosshair( self.chair_front_img, 155, 105)
            self.draw_crosshair( self.chair_top_img, 95, 20)
        """    
        
    def draw_crosshair(self, obj, x, y):
        w =  obj.width()
        h =  obj.height()  
        """           
        self.chair_img_canvas.create_line(x + w/2, y, x + w/2, y + h, dash=(4, 2))
        self.chair_img_canvas.create_line(x, y+h/2, x + w, y+h/2, dash=(4, 2))
        """
        
    def show_muscles(self, position_request, muscles):  # was passing  pressure_percent
        for i in range(6):
           rect =  self.actuator_bars[i].rect()
           width = muscles[i] 
           rect.setWidth(width)
           self.actuator_bars[i].setFrameRect(rect)
           contraction = self.MAX_ACTUATOR_RANGE - width
           self.txt_muscles[i].setText(format("%d mm" % contraction ))
        r = position_request
        # trans_str = format("%2d, %2d, %2d" % (r[0], r[1], r[2]))
        trans_str = "{:<4}, {:<4}, {:<4}".format(int(r[0]), int(r[1]), int(r[2]))
        #rot_str = format("%0.2f, %0.2f, %0.2f" % (r[3], r[4], r[5]))
        rot_str = "{:3.2f}, {:3.2f}, {:3.2f}".format(r[3], r[4], r[5])
        self.ui.txt_translation.setText(trans_str)
        self.ui.txt_rotation.setText(rot_str)
        # print muscles
  

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
