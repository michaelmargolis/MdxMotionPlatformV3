# btn_test.py
from buttons import Buttons
import time
     
dual_reset_pcb_pins = {'DISPATCH_PIN':18, 'PAUSE_PIN':15, 'RESET_PIN_1':27, 'RESET_PIN_2':23, 'ACTIVATE_PIN':24, 'ENCODER_A':4, 'ENCODER_B':14, 'ENCODER_SW_PIN':17}
single_reset_pcb_pins = {'DISPATCH_PIN':18, 'PAUSE_PIN':17, 'RESET_PIN_1':23, 'ACTIVATE_PIN':22, 'ENCODER_A':3, 'ENCODER_B':4, 'ENCODER_SW_PIN':2}
wired_switch_pins = {'DISPATCH_PIN':5, 'PAUSE_PIN':6, 'RESET_PIN_1':13, 'ACTIVATE_PIN':19, 'ENCODER_A':9, 'ENCODER_B':11, 'ENCODER_SW_PIN':26}

pi_switch_pins = {'dual_reset_pcb_pins':dual_reset_pcb_pins, 'single_reset_pcb_pins':single_reset_pcb_pins, 'wired_switch_pins':wired_switch_pins}

rev_dual = {value: key for key, value in dual_reset_pcb_pins.items()}
rev_single = {value: key for key, value in single_reset_pcb_pins.items()}
rev_wired = {value: key for key, value in wired_switch_pins.items()}

wiring = (rev_dual, rev_single, rev_wired)
wiring_str = ('dual_reset_pcb', 'single__reset_pcb', 'hand wired')

def show(pin):
    for idx, variant in enumerate(wiring):
        try:
            assignment = variant[pin]
            if assignment:
                    print(pin, wiring_str[idx],assignment)
        except:
            pass 
    print()
    
if __name__ == "__main__":    
    all_pins = (2,3,4,17,27,22,10,9,11,5,6,13,19,26,14,15,18,23,24,25,8,7,12,16,20,21)
     
    buttons = Buttons(show)

    for pin in all_pins:
            buttons.append(pin, pin, 'pullup','falling')

    print('Press buttons on control panel to verify if they are recognized')
    print('press ztrl-z to exit')
    while True:
        buttons.service()
        time.sleep(.05)
