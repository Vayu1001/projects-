#include <Servo.h>  // Include the Servo library

// Servo objects for each servo motor
Servo LServo;    // Left servo
Servo RServo;    // Right servo
Servo HServo;    // Head servo

// Define the servo control pins
const int LS_pin = 8;    // Left servo pin
const int RS_pin = 9;    // Right servo pin
const int Hs_pin = 10;   // Head servo pin

// Array to store the received servo positions (Lservo, Rservo, Hservo)
int valsRec[3];

void setup() {
  // Initialize serial communication at 9600 baud rate
  Serial.begin(9600);

  // Attach the servos to the corresponding pins
  LServo.attach(LS_pin);
  RServo.attach(RS_pin);
  HServo.attach(Hs_pin);
}

void loop() {
  // Check if there is incoming data from the serial port
  if (Serial.available() > 0) {
    // Read the three servo positions from the serial buffer
    valsRec[0] = Serial.parseInt();  // Left servo angle
    valsRec[1] = Serial.parseInt();  // Right servo angle
    valsRec[2] = Serial.parseInt();  // Head servo angle

    // Move the servos to the received angles
    LServo.write(valsRec[0]);
    RServo.write(valsRec[1]);
    HServo.write(valsRec[2]);
  }
}
