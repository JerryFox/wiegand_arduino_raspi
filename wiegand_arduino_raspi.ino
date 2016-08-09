/*
Dahua Wiegand keypad with card reader 125 kHz
1k pullup resistors between D0, D1 and +5V
*/

#include <Wiegand.h>

const byte keylockPin = 10;
const byte monitorPin = 13;
int openMillis = 4000; // door open interval ms

#include "codes.h"


WIEGAND wg;

void setup() {
	Serial.begin(115200);  
/*
        while (!Serial) {
          ; // wait for serial port to connect. Needed for native USB
        }
*/

	wg.begin();
        pinMode(2, INPUT_PULLUP);
        pinMode(3, INPUT_PULLUP);
        pinMode(keylockPin, OUTPUT);
        digitalWrite(keylockPin, HIGH);
        pinMode(monitorPin, OUTPUT);
        digitalWrite(monitorPin, LOW); 
        listCodes(); 
        Serial.println("SETUP...");
}

byte wholeCode = false; 
String inCode = ""; 
String prefix = "";
unsigned long time = millis(); 
unsigned long beginTime = millis();

void loop() {
  // long time since last key
  if (millis() - time > 10000) {
    inCode = "";
    wholeCode = false; 
  }
  String command = readCommand(50);
  if (command != "") {
    Serial.println("<= " + command);
    if (command == "open") {
      Serial.println("demandOPEN");
      keyUnlock(keylockPin, openMillis);
    }
    else if (command.startsWith("test")) {
      testCodes(command.substring(4));
    }
  }
  if(wg.available())
  {
    if(wg.getWiegandType() == 4) {
      prefix = "k";
      time = millis();
      String numero = String(wg.getCode(),HEX);
      if (numero == "d") {
        inCode = "";
        wholeCode = false;
      }
      else {
        inCode += numero;
      }
      if (inCode.length() >= 5) {
        wholeCode = true; 
      }
    }
    if(wg.getWiegandType() == 26) {
      prefix = "c"; 
      inCode = String(wg.getCode(),HEX);
      wholeCode = true; 
    }
    //Serial.print(prefix + inCode);
    if (wholeCode) {
      String prac = "";
      prac = prefix + inCode;
      if (testCodes(prac)) {
        keyUnlock(keylockPin, openMillis);
        inCode = "";
        wholeCode = false; 
      }
    }
  }
}

void keyUnlock(byte pin, int time) {
  digitalWrite(pin, LOW); 
  digitalWrite(monitorPin, HIGH);
  delay(time); 
  // if code is in web codes too - kill open command
  while (Serial.available()) {
    byte inByte = Serial.read();
  }
  digitalWrite(pin, HIGH) ; 
  digitalWrite(monitorPin, LOW);
}

void listCodes() {
  for (int i =0; i< ARRAYSIZE; i++) { 
    Serial.print("# ");
    Serial.println(codes[i]);  
  }
}

byte testCodes(String code) {
  while (Serial.available()) {
    byte inByte = Serial.read();
  }
  byte ok = false; 
  Serial.println(code); 
  char myCode[128] = ""; //create a character array to hold the converted String
  code.toCharArray(myCode,128); //Convert the String to CharArray.
  for (int i =0; i< ARRAYSIZE; i++) {
    //Serial.print(codes[i]);
    //Serial.print("  ");
    //Serial.println(code);
    if (strcmp(codes[i], myCode) == 0) {
      ok = true;
      Serial.print("hardOPEN ");
      Serial.println(code);
      return ok;
      break;
    }  
  }
  String command = readCommand(50);
  Serial.print("<=");
  Serial.println(command); 
  if (command == "open") {
    ok = true; 
    Serial.println("softOPEN");
  }
  if (command == "service") {
    ok = false;
    wholeCode = false; 
    inCode = ""; 
  }
  return ok;
}

String readCommand(int delay) {
  String command = "";
  char inChar = 0; 
  //int delay = 200; 
  unsigned long beginTime = millis(); 
  while (inChar != 10 && millis() - beginTime < delay) {
    inChar = 0; 
    if (Serial.available()) inChar = Serial.read();
    if (inChar != 0 && inChar != 10) {
    command += inChar;
    } 
  }
  //Serial.println(command); 
  return command;
}


