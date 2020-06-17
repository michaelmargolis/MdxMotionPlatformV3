

 
const int numReadings = 4;

int readings[numReadings];      // the readings from the analog input
int readIndex = 0;              // the index of the current reading
int total = 0;                  // the running total
int average = 0;                // the average

void setup() {
  Serial.begin(9600);
  Serial2.begin(9600);
}

void loop() {
  int distance = getDistance();
  total = total - readings[readIndex];
  readings[readIndex] = distance;
  total = total + readings[readIndex];
  if(readIndex++ >= numReadings)
      readIndex =0;
  int min = 10000;
  int max = 0;    
  for( int i=0; i < numReadings; i++){
    if(readings[i] < min) min = readings[i];
    if(readings[i] > max) max = readings[i];
  }  
  Serial.print(distance); 
  Serial.print(", min="); Serial.print(min);
  Serial.print(", max="); Serial.print(max);
  Serial.print(", delta="); Serial.println(max-min);   
}

int getDistance() {
  static byte buffer[8];
  memset(buffer, '\0', sizeof(buffer));
  Serial2.readBytesUntil('\n', buffer, sizeof(buffer));
  int distance = atoi(buffer); 
  return distance;
}
