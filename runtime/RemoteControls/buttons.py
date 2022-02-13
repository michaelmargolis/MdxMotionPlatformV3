
""" buttons.py """
import RPi.GPIO as GPIO
import time
import warnings


GPIO.setmode(GPIO.BCM)

class Buttons(object):
    def __init__(self, callback, bouncetime=60):
  
        self.callback = callback
        self.bouncetime = float(bouncetime)/1000
        self.pins = []
        self.keys = []
        self.edges = []
        self.last_pin_val = []
        self.is_changing = []
        self.last_pin_change = [] 
        """
        for idx, pin in enumerate(self.pins):
           if input_mode == 'pulldown':
               GPIO.setup(self.pins[idx], GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
           elif  input_mode == 'pullup':
               GPIO.setup(self.pins[idx], GPIO.IN, pull_up_down=GPIO.PUD_UP) 
           self.last_pin_val.append(GPIO.input(self.pins[idx]))
           self.last_pin_change.append(time.time())
           self.is_changing.append(False)
        """

    def append(self, pin, key, input_mode, edge):
        self.pins.append(pin)
        self.keys.append(key)
        self.edges.append(edge)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if input_mode == 'pulldown':
               GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
            elif  input_mode == 'pullup':
                   GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
        self.last_pin_val.append(GPIO.input(pin))
        self.last_pin_change.append(time.time())
        self.is_changing.append(False)

    def raw_value(self, pin):
        "returns un-debounced state"
        return ['high','low'][GPIO.input(pin)]

    def service(self):
        for idx, pin in enumerate(self.pins):
            pinval = GPIO.input(pin)
            # print idx, pinval, self.last_pin_val[idx]
            if (
                    ((pinval == 0 and self.last_pin_val[idx] == 1) and
                     (self.edges[idx] in ['falling', 'both'])) or
                    ((pinval == 1 and self.last_pin_val[idx] == 0) and
                     (self.edges[idx] in ['rising', 'both']))
            ):
                self.is_changing[idx] = True
             
                self.last_pin_change[idx] = time.time()
            self.last_pin_val[idx] = pinval
            if self.is_changing[idx] and time.time() - self.last_pin_change[idx] >= self.bouncetime: 
                self.is_changing[idx] = False
                if 'both' in self.edges[idx]:
                    keys = self.keys[idx]
                    self.callback(keys[pinval]) # 'both' requires list of two keys for low and high
                else:
                    self.callback(self.keys[idx]) 

def show(pin):
    print(key)
    print(pin, wiring_str[idx],assignment)

if __name__ == "__main__":

    dual_reset_pcb_pins = {'DISPATCH_PIN':18, 'PAUSE_PIN':15, 'RESET_PIN_1':27, 'RESET_PIN_2':23, 'ACTIVATE_PIN':24, 'ENCODER_A':4, 'ENCODER_B':14, 'ENCODER_SW_PIN':17}
    single_reset_pcb_pins = {'DISPATCH_PIN':18, 'PAUSE_PIN':17, 'RESET_PIN_1':23,  'RESET_PIN_2':23, 'ACTIVATE_PIN':22, 'ENCODER_A':3, 'ENCODER_B':4, 'ENCODER_SW_PIN':2}
    wired_switch_pins = {'DISPATCH_PIN':5, 'PAUSE_PIN':6, 'RESET_PIN_1':13,  'RESET_PIN_2':13, 'ACTIVATE_PIN':19, 'ENCODER_A':9, 'ENCODER_B':11, 'ENCODER_SW_PIN':26}
   
    rev_dual = {value: key for key, value in dual_reset_pcb_pins.items()}
    rev_single = {value: key for key, value in single_reset_pcb_pins.items()}
    rev_wired = {value: key for key, value in wired_switch_pins.items()}   
    
    wiring = (rev_dual, rev_single, rev_wired)
    wiring_str = ('dual_reset_pcb', 'single__reset_pcb', 'hand wired')

    pi_switch_pins = {'dual_reset_pcb_pins':dual_reset_pcb_pins, 'single_reset_pcb_pins':single_reset_pcb_pins, 'wired_switch_pins':wired_switch_pins}
 
    all_pins = (2,3,4,17,27,22,10,9,11,5,6,13,19,26,14,15,18,23,24,25,8,7,12,16,20,21)

    buttons = Buttons(test)
    buttons.append(21,"sw 21", 'pullup','falling')
    buttons.append(9,"sw 9", 'pullup','falling')
    buttons.append(27,["sw 27 low", "sw 27 high"], 'pullup','both')
    while True:
        buttons.service()
        time.sleep(.05)