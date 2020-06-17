/*
 * UDP test
 * This sketch receives UDP message strings, prints them to the serial port
 *
 */

#include <SPI.h>         // needed for Arduino versions later than 0018
#include <Ethernet.h>
#include <EthernetUdp.h> // Arduino 1.0 UDP library

#define UDP_TX_PACKET_MAX_SIZE 100 //increase UDP size


byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED }; // MAC address to use
byte ip[] = {192, 168, 1, 177 };    // Arduino's IP address

unsigned int localPort = 995;      // Festo easyip port
int propPin = 7;

// buffers for receiving and sending data
char packetBuffer[UDP_TX_PACKET_MAX_SIZE]; //buffer to hold incoming packet,
char replyBuffer[] = "acknowledged";       // a string to send back

extern "C" {
#include <inttypes.h>
#include <stdio.h>  // BAPDEBUG
}

#include "HardwareSerial.h" 

static char _buf[100];
#define printf(...)             \
  do {              \
    sprintf(_buf, __VA_ARGS__); Serial.write(_buf); \
  } while (0)


// A UDP instance to let us send and receive packets over UDP
EthernetUDP Udp;

void setup() {
    // start the Ethernet and UDP:
  Ethernet.begin(mac,ip);
  Udp.begin(localPort);
  Serial.begin(9600);
  pinMode(propPin, OUTPUT);
  digitalWrite(propPin, LOW);
}

void loop() {
  // if there's data available, read a packet
  int packetSize =  Udp.parsePacket(); 
  if(packetSize)
  {
    Serial.print("\nReceived packet of size ");
    Serial.println(packetSize);

    // read packet into packetBuffer and get sender's IP addr and port number
    Udp.read(packetBuffer,UDP_TX_PACKET_MAX_SIZE);
    /*
    Serial.println("Contents:");
    for(int i=0; i < packetSize; i++) {
        Serial.print(byte(packetBuffer[i]), HEX);
        Serial.print(",");
    }        
    Serial.println();
    */
    
    byte flag =  packetBuffer[7];
    byte count = packetBuffer[8];
    printf("flag = %d, count = %d\n", flag, count);
    if(flag == 1 && (count == 6 || count == 7)) {
      int *values  = (int*)&packetBuffer[20];
      printf("%d,%d", flag, count);
      for(int i=0; i < count; i++) 
          printf(",%d", values[i]);    
      printf("\n");
      digitalWrite(propPin, values[6]);
    }
    /*
    // send a string back to the sender
    Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
    Udp.write(replyBuffer);
    Udp.endPacket();
    */
  }
  delay(10);
}
