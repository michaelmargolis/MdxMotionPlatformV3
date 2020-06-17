void setup() {
    Serial1.begin(9600);
    delay(100);
    Serial1.print('I') ;
    delay(100);
}

void loop() {
  Serial.println(Serial1.read());
  delay(100);

}
