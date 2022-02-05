""" Local control interface"""

import sys
import time
import os
import logging

log = logging.getLogger(__name__)

if __name__ == "__main__":
    import rotary_encoder as rotary_encoder
    import buttons as buttons
else:
    import RemoteControls.rotary_encoder as rotary_encoder
    import RemoteControls.buttons as buttons



dual_reset_pcb_pins = {'DISPATCH_PIN':18, 'PAUSE_PIN':15, 'RESET_PIN_1':27, 'RESET_PIN_2':23, 'ACTIVATE_PIN':24, 'ENCODER_A':4, 'ENCODER_B':14, 'ENCODER_SW_PIN':17}
single_reset_pcb_pins = {'DISPATCH_PIN':18, 'PAUSE_PIN':17, 'RESET_PIN_1':23,  'RESET_PIN_2':23, 'ACTIVATE_PIN':22, 'ENCODER_A':3, 'ENCODER_B':4, 'ENCODER_SW_PIN':2}
wired_switch_pins = {'DISPATCH_PIN':5, 'PAUSE_PIN':6, 'RESET_PIN_1':13,  'RESET_PIN_2':13, 'ACTIVATE_PIN':19, 'ENCODER_A':9, 'ENCODER_B':11, 'ENCODER_SW_PIN':26}

pi_switch_pins = {'dual_reset_pcb_pins':dual_reset_pcb_pins, 'single_reset_pcb_pins':single_reset_pcb_pins, 'wired_switch_pins':wired_switch_pins}

class LocalControlItf(object):   # was SerialRemote(object):
    """ provide action strings associated with buttons on raspberry pi."""

    def __init__(self, actions, pin_defs):
        """ Call with dictionary of action strings, pin definitions.
 
        Keys are the strings associated with gpio pins,
        values are the functons to be called for the given key.
        """
        log.debug("Initializing Raspberry Pi Touch Control Panel with pins for %s", pin_defs)
        self.pins = pi_switch_pins[pin_defs]
        self.actions = actions
        self.decoder = rotary_encoder.decoder(pins['ENCODER_A'], pins['ENCODER_B'], self.encoder_callback)
        self.intensity = 10
        self.prev_intensity = None
        self.enc_pushed = False
        self.park_inc = 0
        self.buttons = buttons.Buttons(self.button_callback)
        self.buttons.append(pins['DISPATCH_PIN'],'dispatch', 'pullup','falling')
        self.buttons.append(pins['PAUSE_PIN'],'pause', 'pullup','falling')
        self.buttons.append(pins['RESET_PIN_1'],'reset', 'pullup','falling')
        self.buttons.append(pins['ACTIVATE_PIN'],['activate', 'deactivate'], 'pullup','both')
        self.buttons.append(pins['ENCODER_SW_PIN'],['enc_pushed', 'enc_released'], 'pullup','both')

    def encoder_callback(self, dir):
       if  self.enc_pushed == False:
           self.intensity += dir
           if self.intensity > 10:
               self.intensity = 10
           if self.intensity < 0:
               self.intensity = 0
       else:
           print("button pushed") 
           self.park_inc += dir
    
    def button_callback(self, msg):
        #  print('local control', msg)
        if msg == 'enc_pushed':
             self.enc_pushed = True
             self.actions['show_parks']('True')
        elif msg == 'enc_released':
             self.enc_pushed = False
             self.actions['show_parks']('False')
        else:
            self.actions[msg]()

    def is_activated(self):
        return self.buttons.raw_value(ACTIVATE_PIN) == 'high'

    def service(self):
        """ Poll to service button requests."""
        self.buttons.service()
        if self.prev_intensity != self.intensity:
            msg = format("intensity=%d" % (self.intensity))
            # print(msg)
            self.actions['intensity'](msg)
            self.prev_intensity = self.intensity
        if self.park_inc > 1:
            # print self.park_inc
            self.actions['scroll_parks']('1')
            self.park_inc = 0
        elif self.park_inc < -1:
            self.actions['scroll_parks']('-1')
            self.park_inc = 0


if __name__ == "__main__":
    def detected_remote(info):
        print(info)
    def activate():
        print("activate")
    def deactivate():
        print("deactivate") 
    def pause():
        print("pause")
    def dispatch():
        print("dispatch")
    def reset_vr():
        print("reset vr")
    def deactivate():
        print("deactivate")
    def emergency_stop():
        print("estop")
    def set_intensity(intensity):
        print("intensity ", intensity)
            
    actions = {'detected remote': detected_remote, 'activate': activate,
               'deactivate': deactivate, 'pause': pause, 'dispatch': dispatch,
               'reset': reset_vr, 'emergency_stop': emergency_stop, 'intensity' : set_intensity}
 
    local_control = LocalControlItf(actions)
    while True:
         local_control.service()
         time.sleep(.1)
