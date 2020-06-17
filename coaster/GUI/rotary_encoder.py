#!/usr/bin/env python

import RPi.GPIO as GPIO

class decoder:

   """Class to decode mechanical rotary encoder pulses."""

   def __init__(self, pi, gpioA, gpioB, callback):

      """
      Instantiate the class with the pi and gpios connected to
      rotary encoder contacts A and B.  The common contact
      should be connected to ground.  The callback is
      called when the rotary encoder is turned.  It takes
      one parameter which is +1 for clockwise and -1 for
      counterclockwise.
      """

      GPIO.setmode(GPIO.BCM)
      self.gpioA = gpioA
      self.gpioB = gpioB
      self.callback = callback

      self.levA = 0
      self.levB = 0

      self.lastGpio = None

      GPIO.setup(gpioA, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
      GPIO.setup(gpioB, GPIO.IN, pull_up_down=GPIO.PUD_UP) 

      GPIO.add_event_detect(gpioA, GPIO.RISING, callback=self._pulse)
      GPIO.add_event_detect(gpioB, GPIO.RISING, callback=self._pulse)
      GPIO.add_event_detect(gpioA, GPIO.FALLING, callback=self._pulse)
      GPIO.add_event_detect(gpioB, GPIO.FALLING, callback=self._pulse)


   def _pulse(self, gpio, level, tick):

      """
      Decode the rotary encoder pulse.

                   +---------+         +---------+      0
                   |         |         |         |
         A         |         |         |         |
                   |         |         |         |
         +---------+         +---------+         +----- 1

             +---------+         +---------+            0
             |         |         |         |
         B   |         |         |         |
             |         |         |         |
         ----+         +---------+         +---------+  1
      """

      if gpio == self.gpioA:
         self.levA = level
      else:
         self.levB = level;

      if gpio != self.lastGpio: # debounce
         self.lastGpio = gpio

         if   gpio == self.gpioA and level == 1:
            if self.levB == 1:
               self.callback(1)
         elif gpio == self.gpioB and level == 1:
            if self.levA == 1:
               self.callback(-1)

   def cancel(self):

      """
      Cancel the rotary encoder decoder.
      """
      GPIO.remove_event_detect( self.gpioA)
      GPIO.remove_event_detect( self.gpioB)


if __name__ == "__main__":

   import time
   import GPIO
   import rotary_encoder

   pos = 0

   def callback(way):
      global pos
      pos += way
      print("pos={}".format(pos))

   decoder = rotary_encoder.decoder(23, 24, callback)
   in = raw_input("hit enter to quit")
   decoder.cancel()


