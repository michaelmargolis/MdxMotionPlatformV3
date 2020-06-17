import sys
# import scipy.io as sio
import numpy as np
import cv2
import os
import time
import math
import copy

from gui import *
import traceback
import logging as log
import logging.handlers

sys.path.insert(0, '../output')
from kinematicsV2 import Kinematics
from configNextgen import *
#  from ConfigV3 import *
import d_to_p
import muscle_output

sys.path.insert(0, '../common')
from dynamics import Dynamics
from serialSensors import SerialContainer, Encoder, ServoModel
import serial_defaults


class Plot(object):
    def __init__(self, plot_widget, data, plotNames, plotColors):
        print "todo in plot, only pass active data slice"
        self.pwt = plot_widget
        self.names = plotNames
        self.data = data
        self.chart_width = 120
        self.colors = plotColors
        self.pwt.setAntialiasing(True)
        # self.ui.plotWidget.setRange(yRange=[-1,1])
        self.pwt.setYRange(-1,1)
        self.pwt.hideAxis('left')
        # self.ui.plotWidget.hideAxis('bottom')
        #self.pwt.setBackground((230,230,230))
        self.pwt.setBackground((30,30,30))
        self.vline = None
        self.end_frame = None


    def plot(self, frame):
        # print "in plot", frame
        self.frame = frame
        if frame  > self.chart_width/2:
            start_frame = frame - self.chart_width/2
        else:
            start_frame = 0
        self.end_frame = start_frame + self.chart_width
        if self.end_frame > len(self.data):
            self.end_frame = len(self.data)

        self.pwt.clear()
        #vLine = pg.InfiniteLine(angle=90, movable=False)
        # self.ui.plotwidget.addItem(vLine, ignoreBounds=True)
        # self.ui.plotWidget.addLegend()
        x = np.arange(start_frame, self.end_frame)
        # print self.telemetry[0:frame,2]
        for i in range(6):
            self.pwt.plot(x,self.data[start_frame:self.end_frame,i+2],pen=self.colors[i][0],)
        self.vline = self.pwt.addLine(x=frame, movable=False)


    def set_cursor(self, frame):
        if self.end_frame == None or frame >= self.end_frame:
            self.plot(frame)
        else:
            if self.vline:
                self.vline.setValue(frame)

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.centralwidget.setStyleSheet("color: gray; background-color: black;")  
        
        self.cap = None
        self.t_frame = -1
        self.fps = 0
        self.telemetry = None
        np.set_printoptions(precision=3, suppress = True)

        self.delta_timer = QtCore.QTimer(self) # timer for distance deltas
        self.delta_timer.timeout.connect(self.distance_delta_update)

        # configures
        self.configure_signals()
        self.configure_buttons()
        self.configure_defaults()
        self.configure_labels()
        self.draw_chair_frame()
        self.configure_kinematics()
        self.configure_festo()
        self.configure_serial()


    def configure_signals(self):
        self.ui.btn_open.clicked.connect(self.open)
        self.ui.btn_serial_connect.clicked.connect(self.serial_connect)
        self.ui.btn_play.clicked.connect(self.play)
        self.ui.btn_pause.clicked.connect(self.pause)
        self.ui.btn_goto_frame.clicked.connect(self.sync_frame)
        self.ui.btn_goto_time.clicked.connect(self.sync_time)
        self.ui.btn_fwd.clicked.connect(self.forward)
        self.ui.btn_rev.clicked.connect(self.back)
        self.ui.sld_course_pos.valueChanged.connect(self.course_pos)
        self.ui.btn_load_adjust.clicked.connect(self.run_lookup)
        self.ui.chk_delta_capture.stateChanged.connect(self.delta_capture_state_changed)
        
    def configure_defaults(self):
        videos = [f.split('.')[0] for f in os.listdir(os.getcwd()) if f.endswith('.' + 'avi')]
        self.ui.cmb_video_fname.addItems(videos)
        self.ui.txt_intensity.setText("0.5")
        #telemetry combo
        # telemetry = [f.split('.')[0] for f in os.listdir(os.getcwd()) if f.endswith('.' + 'tlm')]
        #self.ui.cmb_telemetry.addItems(telemetry)
        
    def configure_buttons(self):
        self.ui.btn_open.setStyleSheet(" background-color:#303030;\n") 
        self.ui.btn_serial_connect.setStyleSheet(" background-color: #303030;\n")
        self.ui.btn_play.setStyleSheet(" background-color: #303030;\n") 
        self.ui.btn_pause.setStyleSheet(" background-color: #303030;\n") 
        self.ui.btn_goto_frame.setStyleSheet(" background-color: #303030;\n")
        self.ui.btn_goto_time.setStyleSheet(" background-color: #303030;\n") 
        self.ui.btn_fwd.setStyleSheet(" background-color: #303030;\n")
        self.ui.btn_rev.setStyleSheet(" background-color: #303030;\n")
        self.ui.btn_load_adjust.setStyleSheet(" background-color: #303030;\n")
        self.ui.cmb_video_fname.setStyleSheet(" background-color: #303030;\n")
        self.ui.gb_adjust.setStyleSheet(" background-color: #d0d0d0;\n")

    def configure_labels(self):
        self.tlm_labels = [self.ui.lbl_x, self.ui.lbl_y, self.ui.lbl_z, 
                             self.ui.lbl_roll, self.ui.lbl_pitch, self.ui.lbl_yaw] 

    def configure_kinematics(self):
        self.k = Kinematics()
        cfg = PlatformConfig()

        cfg.calculate_coords()
        # self.telemetry = Telemetry(self.telemetry_cb, cfg.limits_1dof)
        self.k.set_geometry( cfg.BASE_POS, cfg.PLATFORM_POS)
        if cfg.PLATFORM_TYPE == "SLIDER":
            self.k.set_slider_params(cfg.joint_min_offset, cfg.joint_max_offset, cfg.strut_length,  cfg.slider_angles)
        
        self.DtoP = d_to_p.D_to_P(200) # argument is max distance 
        self.dynam = Dynamics()
        self.dynam.begin(cfg.limits_1dof,"shape.cfg")

    def configure_serial(self):
        self.encoder = SerialContainer(Encoder(), self.ui.cmb_encoder_port, "encoder", self.ui.lbl_encoders, 115200)
        self.model = SerialContainer(ServoModel(), self.ui.cmb_model_port, "model", self.ui.lbl_model, 57600)

        ports = self.encoder.sp.get_ports()
        log.info("serial ports: %s", [str(p) for p in ports])
        ports.append("Ignore")
        self.open_ports = 0
        self.set_combo_default(self.encoder, ports)
        self.set_combo_default(self.model, ports)
        self.serial_connect() # auto connect

    def set_combo_default(self, ser, ports):
        ser.combo.clear()
        ser.combo.addItems(ports)
        if ser.desc in serial_defaults.dict:
            port = serial_defaults.dict[ser.desc]
            # print ser.desc, "port is ", port
            index = ser.combo.findText(port, QtCore.Qt.MatchFixedString)
            if index >= 0:
                ser.combo.setCurrentIndex(index)
            else:
                ser.combo.setCurrentIndex(ser.combo.count() - 1)
        else:
            ser.combo.setCurrentIndex(ser.combo.count() - 1)

    def configure_festo(self):    
        self.muscle_output = muscle_output.MuscleOutput()  
        self.muscle_output.poll_pressures = False # enable background polling of actual pressures
        self.xyzrpy = [0,0,0,0,0,0]
        if self.DtoP.load_DtoP('..\output\DtoP.csv'):
            log.info("Loaded %d rows of distance to pressure files ", self.DtoP.rows)
            self.muscle_output.set_d_to_p_curves(self.DtoP.d_to_p_up, self.DtoP.d_to_p_down) # pass curves to platform module
        else:
            log.error("Unable to read distance to pressure files")
 
    def run_lookup(self):
        # find closest curves for each muscle at the current load
        up_pressure = 3000
        down_pressure = 2000
        dur = 2

        self.muscle_output.slow_pressure_move(0, up_pressure, dur)
        time.sleep(.5)
        encoder_data,timestamp = self.encoder.sp.read()
        print "TODO, using hard coded encoder data"
        encoder_data = np.array([123,125,127,129,133,136])
        self.DtoP.set_DtoP_index(up_pressure, encoder_data, 'up' )
        # self.ui.txt_up_index.setText(str(self.DtoP.up_curve_idx))
 
        self.muscle_output.slow_pressure_move(up_pressure, down_pressure, dur/2)
        time.sleep(.5)
        encoder_data,timestamp = self.encoder.sp.read()
        encoder_data = np.array([98,100,102,104, 98,106])
        self.DtoP.set_DtoP_index(down_pressure, encoder_data, 'down' )
        # self.ui.txt_down_index.setText(str(self.DtoP.down_curve_idx))
        self.muscle_output.set_d_to_p_indices(self.DtoP.up_curve_idx, self.DtoP.down_curve_idx)
        self.ui.gb_adjust.setStyleSheet(" background-color: 'black';\n")

    def draw_chair_frame(self):
        pass
        """
        painter = QtGui.QPainter(self.ui.lbl_chairs.pixmap())
        painter.begin(self)
        painter.drawLine(10, 10, 100, 200)
        painter.end()
        """
        
    def nextFrameSlot(self):
        ret, frame = self.cap.read()
        if ret: 
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)
            pix = QtGui.QPixmap.fromImage(img)
            self.ui.lbl_video_frame.setPixmap(pix)
            
            time = self.cap.get(cv2.CAP_PROP_POS_MSEC) *.001
            frame = self.frame_from_time(time)
            if frame != self.t_frame:
                self.show_telemetry(frame)
                self.plt.set_cursor(frame)
            self.ui.txt_time.setText(format("%.2f" % time)) # this writes the video time
        
    def goto_frame(self, frame):
        if frame < len(self.telemetry):
            time = self.telemetry[frame][0]
            # print ", in goto frame, new frame=", frame, "telem time=",time,
            # self.ui.txt_time.setText(format("%.2f" % self.telemetry[frame][0]))
            self.goto_time(time)
        else:
            print "cant goto frame", frame

    def sync_frame(self):
        frame = int(self.ui.txt_frame.text())
        self.goto_frame(frame)
 
    def goto_time(self, time):
        ret = self.cap.set(cv2.CAP_PROP_POS_MSEC, time*1000)
        # print "goto time returned", ret, time*1000
        frame = self.frame_from_time(time) 
        # print "in goto time, frame from time=", frame,"t_frame=",self.t_frame,
        if frame != self.t_frame:
            self.show_telemetry(frame)
        self.nextFrameSlot()  
        # print self.telemetry[self.t_frame]
        # self.ui.txt_frame.setText(str(self.t_frame))
        self.plt.plot(frame)
        
    def sync_time(self):
        time = float(self.ui.txt_time.text())
        self.goto_time(time)

    def forward(self):
        if self.t_frame < self.telemetry.shape[0]:
            # print "going from", self.t_frame, "to",
            self.goto_frame(self.t_frame+1)

    def back(self):
        if self.t_frame > 0:
            self.goto_frame(self.t_frame-1)

    def course_pos(self):
        percent = self.sender().value()
        if self.cap != None:
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames > 0:
                frame = int(percent * total_frames *.01)
                frame = int(frame / (self.fps/20))
                self.ui.txt_frame.setText(str(frame))
    
    def frame_from_time(self, _time):
        #returns the telemetry frame closest to the given time
        frame = (np.abs(self.telemetry[:,0]-_time)).argmin()
        return frame
        # print time, frame, self.telemetry[frame][0]

    def open(self):
        fname = str(self.ui.cmb_video_fname.currentText()) 
        if len(fname) < 2:
            path =  "M:\\mdx\\nl2_video\\"
            fname = "mdx_coaster"
        else:
            path=""
        self.cap = cv2.VideoCapture(path+fname+'.avi')
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.ui.txt_fps.setText(str(self.fps))
        log.info("opened %s, video fps = %d", fname, self.fps)
        self.telemetry = np.loadtxt(fname+'.csv', delimiter = ',') 
        log.info("opened %d telemetry records", self.telemetry.shape[0])
        if self.telemetry[0][0] != 0:
            # this sequences elapsed times to start at 0
            self.telemetry[:,0] = [x-self.telemetry[0][0] for x in self.telemetry[:,0]]

        """
        deltas = [0]
        headings = self.telemetry[:,8]
        for idx, h in enumerate(headings):
            if idx > 0:
                prev = headings[idx-1] 
                deltas.append(min(h-prev, h-prev+2*math.pi, h-prev-2*math.pi, key=abs))            
        self.telemetry[:,8] = deltas
        np.savetxt("t.csv",self.telemetry, delimiter = ',',fmt='%0.3f'  )
        """


        plot_names = ['X','y','z','Roll','Pitch','Yaw']
        plot_colors = ['cyan','yellow','white','blue','green','red']
        for idx, lbl in enumerate(self.tlm_labels):
            lbl.setStyleSheet(format("background-color:%s;" %  plot_colors[idx]))
        self.plt = Plot( self.ui.plotWidget, self.telemetry, plot_names, plot_colors )
        self.nextFrameSlot()

    def serial_connect(self):
        if self.open_ports > 0:
            self.close_port(self.encoder)
            self.close_port(self.model)
            self.open_ports =0
            self.ui.btn_serial_connect.setText("    Connect    ")
        else:
            self.open_port(self.encoder)
            self.open_port(self.model)
            if self.open_ports > 0:
                self.ui.btn_serial_connect.setText("  Disconnect  ")
                if self.model.sp.is_open():
                    self.muscle_output.set_echo_method(self.echo_to_model)

    def open_port(self, ser): 
        if ser.sp.is_open():
            self.disconnect(ser.sp)
            ser.label.setStyleSheet('QLabel  {color: gray;}')
        else:
            port = str(ser.combo.currentText())
            if 0 < len(port) and port != "Ignore":
                if ser.sp.open_port(port, ser.baud):
                    ser.label.setStyleSheet('QLabel  {color: green;}')
                    #print "opened", ser.desc, "serial port"
                    log.info("opened serial %s on %s", ser.desc, port)
                    self.open_ports += 1
                else:
                    log.error("serial port %s is not available", ser.desc)
                    #print ser.desc, "port is not available"
            else:
                #print ser.desc, "port was not opened"
                log.error("serial port %s was not opened", ser.desc)

    def close_port(self, ser):
        ser.label.setStyleSheet('QLabel  {color: gray;}')
        if ser.sp.is_open():
            ser.sp.close_port()

    def echo_to_model(self, percents):
        if self.model.sp.is_open():
            msg = 'm,' + ','.join(map(str, percents)) + '\n'
            self.model.sp.write( msg)
            print "sending msg to servos", msg

    def delta_capture_state_changed(self, int):
        if self.ui.chk_delta_capture.isChecked():
            fname = "distance_deltas.csv"
            self.delta_file =  open(fname, 'a')
            if  self.delta_file.closed:
                print "unable to open", fname
            else:
                print "opened", fname
                encoder_data,timestamp = self.encoder.sp.read()
                if encoder_data == None:
                    print "no encoder data, has the port been started?"
                else:
                    if self.muscle_output.up_indices == None:
                        print "muscle curve files have not been loaded and calibrated"
                    else:
                        self.delta_timer.start(50)
        else:
            self.delta_timer.stop()
            self.delta_file.close()
            

    def distance_delta_update(self):
        if  self.delta_file.closed:
            pass
        else:
           if self.muscle_output.distances:
                encoder_data,timestamp = self.encoder.sp.read()
                if encoder_data:
                     encoder_data = map(int, encoder_data)
                     delta = [e-d for e,d in zip(encoder_data, self.muscle_output.distances)]
                     data = ','.join(map(str, self.muscle_output.distances)) + ","  + ','.join(map(str, delta)) + "\n"
                     self.delta_file.write(data)
                else:
                    print "no encoder data"

    def show_telemetry(self, frame):
        if len(self.telemetry) >= frame:
            self.ui.txt_frame.setText(format("%d" % frame))
            self.t_frame = frame
            fr = self.telemetry[frame] # read frame data into fr 
            # print fr
            self.ui.txt_time.setText(format("%.2f" % fr[0]))
            self.ui.txt_speed.setText(format("%.2f" % fr[1]))
            self.ui.txt_x.setText(format("%.3f" % fr[2]))
            self.ui.txt_y.setText(format("%.3f" % fr[3]))
            self.ui.txt_z.setText(format("%.3f" % fr[4]))
            self.ui.txt_roll.setText(format("%.3f" % fr[5]))
            self.ui.txt_pitch.setText(format("%.3f" % fr[6]))
            self.ui.txt_yaw.setText(format("%.3f" % fr[7]))
            self.ui.txt_heading.setText(format("%.1f" % (180+fr[8]*57.2958)))
            self.ui.txt_ax.setText(format("%.3f" % fr[9]))
            self.ui.txt_ay.setText(format("%.3f" % fr[10]))
            self.ui.txt_az.setText(format("%.3f" % fr[11]))
            self.show_chair()
            xyzrpy = copy.deepcopy(fr[2:8])
            scale = 16
            xyzrpy[0] *= scale
            xyzrpy[1] *= scale
            xyzrpy[2] *= scale
            xyzrpy[3] *=-1
            xyzrpy[4] *=1
            xyzrpy[5] *=-1
            print xyzrpy
            self.k.set_intensity(float(self.ui.txt_intensity.text()))
            percents = self.k.actuator_percents(xyzrpy)
            if self.muscle_output.up_indices == None:
                print "muscle curve files have not been loaded and calibrated"
            else:
                self.muscle_output.move_percent(percents) 

        else:
           print "frame", frame, "not available"

    def play(self):
        self.t_frame = -1  # force update of telemetry
        self.frame_timer = QtCore.QTimer()
        self.frame_timer.timeout.connect(self.nextFrameSlot)
        self.fps = float(self.ui.txt_fps.text())
        self.frame_timer.start( 1000.0/self.fps) 
     
    def pause(self):
        print "pause"
        self.frame_timer.stop()
        self.plt.plot(self.t_frame)
        self.k.dump() # save kinematics dbg to file


    def show_chair(self):
        pixmap = QtGui.QPixmap('TopView1.png')
        #self.ui.lbl_chair_top.setPixmap(pixmap)
        rotation = 180- (self.telemetry[self.t_frame][7] * 20) # convert norm to degrees
        transform = QtGui.QTransform().rotate(rotation)
        pixmap = pixmap.transformed(transform, QtCore.Qt.SmoothTransformation)   
        self.ui.lbl_chair_top.setPixmap(pixmap)

        #self.resize(pixmap.width(),pixmap.height())

def start_logging(level):
    log_format = log.Formatter('%(asctime)s,%(levelname)s,%(message)s')
    logger = log.getLogger()
    logger.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler("ocv.log", maxBytes=(10240 * 5), backupCount=2)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    console_handler = log.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
if __name__ == '__main__':
    # multiprocessing.freeze_support()
    start_logging(log.INFO)
    log.info("Starting OCV player")
    log.info("Python: %s", sys.version[0:5])
    app = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.exec_() #mm added underscore
    log.info("Finishing OCV player")
    log.shutdown()
    win.close()
    app.exit()  
    sys.exit()
    

while(cap.isOpened()):
    ret, frame = cap.read()

    #  gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # cv2.imshow('frame',gray)
    cv2.imshow('frame',frame)
    f += 1
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    print "frame", f, f/60
cap.release()
cv2.destroyAllWindows()