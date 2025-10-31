/*
  Porton.ino
  Sketch mejorado para control de portón con:
    - Servo (miServo)
    - Sensor PIR
    - Sensor de distancia HC-SR04
    - LCD I2C (LiquidCrystal_I2C)
    - Comunicación Bluetooth (dos variantes: Serial1 y SoftwareSerial)

  Instrucciones:
  - Si tu placa tiene Serial1 (Arduino Mega, Due, etc.) usa la VARIANTE A (descomentar VARIANTE_A define).
  - Si usas Arduino Uno/Nano, usa la VARIANTE B (SoftwareSerial) y ajusta los pines RX/TX.
  - Envía comandos por Bluetooth como: 90\n (número seguido de newline). El sketch responderá con "OK <pos>".
*/

// --- CONFIG: elige VARIANTE_A (Serial1) o VARIANTE_B (SoftwareSerial)
#define VARIANTE_A // Comentaa esta línea si quieres usar SoftwareSerial (VARIANTE_B)

#include <Servo.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#ifndef VARIANTE_A
#include <SoftwareSerial.h>
#endif

// --- Config Servo ---
Servo miServo;
const int pinServo = 9;
int posicionActual = 0;
const int delayMovimiento = 20; // ms entre pasos

// --- PIR ---
const int pinPIR = 2;
bool hayMovimiento = false;
unsigned long lastPIRChange = 0;
const unsigned long pirDebounce = 200;

// --- HC-SR04 ---
const int pinTrig = 3;
const int pinEcho = 4;
unsigned long duracion = 0;
int distancia = 0;
const unsigned long pulseTimeout = 30000UL; // microsegundos

// --- LCD I2C ---
LiquidCrystal_I2C lcd(0x27, 16, 2); // Cambia a 0x3F si tu módulo es diferente

#ifndef VARIANTE_A
// --- SoftwareSerial (Uno/Nano) ---
// Ajusta pines RX/TX para tu conexión al módulo BT
const int BT_RX = 10; // Arduino RX <= TX del módulo
const int BT_TX = 11; // Arduino TX => RX del módulo
SoftwareSerial btSerial(BT_RX, BT_TX);
#endif

// Límites servo
const int ANGULO_MIN = 0;
const int ANGULO_MAX = 180;
const int POS_ABIERTO = 90;  // ajustar según montaje
const int POS_CERRADO = 0;

String inputBuffer = "";

void setup() {
  Serial.begin(9600);
#ifndef VARIANTE_A
  btSerial.begin(9600);
  Serial.println("Usando SoftwareSerial (VARIANTE_B) para Bluetooth");
#else
  Serial1.begin(9600); // para placas con Serial1
  Serial.println("Usando Serial1 (VARIANTE_A) para Bluetooth");
#endif

  miServo.attach(pinServo);
  posicionActual = POS_CERRADO;
  miServo.write(posicionActual);

  pinMode(pinPIR, INPUT);
  pinMode(pinTrig, OUTPUT);
  pinMode(pinEcho, INPUT);

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0,0);
  lcd.print("Sistema PORTON");
  lcd.setCursor(0,1);
  lcd.print("Iniciando...");
  delay(1000);
  lcd.clear();

  Serial.println("Setup completo.");
}

void loop() {
  // HC-SR04
  digitalWrite(pinTrig, LOW);
  delayMicroseconds(2);
  digitalWrite(pinTrig, HIGH);
  delayMicroseconds(10);
  digitalWrite(pinTrig, LOW);

  duracion = pulseIn(pinEcho, HIGH, pulseTimeout);
  if (duracion == 0) distancia = -1;
  else distancia = (int)(duracion * 0.034 / 2);

  // PIR con debounce
  bool estadoPIR = digitalRead(pinPIR);
  if (estadoPIR != hayMovimiento) {
    unsigned long ahora = millis();
    if (ahora - lastPIRChange > pirDebounce) {
      hayMovimiento = estadoPIR;
      lastPIRChange = ahora;
    }
  }

  // Actualizar LCD
  lcd.setCursor(0,0);
  lcd.print("Dist: ");
  if (distancia < 0) {
    lcd.print("---   ");
  } else {
    lcd.print(distancia);
    lcd.print(" cm ");
  }

  lcd.setCursor(0,1);
  lcd.print("Movim: ");
  if (hayMovimiento) lcd.print("DETECTADO ");
  else lcd.print("NO        ");

  // Leer Bluetooth
#ifndef VARIANTE_A
  while (btSerial.available() > 0) {
    char c = (char)btSerial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      processCommand(inputBuffer, true);
      inputBuffer = "";
    } else {
      inputBuffer += c;
      if (inputBuffer.length() > 20) inputBuffer = inputBuffer.substring(inputBuffer.length() - 20);
    }
  }
#else
  while (Serial1.available() > 0) {
    char c = (char)Serial1.read();
    if (c == '\r') continue;
    if (c == '\n') {
      processCommand(inputBuffer, false);
      inputBuffer = "";
    } else {
      inputBuffer += c;
      if (inputBuffer.length() > 20) inputBuffer = inputBuffer.substring(inputBuffer.length() - 20);
    }
  }
#endif

  delay(50);
}

void processCommand(String cmd, bool usingSoftwareSerial) {
  cmd.trim();
  if (cmd.length() == 0) return;

  Serial.print("Comando recibido: '");
  Serial.print(cmd);
  Serial.println("'");

  int objetivo = cmd.toInt();

  if (objetivo < ANGULO_MIN) objetivo = ANGULO_MIN;
  if (objetivo > ANGULO_MAX) objetivo = ANGULO_MAX;

  if (objetivo != posicionActual) {
    if (objetivo > posicionActual) {
      for (int p = posicionActual; p <= objetivo; p++) {
        miServo.write(p);
        delay(delayMovimiento);
      }
    } else {
      for (int p = posicionActual; p >= objetivo; p--) {
        miServo.write(p);
        delay(delayMovimiento);
      }
    }
    posicionActual = objetivo;
    Serial.print("Movimiento completado a ");
    Serial.println(posicionActual);

    // ACK
    if (usingSoftwareSerial) {
#ifndef VARIANTE_A
      btSerial.print("OK ");
      btSerial.println(posicionActual);
#endif
    } else {
#ifdef VARIANTE_A
      Serial1.print("OK ");
      Serial1.println(posicionActual);
#endif
    }
  } else {
    Serial.println("Ya en la posicion solicitada.");
#ifndef VARIANTE_A
    btSerial.println("OK SAME");
#else
    Serial1.println("OK SAME");
#endif
  }
}
