// FanController

#include <Servo.h>

const int minThrottle = 1000;
const int maxThrottle = 2000;

Servo fanEsc; 

const int escPin = 2;

void setup() {
  Serial.begin(57600);
  Serial.println("fan controller");
  fanEsc.attach(escPin);
  fanEsc.writeMicroseconds(minThrottle); 
  delay(4000); // wait for fan esc to arm
  Serial.println("ready");
}

unsigned long previousMillis = 0;  
const long interval = 900;
int power = 0;

void loop() {
  if (Serial.available()) {
     if(Serial.find("power")) {
         power = Serial.parseInt();
         power  = constrain(power, 0,100); 
         int pw = map(power,0,100, minThrottle,maxThrottle);
         fanEsc.writeMicroseconds(pw);       
         Serial.print("fan:"); Serial.println(power);
     }
   }
   unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    Serial.print("fan:"); Serial.println(power);
  }
}
