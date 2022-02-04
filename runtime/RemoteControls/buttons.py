
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
    try:
        print(pin, pin_defs[pin])
    except:
        print(pin)


if __name__ == "__main__":
    all_pins = [2,3,4,17,27,22,10,9,11,5,6,13,19,26,18,23,24,25,8,7,12,16,20,21]

    pin_defs = {18:'pcb_DISPATCH_PIN', 17:'pcb_PAUSE_PIN',23:'pcb_RESET_PIN', 22:'pcb_ACTIVATE_PIN', \
               3:'pcb_ENCODER_A', 4:'pcb_ENCODER_B', 2:'pcb_ENCODER_SW_PIN', \
               5:'wired_DISPATCH_PIN', 6:'wired_PAUSE_PIN', 13:'wired_RESET_PIN', 19:'wired_ACTIVATE_PIN',\
               9:'wired_ENCODER_A', 11:'wired_ENCODER_B', 26:'wired_ENCODER_SW_PIN' }
    
    buttons = Buttons(show)
    for pin in all_pins:        
        buttons.append(pin, str(pin), 'pullup', 'falling')

    while True:
        buttons.service()
        time.sleep(.05)