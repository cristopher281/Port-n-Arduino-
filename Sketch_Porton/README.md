# Sketch Portón (Sketch_Porton)

Este directorio contiene el sketch mejorado para el proyecto del portón automatizado.

Archivos:
- `Porton.ino`  - Sketch principal. Incluye dos variantes (Serial1 para placas con puerto serie hardware adicional, y SoftwareSerial para Uno/Nano).
- `I2C_Scanner.ino` - Pequeño sketch para detectar la dirección I2C de tu LCD.

Cómo usar
1. Abre `Porton.ino` en el IDE de Arduino.
2. Si tu placa tiene `Serial1` (Mega, Due...), deja activa `VARIANTE_A` en la parte superior. Si usas UNO/NANO, comenta `#define VARIANTE_A` para usar SoftwareSerial y ajusta `BT_RX`/`BT_TX`.
3. Ajusta pines si tu conexión difiere (servo, trig/echo, pir, pines BT).
4. Verifica la dirección I2C del LCD con `I2C_Scanner.ino` si la pantalla no muestra texto (direcciones comunes: `0x27`, `0x3F`).
5. Carga el sketch en la placa.
6. Empareja tu módulo Bluetooth (HC-05/06) con la app móvil. Envía números con newline, por ejemplo `90\n`.

Cableado recomendado
- Servo: VCC 5V (o fuente externa si tu servo consume mucho), GND a GND común, señal a pin 9.
- HC-SR04: Trig -> pin 3, Echo -> pin 4, Vcc 5V, GND.
- PIR: salida digital -> pin 2, Vcc 5V, GND.
- LCD I2C: SDA -> A4 (Uno/Nano) o pin SDA de la placa, SCL -> A5 o pin SCL, Vcc 5V, GND.
- Módulo Bluetooth: TX -> RX (pin 10 si usas SoftwareSerial con BT_RX=10), RX -> TX (pin 11 si usas SoftwareSerial con BT_TX=11). O si usas `Serial1`, conecta al puerto serie hardware según tu placa.

Notas
- SoftwareSerial suele funcionar bien a 9600 baud. Evita baudios altos si hay problemas.
- Protege la alimentación del servo (usa fuente separada si necesita corriente alta).
- Si `pulseIn` devuelve 0, puede deberse a falta de eco o cableado incorrecto; revisa el sensor.

Pruebas rápidas
- Envia desde la app `90` seguido de "Enviar con nueva línea". Debes recibir `OK 90` desde el Arduino.
- Observa la LCD para la distancia y la detección PIR.

Si quieres, puedo: crear también un archivo de diagrama (texto) con esquemas de conexión, añadir un ejemplo de App Inventor o generar un pequeño script para simular comandos Bluetooth. Indica qué prefieres.