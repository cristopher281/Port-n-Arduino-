import tkinter as tk
from tkinter import ttk, font
import serial
import threading
import time

# --- CONFIGURACIÓN ---
# ¡CAMBIA ESTO! Revisa tu IDE de Arduino para ver el puerto correcto
PUERTO_SERIAL = 'COM4'
VELOCIDAD_SERIAL = 9600
# --- FIN CONFIGURACIÓN ---

# Variables globales para los datos de los sensores
datos_distancia = tk.StringVar(value="--- cm")
datos_movimiento = tk.StringVar(value="---")

# Variable global para el estado de la conexión
estado_conexion = tk.StringVar(value="Desconectado")

# Objeto Serial (inicialmente None)
arduino = None

def conectar_arduino():
    """Intenta conectar o desconectar el Arduino."""
    global arduino
    try:
        if arduino is None or not arduino.is_open:
            # Conectar
            arduino = serial.Serial(PUERTO_SERIAL, VELOCIDAD_SERIAL, timeout=1)
            time.sleep(2) # Esperar a que el Arduino se reinicie
            
            # Iniciar el hilo de lectura
            hilo_lectura = threading.Thread(target=leer_datos_serial, daemon=True)
            hilo_lectura.start()
            
            btn_conectar.config(text="Desconectar")
            estado_conexion.set(f"Conectado a {PUERTO_SERIAL}")
            print("Conectado a Arduino.")
        else:
            # Desconectar
            arduino.close()
            btn_conectar.config(text="Conectar")
            estado_conexion.set("Desconectado")
            datos_distancia.set("--- cm")
            datos_movimiento.set("---")
            print("Desconectado de Arduino.")
            
    except serial.SerialException as e:
        estado_conexion.set(f"Error: {e}")
        arduino = None
        print(f"Error de conexión: {e}")

def leer_datos_serial():
    """Lee datos del Arduino en un hilo separado."""
    global arduino
    while arduino and arduino.is_open:
        try:
            if arduino.in_waiting > 0:
                linea = arduino.readline().decode('utf-8').strip()
                
                # Imprime la línea cruda para depuración
                # print(f"Arduino dice: {linea}") 
                
                # Procesa solo las líneas de datos (ej: "D:120,M:0")
                if linea.startswith("D:") and ",M:" in linea:
                    actualizar_datos(linea)
                    
        except serial.SerialException:
            # El puerto fue desconectado
            break
        except Exception as e:
            # Otro error de lectura
            print(f"Error leyendo: {e}")
            time.sleep(0.1)
    
    # Si el bucle termina, estamos desconectados
    if btn_conectar['text'] == "Desconectar":
        conectar_arduino() # Llama a la función para actualizar la UI

def actualizar_datos(linea):
    """Procesa la línea de datos y actualiza la GUI."""
    try:
        # linea = "D:120,M:0"
        partes = linea.split(',') # ['D:120', 'M:0']
        
        # Procesar distancia
        val_dist = partes[0].split(':')[1] # '120'
        datos_distancia.set(f"{val_dist} cm")
        
        # Procesar movimiento
        val_mov = partes[1].split(':')[1] # '0'
        if val_mov == '1':
            datos_movimiento.set("¡DETECTADO!")
            lbl_mov_valor.config(foreground="red")
        else:
            datos_movimiento.set("NO")
            lbl_mov_valor.config(foreground="green")
            
    except Exception as e:
        print(f"Error procesando datos '{linea}': {e}")

def enviar_comando_servo(posicion):
    """Envía un comando de posición al Arduino."""
    if arduino and arduino.is_open:
        comando = f"{posicion}\n"
        arduino.write(comando.encode('utf-8'))
        print(f"Comando enviado a Python: {comando.strip()}")
    else:
        print("No se puede enviar comando: Arduino desconectado.")

# --- Creación de la Interfaz Gráfica (GUI) ---
root = tk.Tk()
root.title("Dashboard Portón Arduino")
root.geometry("400x350")
root.configure(bg="#f0f0f0")

# --- Estilos ---
style = ttk.Style()
style.configure("TFrame", background="#f0f0f0")
style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 12))
style.configure("Title.TLabel", font=("Helvetica", 16, "bold"))
style.configure("Data.TLabel", font=("Helvetica", 20, "bold"), foreground="#000080")
style.configure("TButton", font=("Helvetica", 12))

# --- Frame Principal ---
main_frame = ttk.Frame(root, padding="20")
main_frame.pack(expand=True, fill=tk.BOTH)

# --- Título ---
ttk.Label(main_frame, text="Dashboard Portón", style="Title.TLabel").pack(pady=(0, 20))

# --- Sección de Conexión ---
frame_conexion = ttk.Frame(main_frame, style="TFrame")
frame_conexion.pack(fill=tk.X, pady=5)
btn_conectar = ttk.Button(frame_conexion, text="Conectar", command=conectar_arduino)
btn_conectar.pack(side=tk.LEFT, padx=5)
lbl_conexion = ttk.Label(frame_conexion, textvariable=estado_conexion, style="TLabel")
lbl_conexion.pack(side=tk.LEFT, padx=5)

# --- Sección de Datos Sensores ---
frame_datos = ttk.Frame(main_frame, padding=10, relief="groove")
frame_datos.pack(fill=tk.X, pady=10)

# Distancia
ttk.Label(frame_datos, text="Distancia Obstáculo:", style="TLabel").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
lbl_dist_valor = ttk.Label(frame_datos, textvariable=datos_distancia, style="Data.TLabel")
lbl_dist_valor.grid(row=0, column=1, sticky=tk.W, padx=10)

# Movimiento
ttk.Label(frame_datos, text="Sensor Movimiento:", style="TLabel").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
lbl_mov_valor = ttk.Label(frame_datos, textvariable=datos_movimiento, style="Data.TLabel")
lbl_mov_valor.config(foreground="gray")
lbl_mov_valor.grid(row=1, column=1, sticky=tk.W, padx=10)


# --- Sección de Control Servo ---
frame_control = ttk.Frame(main_frame, padding=10, relief="groove")
frame_control.pack(fill=tk.X, pady=10)

ttk.Label(frame_control, text="Control Manual del Portón:", style="TLabel").pack(pady=5)

frame_botones = ttk.Frame(frame_control, style="TFrame")
frame_botones.pack()

# Comando "lambda" es necesario para pasar argumentos a la función
btn_abrir = ttk.Button(frame_botones, text="ABRIR (180°)", command=lambda: enviar_comando_servo(180))
btn_abrir.pack(side=tk.LEFT, padx=10, pady=10, ipady=10)

btn_cerrar = ttk.Button(frame_botones, text="CERRAR (0°)", command=lambda: enviar_comando_servo(0))
btn_cerrar.pack(side=tk.LEFT, padx=10, pady=10, ipady=10)


# --- Iniciar la aplicación ---
root.mainloop()

# Al cerrar la ventana, nos aseguramos de cerrar la conexión
if arduino and arduino.is_open:
    arduino.close()
    print("Cerrando conexión serial.")