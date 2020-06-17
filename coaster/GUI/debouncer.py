
""" debounce.py """
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

class Debounce(object):
    def __init__(self, pins, keys, callback, input_mode = 'none', edge='falling', bouncetime=50):
        self.edge = edge
        self.callback = callback
        self.pins = pins
        self.keys = keys
        self.bouncetime = float(bouncetime)/1000
        self.last_pin_val = []
        self.is_changing = []
        self.last_pin_change = [] 
        for idx, pin in enumerate(self.pins):
           if input_mode == 'pulldown':
               GPIO.setup(self.pins[idx], GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
           elif  input_mode == 'pullup':
               GPIO.setup(self.pins[idx], GPIO.IN, pull_up_down=GPIO.PUD_UP) 
           self.last_pin_val = append(GPIO.input(self.pins[idx]))
           self.last_pin_change.append(time.time)


    def service(self):
        for idx, pin in enumerate(self.pins):
            pinval = GPIO.input(pin)
            if (
                    ((pinval == 0 and self.last_pin_val[idx] == 1) and
                     (self.edge in ['falling', 'both'])) or
                    ((pinval == 1 and self.last_pin_val[idx] == 0) and
                     (self.edge in ['rising', 'both']))
            ):
                is_changing[idx] = True
                self.last_pin_val[idx] = pinval
                self.last_pin_change = time.time
            if time.time - self.last_pin_change > self.bouncetime: 
                is_changing[idx] = False
                self.callback(self.keys[idx]) 

def test(key):
    print key

if __name__ == "__main__":
    debounce = Debounce([17,18,27], ["sw 17", "sw 18", "sw 27"], test, input_mode = 'pullup' )
    while True:
        debounce.service()
        time.sleep(.1)