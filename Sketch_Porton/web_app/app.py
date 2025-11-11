import os
import time
import threading
import random
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# Intentamos importar pyserial; si no está disponible, usar simulador
try:
    import serial
except Exception:
    serial = None

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devkey')
# Usar eventlet/gevent en despliegue (Render). Aquí permitimos cualquier async_mode.
socketio = SocketIO(app, cors_allowed_origins='*')

# Config
USE_SERIAL = os.environ.get('USE_SERIAL', 'false').lower() in ('1', 'true', 'yes')
SERIAL_PORT = os.environ.get('SERIAL_PORT', 'COM4')
SERIAL_BAUD = int(os.environ.get('SERIAL_BAUD', '9600'))
EMIT_INTERVAL = float(os.environ.get('EMIT_INTERVAL', '0.6'))

sensor_thread = None
thread_stop = threading.Event()


def serial_reader_loop():
    """Lee desde el puerto serie y emite eventos socket.io con {dist, mov}."""
    ser = None
    try:
        if serial is None:
            raise RuntimeError('pyserial no disponible')
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
        # esperar a que Arduino reinicie si aplica
        time.sleep(2.0)
        while not thread_stop.is_set():
            try:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    # formato esperado: D:<n>,M:<0|1>
                    if line.startswith('D:') and ',M:' in line:
                        parts = line.split(',')
                        d = int(parts[0].split(':')[1])
                        m = int(parts[1].split(':')[1])
                        payload = {'dist': d, 'mov': m}
                        socketio.emit('sensor', payload)
                else:
                    time.sleep(0.01)
            except Exception:
                time.sleep(0.2)
    except Exception:
        # fall back al simulador si el serial falla
        simulator_loop()
    finally:
        if ser and ser.is_open:
            ser.close()


def simulator_loop():
    """Simulador: emite datos periódicamente; útil para pruebas sin hardware."""
    base = 2500
    while not thread_stop.is_set():
        # pequeños ruidos alrededor de base
        dist = max(0, base + random.randint(-50, 50))
        # movimiento aleatorio con baja probabilidad
        mov = 1 if random.random() < 0.05 else 0
        socketio.emit('sensor', {'dist': dist, 'mov': mov})
        time.sleep(EMIT_INTERVAL)


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    print('Cliente conectado')
    emit('connected', {'msg': 'OK'})


@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')


def start_sensor_thread():
    global sensor_thread
    if sensor_thread and sensor_thread.is_alive():
        return
    thread_stop.clear()
    if USE_SERIAL and serial is not None:
        sensor_thread = threading.Thread(target=serial_reader_loop, daemon=True)
    else:
        sensor_thread = threading.Thread(target=simulator_loop, daemon=True)
    sensor_thread.start()


if __name__ == '__main__':
    start_sensor_thread()
    # Dev server (no para producción); Render usará gunicorn/eventlet
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
