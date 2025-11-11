# Sketch_Porton — Web deploy notes# Dashboard Portón — despliegue local



He creado una versión web del dashboard en `web_app/` pensada para desplegar en plataformas como Render.Este directorio contiene la interfaz de escritorio (Tkinter) que se conecta a tu Arduino vía puerto serie y muestra datos de distancia y detección de movimiento, además de permitir controlar un servo.



Qué contieneArchivos importantes

- `web_app/app.py` — Flask + Flask-SocketIO backend. Lee el puerto serie si `USE_SERIAL=true` y `pyserial` está instalado; si no, usa un simulador para generar datos.- `dashboard.py` — aplicación principal (Tkinter + Matplotlib).

- `web_app/templates/index.html` — Interfaz con Chart.js.- `Porton.ino` — sketch Arduino (subir a la placa Mega/Nano/etc.).

- `web_app/static/main.js` — Cliente socket.io y lógica del gráfico.- `requirements.txt` — dependencias Python: pyserial, matplotlib.

- `web_app/requirements.txt` — Requisitos para deploy (Flask, Flask-SocketIO, eventlet, pyserial...).- `run_dashboard.bat` — script para ejecutar el dashboard en Windows (usa `venv` si existe).

- `web_app/Procfile` — inicio con gunicorn+eventlet (útil para deploy en Render).- `setup_venv.bat` — crea un virtualenv y instala dependencias.



Notas importantes sobre deploymentRequisitos

- Render (y otros hosts en cloud) NO pueden acceder a tu Arduino conectado por USB en tu PC. Si quieres alojar completamente en la nube y recibir datos reales del Arduino, necesitas que el dispositivo envíe sus lecturas por red (HTTP, WebSocket o MQTT). Opciones:- Windows con Python 3.8+ instalado y `python` en PATH.

  - Reemplazar Arduino por un ESP32/ESP8266 que envíe datos vía WiFi a tu backend en la nube.- Arduino Mega (o la placa que uses) con el sketch `Porton.ino` cargado.

  - Mantener el Arduino en tu red local y ejecutar el backend en una máquina local que haga tunnel a la nube (solución más compleja y menos recomendable por seguridad).

  - Ejecutar el backend en un Raspberry Pi o servidor local conectado por USB y exponer solo la UI en la nube.Pasos para ejecutar localmente (recomendado)



Ejecución local (dev)1. Clona o abre esta carpeta en tu PC.

```cmd2. (Opcional pero recomendado) Crea un entorno virtual e instala dependencias:

cd /d "c:\Users\DELL\OneDrive\Escritorio\Porton-Arduino\Sketch_Porton\web_app"

python -m venv venv_web    Abre cmd en esta carpeta y ejecuta:

call venv_web\Scripts\activate.bat

pip install -r requirements.txt    ```cmd

# Para desarrollo    setup_venv.bat

python app.py    ```

# Para simular deploy (gunicorn + eventlet)

gunicorn -k eventlet -w 1 web_app.app:app3. Ejecuta el dashboard:

```

    - Si usaste `setup_venv.bat`, puedes ejecutar:

Variables de entorno

- `USE_SERIAL` (true/false) — si true intenta leer de `SERIAL_PORT` usando pyserial.        ```cmd

- `SERIAL_PORT` — puerto por defecto `COM4`.        call venv\Scripts\activate.bat

- `SERIAL_BAUD` — velocidad por defecto `9600`.        python dashboard.py

- `EMIT_INTERVAL` — intervalo del simulador en segundos.        ```



Siguientes pasos sugeridos    - O usa el script que detecta el virtualenv automáticamente:

- Si quieres deploy en Render con datos reales, migrar el Arduino a un módulo WiFi (ESP32) que publique lecturas a este backend.

- Puedo ayudarte a implementar el endpoint HTTP/MQTT en el Arduino (o ESP) y adaptar el backend para recibirlo.        ```cmd

        run_dashboard.bat
        ```

4. En la interfaz pulsar "Conectar" para abrir el puerto serie configurado en `dashboard.py` (por defecto `COM4`, 9600 bps).

Notas
- Si usas Arduino connected por USB asegúrate de seleccionar el puerto correcto en `dashboard.py` (PUERTO_SERIAL).
- Si el Arduino está usando un módulo Bluetooth o `Serial1`, ajusta `Porton.ino` según corresponda.
- Para crear un ejecutable `.exe` (opcional) puedo añadir un script con PyInstaller.

Contacto
- Si necesitas que prepare un instalador `.exe` o despliegue en Raspberry Pi, dime y lo preparo.
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