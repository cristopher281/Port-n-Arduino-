import tkinter as tk
from tkinter import ttk, font
import serial
import threading
import time
from collections import deque
import sys

# Matplotlib para gráficos embebidos en Tkinter
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- CONFIGURACIÓN GLOBAL ---
# ¡CAMBIA ESTO! Revisa tu IDE de Arduino para ver el puerto correcto
PUERTO_SERIAL = 'COM4' 
VELOCIDAD_SERIAL = 9600
HISTORY_SIZE = 120 # Número de puntos a mostrar en el gráfico

# --- PALETA DE COLORES (Tema Oscuro) ---
BG_COLOR = "#2b2b2b"       # Fondo principal
FRAME_COLOR = "#24282c"    # Fondo de 'tarjetas' o 'frames'
TEXT_COLOR = "#e8f0f2"     # Texto principal (blanco suave)
ACCENT_COLOR = "#00e5ff"   # Acento neon (cian)
ACCENT2_COLOR = "#6a00ff"  # Acento secundario (púrpura)
SUCCESS_COLOR = "#2bd97b"  # Verde para 'Conectado'
DANGER_COLOR = "#ff5c7c"   # Rojo para 'Peligro' o 'Error'
PLOT_BG_COLOR = "#17191a"  # Fondo del gráfico

# --- FUENTES ---
FONT_NORMAL = ("Helvetica", 11)
FONT_BOLD = ("Helvetica", 12, "bold")
FONT_TITLE = ("Helvetica", 18, "bold")
FONT_DATA = ("Helvetica", 24, "bold")


class ArduinoDashboard:
    """
    Clase principal que encapsula toda la lógica y la GUI del dashboard.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard Portón Arduino (Versión Mejorada)")
        self.root.geometry("600x650") # Ampliado para el gráfico
        self.root.configure(bg=BG_COLOR)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # --- Variables de estado ---
        self.arduino = None
        self.hilo_lectura = None
        self.conectado = False
        
        # --- Variables de Tkinter ---
        self.datos_distancia = tk.StringVar(value="--- cm")
        self.datos_movimiento = tk.StringVar(value="---")
        self.estado_conexion = tk.StringVar(value="Desconectado")

        # --- Historial para gráficos ---
        self.dist_hist = deque(maxlen=HISTORY_SIZE)
        self.mov_hist = deque(maxlen=HISTORY_SIZE)

        # --- Inicializar Estilos y Widgets ---
        self._crear_estilos()
        self._crear_widgets()

    def _crear_estilos(self):
        """Configura los estilos de ttk para el tema oscuro."""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # --- Estilos base ---
        self.style.configure('.',
                             background=BG_COLOR,
                             foreground=TEXT_COLOR,
                             font=FONT_NORMAL)

        # --- Frames tipo tarjeta ---
        self.style.configure('Card.TFrame', background=FRAME_COLOR, relief='flat', borderwidth=1)
        self.style.configure('Panel.TFrame', background=BG_COLOR)

        # --- Labels ---
        self.style.configure('Title.TLabel', font=FONT_TITLE, foreground=TEXT_COLOR, background=BG_COLOR)
        self.style.configure('Data.TLabel', font=FONT_DATA, foreground=ACCENT_COLOR, background=FRAME_COLOR)
        self.style.configure('Small.TLabel', font=FONT_NORMAL, foreground=TEXT_COLOR, background=BG_COLOR)
        self.style.configure('Success.TLabel', foreground=SUCCESS_COLOR, background=BG_COLOR)
        self.style.configure('Danger.TLabel', foreground=DANGER_COLOR, background=BG_COLOR)

        # --- Botones con aspecto plano y acento neon ---
        self.style.configure('Accent.TButton', font=FONT_BOLD, foreground='#0b0b0b', background=ACCENT_COLOR, relief='flat', padding=8)
        self.style.map('Accent.TButton',
                       background=[('active', ACCENT2_COLOR), ('disabled', '#444')],
                       foreground=[('active', '#ffffff')])

        self.style.configure('Danger.TButton', font=FONT_BOLD, foreground='#ffffff', background=DANGER_COLOR, relief='flat', padding=8)
        self.style.map('Danger.TButton', background=[('active', '#e04b65')])


    def _crear_widgets(self):
        """Crea y posiciona todos los elementos de la GUI."""
        # --- Frame Principal (usamos tk.Frame para fondo consistente) ---
        main_frame = tk.Frame(self.root, bg=BG_COLOR, padx=15, pady=15)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # --- Encabezado con logo y título ---
        header = tk.Frame(main_frame, bg=BG_COLOR)
        header.pack(fill=tk.X, pady=(0, 12))

        # Pequeño logo circular hecho con Canvas
        logo = tk.Canvas(header, width=40, height=40, bg=BG_COLOR, highlightthickness=0)
        logo.create_oval(6, 6, 34, 34, fill=ACCENT_COLOR, outline=ACCENT2_COLOR, width=2)
        logo.pack(side=tk.LEFT, padx=(4, 12))

        title_lbl = tk.Label(header, text="Dashboard Portón", font=FONT_TITLE, fg=TEXT_COLOR, bg=BG_COLOR)
        title_lbl.pack(side=tk.LEFT, anchor='c')

        # Línea de acento debajo del header
        accent_line = tk.Frame(main_frame, height=2, bg=ACCENT_COLOR)
        accent_line.pack(fill=tk.X, pady=(8, 12))

        # --- Sección de Conexión ---
        frame_conexion = ttk.Frame(main_frame)
        frame_conexion.pack(fill=tk.X, pady=5)

        self.btn_conectar = ttk.Button(frame_conexion, text="Conectar", command=self.conectar_arduino, style='Accent.TButton')
        self.btn_conectar.pack(side=tk.LEFT, padx=5, ipady=5)

        self.lbl_conexion = ttk.Label(frame_conexion, textvariable=self.estado_conexion, style="Danger.TLabel")
        self.lbl_conexion.pack(side=tk.LEFT, padx=10, anchor="w")

        # --- Área de gráfico ---
        plot_frame = ttk.Frame(main_frame, style="Card.TFrame")
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.fig = Figure(figsize=(5, 3), dpi=100, facecolor=FRAME_COLOR)
        self.ax = self.fig.add_subplot(111, facecolor=PLOT_BG_COLOR)

        # Colores del gráfico
        self.ax.set_title('Historial de Distancia (cm)', color=TEXT_COLOR)
        self.ax.set_xlabel('Muestras Recientes', color=TEXT_COLOR)
        self.ax.set_ylabel('Distancia (cm)', color=TEXT_COLOR)
        self.ax.tick_params(axis='both', colors=TEXT_COLOR)
        self.ax.grid(True, linestyle=':', color=TEXT_COLOR, alpha=0.4)
        self.fig.tight_layout() # Evita que las etiquetas se corten

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas.draw()

        # --- Sección de Datos Sensores ---
        frame_datos = ttk.Frame(main_frame, style="Card.TFrame", padding=20)
        frame_datos.pack(fill=tk.X, pady=10)
        frame_datos.columnconfigure(1, weight=1) # Columna de valor se expande

        # Distancia
        ttk.Label(frame_datos, text="Distancia Obstáculo:", style="Small.TLabel").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        lbl_dist_valor = ttk.Label(frame_datos, textvariable=self.datos_distancia, style="Data.TLabel")
        lbl_dist_valor.grid(row=0, column=1, sticky="e", padx=10)

        # Movimiento
        ttk.Label(frame_datos, text="Sensor Movimiento:", style="Small.TLabel").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.lbl_mov_valor = ttk.Label(frame_datos, textvariable=self.datos_movimiento, style="Data.TLabel")
        self.lbl_mov_valor.config(foreground="gray")
        self.lbl_mov_valor.grid(row=1, column=1, sticky="e", padx=10)

        # --- Sección de Control Servo ---
        frame_control = ttk.Frame(main_frame, style="Card.TFrame", padding=20)
        frame_control.pack(fill=tk.X, pady=10)

        ttk.Label(frame_control, text="Control Manual del Portón:", style="Small.TLabel", font=FONT_BOLD).pack(pady=5)

        # Usamos un Frame de Tk clásico para poder dar color de fondo directamente
        frame_botones = tk.Frame(frame_control, bg=FRAME_COLOR)
        frame_botones.pack()

        btn_abrir = ttk.Button(frame_botones, text="ABRIR (180°)", command=lambda: self.enviar_comando_servo(180), style='Accent.TButton')
        btn_abrir.pack(side=tk.LEFT, padx=10, pady=10, ipady=10, fill=tk.X, expand=True)

        btn_cerrar = ttk.Button(frame_botones, text="CERRAR (0°)", command=lambda: self.enviar_comando_servo(0), style='Accent.TButton')
        btn_cerrar.pack(side=tk.LEFT, padx=10, pady=10, ipady=10, fill=tk.X, expand=True)

    def conectar_arduino(self):
        """Intenta conectar o desconectar el Arduino."""
        if self.conectado:
            # --- Desconectar ---
            self.conectado = False
            if self.hilo_lectura:
                self.hilo_lectura.join(timeout=1) # Espera a que el hilo termine
            if self.arduino:
                self.arduino.close()
            
            self._actualizar_ui_desconectado()
            print("Desconectado de Arduino.")
        
        else:
            # --- Conectar ---
            try:
                self.arduino = serial.Serial(PUERTO_SERIAL, VELOCIDAD_SERIAL, timeout=1)
                time.sleep(2) # Esperar a que el Arduino se reinicie
                
                self.conectado = True
                self.hilo_lectura = threading.Thread(target=self.leer_datos_serial, daemon=True)
                self.hilo_lectura.start()
                
                self._actualizar_ui_conectado()
                print(f"Conectado a Arduino en {PUERTO_SERIAL}.")

            except serial.SerialException as e:
                self.estado_conexion.set(f"Error: {e}")
                self.lbl_conexion.config(style="Danger.TLabel")
                self.arduino = None
                print(f"Error de conexión: {e}")

    def _actualizar_ui_conectado(self):
        """Actualiza la GUI al estado 'Conectado'."""
        self.btn_conectar.config(text="Desconectar", style="Danger.TButton")
        self.estado_conexion.set(f"Conectado a {PUERTO_SERIAL}")
        self.lbl_conexion.config(style="Success.TLabel")

    def _actualizar_ui_desconectado(self):
        """Actualiza la GUI al estado 'Desconectado'."""
        self.btn_conectar.config(text="Conectar", style="TButton")
        self.estado_conexion.set("Desconectado")
        self.lbl_conexion.config(style="Danger.TLabel")
        self.datos_distancia.set("--- cm")
        self.datos_movimiento.set("---")
        self.lbl_mov_valor.config(foreground="gray")

    def leer_datos_serial(self):
        """Lee datos del Arduino en un hilo separado."""
        while self.conectado and self.arduino and self.arduino.is_open:
            try:
                if self.arduino.in_waiting > 0:
                    linea = self.arduino.readline().decode('utf-8').strip()
                    
                    if linea.startswith("D:") and ",M:" in linea:
                        # Programa la actualización en el hilo principal de la GUI
                        self.root.after(0, self.actualizar_datos, linea)
                        
            except serial.SerialException:
                # El puerto fue desconectado
                print("Error: Puerto desconectado.")
                self.conectado = False
                self.root.after(0, self._actualizar_ui_desconectado)
                break
            except Exception as e:
                # Otro error de lectura
                print(f"Error leyendo: {e}")
                time.sleep(0.1)

    def actualizar_datos(self, linea):
        """Procesa la línea de datos y actualiza la GUI (llamado desde el hilo principal)."""
        try:
            partes = linea.split(',')  # ['D:120', 'M:0']
            
            # --- Procesar Distancia ---
            val_dist_s = partes[0].split(':')[1]
            val_dist = int(val_dist_s)
            self.datos_distancia.set(f"{val_dist} cm")
            
            # --- Procesar Movimiento ---
            val_mov_s = partes[1].split(':')[1] # '0' o '1'
            val_mov = (val_mov_s == '1') # True si es '1', False si es '0'

            if val_mov:
                self.datos_movimiento.set("¡DETECTADO!")
                self.lbl_mov_valor.config(foreground=DANGER_COLOR)
            else:
                self.datos_movimiento.set("NO")
                self.lbl_mov_valor.config(foreground=SUCCESS_COLOR)

            # --- CAMBIO: Corregido el error, ahora SÍ se añaden datos a mov_hist ---
            self.dist_hist.append(val_dist)
            self.mov_hist.append(val_mov)
            
            self._actualizar_grafico()

        except Exception as e:
            print(f"Error procesando datos '{linea}': {e}")

    def _actualizar_grafico(self):
        """Dibuja el historial de distancia en el gráfico."""
        self.ax.clear()
        
        # --- Estilo del gráfico (debe reaplicarse al limpiar) ---
        self.ax.set_facecolor(PLOT_BG_COLOR)
        self.ax.set_title('Historial de Distancia (cm)', color=TEXT_COLOR)
        self.ax.set_xlabel('Muestras Recientes', color=TEXT_COLOR)
        self.ax.set_ylabel('Distancia (cm)', color=TEXT_COLOR)
        self.ax.tick_params(axis='both', colors=TEXT_COLOR)
        self.ax.grid(True, linestyle=':', color=TEXT_COLOR, alpha=0.4)
        
        n = len(self.dist_hist)
        if n > 0:
            xs = list(range(-n + 1, 1))
            ys = list(self.dist_hist)
            self.ax.plot(xs, ys, color=ACCENT_COLOR, marker='o', markersize=2)
            
            # Límites Y automáticos con margen
            min_y = min(ys)
            max_y = max(ys)
            padding = max((max_y - min_y) * 0.1, 5) # 10% de padding o 5cm
            self.ax.set_ylim(0, max_y + padding) # Mínimo 0
            self.ax.set_xlim(-HISTORY_SIZE, 0) # Eje X fijo

            # --- Dibujar marcadores rojos cuando hubo movimiento ---
            xm, ym = [], []
            for idx, (mv, dist) in enumerate(zip(self.mov_hist, self.dist_hist)):
                if mv: # Si el movimiento fue True
                    xm.append(idx - n + 1)
                    ym.append(dist)
            
            if xm:
                self.ax.scatter(xm, ym, color=DANGER_COLOR, s=60, zorder=5, label='Movimiento')
                self.ax.legend(loc='upper right', facecolor=FRAME_COLOR, labelcolor=TEXT_COLOR)
        else:
            self.ax.text(0.5, 0.5, 'Esperando datos...', transform=self.ax.transAxes, 
                         ha='center', color=TEXT_COLOR, font=FONT_BOLD)

        self.canvas.draw_idle()

    def enviar_comando_servo(self, posicion):
        """Envía un comando de posición al Arduino."""
        if self.conectado and self.arduino and self.arduino.is_open:
            comando = f"{posicion}\n"
            self.arduino.write(comando.encode('utf-8'))
            print(f"Comando enviado a Python: {comando.strip()}")
        else:
            print("No se puede enviar comando: Arduino desconectado.")

    def _on_closing(self):
        """Manejador para el cierre de la ventana."""
        print("Cerrando aplicación...")
        self.conectado = False # Detiene el bucle de lectura
        
        if self.hilo_lectura:
            self.hilo_lectura.join(timeout=1)
            
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
            print("Puerto serial cerrado.")
            
        self.root.quit()
        self.root.destroy()

# --- Punto de entrada principal ---
if __name__ == "__main__":
    # Añadimos diagnóstico extra para capturar problemas de arranque (p. ej. errores de Tcl/Tk)
    import traceback, os

    print("Args de Python:", sys.argv)
    # Imprimir algunas variables de entorno relevantes para Tcl/Tk
    for k in ["TK_LIBRARY", "TCL_LIBRARY", "TERM", "DISPLAY", "PYTHONHOME", "PYTHONPATH"]:
        if k in os.environ:
            print(f"ENV {k}={os.environ[k]}")

    try:
        root = tk.Tk()
        app = ArduinoDashboard(root)
        root.mainloop()
    except Exception:
        print("Error fatal durante arranque de la GUI. Volcando traceback completo:")
        traceback.print_exc()
    finally:
        print("Aplicación cerrada.")
        sys.exit()