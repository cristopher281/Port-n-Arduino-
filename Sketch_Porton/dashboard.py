import tkinter as tk
from tkinter import ttk, font
import serial
import threading
import time
from collections import deque
import sys
import platform

# Matplotlib para gráficos embebidos en Tkinter
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- CONFIGURACIÓN GLOBAL ---
PUERTO_SERIAL = 'COM4' # ¡¡ASEGÚRATE DE QUE ESTE SEA TU PUERTO!!
VELOCIDAD_SERIAL = 9600
HISTORY_SIZE = 120 # Número de puntos a mostrar en el gráfico

# --- PALETA DE COLORES "IMPACTO NEON" ---
BG_COLOR = "#1e1e1e"       # Un negro más profundo, tipo VS Code
FRAME_COLOR = "#2a2a2a"    # Fondo de 'tarjetas' (ligeramente más claro)
TEXT_COLOR = "#d4d4d4"     # Texto principal (blanco suave)
ACCENT_COLOR = "#00e5ff"   # Acento neon (cian brillante)
SUCCESS_COLOR = "#4cd964"  # Verde neon
DANGER_COLOR = "#ff4554"   # Rojo neon
PLOT_BG_COLOR = "#252526"  # Fondo del gráfico

# --- FUENTES ---
# Usamos fuentes modernas si están disponibles
try:
    if platform.system() == "Windows":
        FONT_FAM = "Segoe UI"
    elif platform.system() == "Darwin": # macOS
        FONT_FAM = "Helvetica Neue"
    else: # Linux/Otros
        FONT_FAM = "Roboto"
    # Prueba de que la fuente existe
    root_test = tk.Tk()
    font.Font(family=FONT_FAM, size=1)
    root_test.destroy()
except tk.TclError:
    FONT_FAM = "Helvetica" # Fuente de respaldo

FONT_SMALL = (FONT_FAM, 10)
FONT_NORMAL = (FONT_FAM, 11)
FONT_BOLD = (FONT_FAM, 12, "bold")
FONT_TITLE = (FONT_FAM, 20, "bold")
FONT_STAT_TITLE = (FONT_FAM, 12, "bold")
FONT_STAT_DATA = (FONT_FAM, 40, "bold")

class ArduinoDashboard:
    """
    Clase principal que encapsula la lógica y la GUI del dashboard "Next Level".
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard Portón Arduino [Nivel Dios]")
        self.root.geometry("900x600") # Más ancho para 2 columnas
        self.root.configure(bg=BG_COLOR)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # --- Variables de estado ---
        self.arduino = None
        self.hilo_lectura = None
        self.conectado = False
        
        # --- Variables de Tkinter ---
        self.datos_distancia = tk.StringVar(value="---")
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

        self.style.configure('.',
                             background=BG_COLOR,
                             foreground=TEXT_COLOR,
                             font=FONT_NORMAL,
                             fieldbackground=BG_COLOR,
                             bordercolor=FRAME_COLOR)
        
        # --- Frames tipo tarjeta ---
        self.style.configure('Card.TFrame', background=FRAME_COLOR, relief='flat')

        # --- Labels ---
        self.style.configure('TLabel', background=BG_COLOR, foreground=TEXT_COLOR)
        self.style.configure('Title.TLabel', font=FONT_TITLE, background=BG_COLOR)
        self.style.configure('StatTitle.TLabel', font=FONT_STAT_TITLE, foreground=TEXT_COLOR, background=FRAME_COLOR)
        
        # Estilos de datos (para cambiar color)
        self.style.configure('DefaultData.TLabel', font=FONT_STAT_DATA, foreground=TEXT_COLOR, background=FRAME_COLOR)
        self.style.configure('AccentData.TLabel', font=FONT_STAT_DATA, foreground=ACCENT_COLOR, background=FRAME_COLOR)
        self.style.configure('SuccessData.TLabel', font=FONT_STAT_DATA, foreground=SUCCESS_COLOR, background=FRAME_COLOR)
        self.style.configure('DangerData.TLabel', font=FONT_STAT_DATA, foreground=DANGER_COLOR, background=FRAME_COLOR)

        # Estilos de conexión
        self.style.configure('Success.TLabel', font=FONT_BOLD, foreground=SUCCESS_COLOR, background=BG_COLOR)
        self.style.configure('Danger.TLabel', font=FONT_BOLD, foreground=DANGER_COLOR, background=BG_COLOR)

        # --- Botones ---
        self.style.configure('TButton', font=FONT_BOLD, foreground=BG_COLOR, background=ACCENT_COLOR,
                             relief='flat', padding=(15, 12), borderwidth=0)
        self.style.map('TButton',
                       background=[('active', '#00c4d6'), ('disabled', '#444')],
                       foreground=[('active', BG_COLOR)])

        self.style.configure('Danger.TButton', background=DANGER_COLOR, foreground=TEXT_COLOR)
        self.style.map('Danger.TButton', background=[('active', '#e04b65')])

    def _crear_widgets(self):
        """Crea y posiciona todos los elementos de la GUI."""
        
        # --- Contenedor Principal con Grid de 2 Columnas ---
        main_frame = tk.Frame(self.root, bg=BG_COLOR)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=15, pady=15)
        
        main_frame.grid_columnconfigure(0, weight=1, minsize=280) # Columna Izquierda (Controles/Datos)
        main_frame.grid_columnconfigure(1, weight=3)           # Columna Derecha (Gráfico)
        main_frame.grid_rowconfigure(0, weight=1)

        # --- [COLUMNA IZQUIERDA] ---
        left_panel = tk.Frame(main_frame, bg=BG_COLOR)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Encabezado con logo y título
        header = tk.Frame(left_panel, bg=BG_COLOR)
        header.pack(fill=tk.X, pady=(0, 20))
        logo = tk.Canvas(header, width=30, height=30, bg=BG_COLOR, highlightthickness=0)
        logo.create_oval(4, 4, 26, 26, fill=ACCENT_COLOR, outline=ACCENT_COLOR, width=2)
        logo.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(header, text="Dashboard Portón", style='Title.TLabel').pack(side=tk.LEFT)

        # Sección de Conexión
        frame_conexion = ttk.Frame(left_panel)
        frame_conexion.pack(fill=tk.X, pady=10)
        self.btn_conectar = ttk.Button(frame_conexion, text="Conectar", command=self.conectar_arduino)
        self.btn_conectar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lbl_conexion = ttk.Label(frame_conexion, textvariable=self.estado_conexion, style="Danger.TLabel")
        self.lbl_conexion.pack(side=tk.LEFT, padx=20, anchor="w")

        # --- Tarjetas de Estadísticas (Stat Cards) ---
        # Tarjeta de Distancia
        card_dist = ttk.Frame(left_panel, style="Card.TFrame", padding=20)
        card_dist.pack(fill=tk.X, pady=10)
        ttk.Label(card_dist, text="DISTANCIA OBSTÁCULO", style="StatTitle.TLabel").pack(anchor="w")
        self.lbl_dist_valor = ttk.Label(card_dist, textvariable=self.datos_distancia, style="AccentData.TLabel")
        self.lbl_dist_valor.pack(anchor="w", pady=(10,0))
        # Etiqueta de unidad "cm"
        ttk.Label(card_dist, text="cm", style="TLabel", font=FONT_STAT_TITLE, background=FRAME_COLOR).place(relx=1.0, rely=1.0, x=-20, y=-15, anchor='se')


        # Tarjeta de Movimiento
        card_mov = ttk.Frame(left_panel, style="Card.TFrame", padding=20)
        card_mov.pack(fill=tk.X, pady=10)
        ttk.Label(card_mov, text="SENSOR MOVIMIENTO", style="StatTitle.TLabel").pack(anchor="w")
        self.lbl_mov_valor = ttk.Label(card_mov, textvariable=self.datos_movimiento, style="DefaultData.TLabel")
        self.lbl_mov_valor.pack(anchor="w", pady=(10,0))

        # Sección de Control Servo (al final)
        frame_control = ttk.Frame(left_panel, style="Card.TFrame", padding=20)
        frame_control.pack(fill=tk.X, pady=(20, 10), side=tk.BOTTOM) # Pegado abajo
        ttk.Label(frame_control, text="CONTROL MANUAL DEL PORTÓN", style="StatTitle.TLabel").pack(anchor="w", pady=(0, 15))
        
        frame_botones = ttk.Frame(frame_control, style="Card.TFrame")
        frame_botones.pack(fill=tk.X, expand=True)
        
        btn_abrir = ttk.Button(frame_botones, text="ABRIR", command=lambda: self.enviar_comando_servo(180))
        btn_abrir.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        btn_cerrar = ttk.Button(frame_botones, text="CERRAR", command=lambda: self.enviar_comando_servo(0))
        btn_cerrar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # --- [COLUMNA DERECHA] ---
        right_panel = ttk.Frame(main_frame, style="Card.TFrame", padding=10)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # Configurar gráfico
        self.fig = Figure(figsize=(5, 5), dpi=100, facecolor=FRAME_COLOR)
        self.ax = self.fig.add_subplot(111, facecolor=PLOT_BG_COLOR)
        self.ax.tick_params(axis='both', which='major', labelsize=10, colors=TEXT_COLOR)
        self.ax.set_title('Historial de Distancia (cm)', color=TEXT_COLOR, fontdict={'fontfamily': FONT_FAM, 'fontsize': 14})
        self.ax.set_xlabel('Muestras Recientes', color=TEXT_COLOR, fontdict={'fontfamily': FONT_FAM, 'fontsize': 10})
        self.ax.set_ylabel('Distancia (cm)', color=TEXT_COLOR, fontdict={'fontfamily': FONT_FAM, 'fontsize': 10})
        self.ax.grid(True, linestyle=':', color=TEXT_COLOR, alpha=0.2)
        self.ax.spines['top'].set_color(FRAME_COLOR)
        self.ax.spines['right'].set_color(FRAME_COLOR)
        self.ax.spines['bottom'].set_color(TEXT_COLOR)
        self.ax.spines['left'].set_color(TEXT_COLOR)
        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()


    def conectar_arduino(self):
        """Intenta conectar o desconectar el Arduino."""
        if self.conectado:
            # --- Desconectar ---
            self.conectado = False
            if self.hilo_lectura:
                self.hilo_lectura.join(timeout=1)
            if self.arduino:
                self.arduino.close()
            self._actualizar_ui_desconectado()
            print("Desconectado de Arduino.")
        
        else:
            # --- Conectar ---
            try:
                self.arduino = serial.Serial(PUERTO_SERIAL, VELOCIDAD_SERIAL, timeout=1)
                time.sleep(2)
                self.conectado = True
                self.hilo_lectura = threading.Thread(target=self.leer_datos_serial, daemon=True)
                self.hilo_lectura.start()
                self._actualizar_ui_conectado()
                print(f"Conectado a Arduino en {PUERTO_SERIAL}.")
            except serial.SerialException as e:
                self.estado_conexion.set(f"Error: No se encuentra {PUERTO_SERIAL}")
                self.lbl_conexion.config(style="Danger.TLabel")
                self.arduino = None
                print(f"Error de conexión: {e}")

    def _actualizar_ui_conectado(self):
        self.btn_conectar.config(text="Desconectar", style="Danger.TButton")
        self.estado_conexion.set(f"Conectado a {PUERTO_SERIAL}")
        self.lbl_conexion.config(style="Success.TLabel")

    def _actualizar_ui_desconectado(self):
        self.btn_conectar.config(text="Conectar", style="TButton")
        self.estado_conexion.set("Desconectado")
        self.lbl_conexion.config(style="Danger.TLabel")
        self.datos_distancia.set("---")
        self.datos_movimiento.set("---")
        self.lbl_mov_valor.config(style="DefaultData.TLabel")

    def leer_datos_serial(self):
        """Lee datos del Arduino en un hilo separado."""
        while self.conectado and self.arduino and self.arduino.is_open:
            try:
                if self.arduino.in_waiting > 0:
                    linea = self.arduino.readline().decode('utf-8').strip()
                    if linea.startswith("D:") and ",M:" in linea:
                        self.root.after(0, self.actualizar_datos, linea)
            except serial.SerialException:
                print("Error: Puerto desconectado.")
                self.root.after(0, self.conectar_arduino) # Intenta desconectar limpiamente
                break
            except Exception as e:
                print(f"Error leyendo: {e}")
                time.sleep(0.1)

    def actualizar_datos(self, linea):
        """Procesa la línea de datos y actualiza la GUI."""
        try:
            partes = linea.split(',')
            
            # --- Procesar Distancia ---
            val_dist_s = partes[0].split(':')[1]
            val_dist = int(val_dist_s)
            self.datos_distancia.set(f"{val_dist}")
            
            # --- Procesar Movimiento ---
            val_mov_s = partes[1].split(':')[1]
            val_mov = (val_mov_s == '1') 

            if val_mov:
                self.datos_movimiento.set("¡DETECTADO!")
                self.lbl_mov_valor.config(style="DangerData.TLabel")
            else:
                self.datos_movimiento.set("NO")
                self.lbl_mov_valor.config(style="SuccessData.TLabel")
            
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
        self.ax.set_title('Historial de Distancia (cm)', color=TEXT_COLOR, fontdict={'fontfamily': FONT_FAM, 'fontsize': 14})
        self.ax.set_xlabel('Muestras Recientes', color=TEXT_COLOR, fontdict={'fontfamily': FONT_FAM, 'fontsize': 10})
        self.ax.set_ylabel('Distancia (cm)', color=TEXT_COLOR, fontdict={'fontfamily': FONT_FAM, 'fontsize': 10})
        self.ax.grid(True, linestyle=':', color=TEXT_COLOR, alpha=0.2)
        self.ax.tick_params(axis='both', colors=TEXT_COLOR)
        self.ax.spines['top'].set_color(FRAME_COLOR)
        self.ax.spines['right'].set_color(FRAME_COLOR)
        self.ax.spines['bottom'].set_color(TEXT_COLOR)
        self.ax.spines['left'].set_color(TEXT_COLOR)
        
        n = len(self.dist_hist)
        if n > 0:
            xs = list(range(-n + 1, 1))
            ys = list(self.dist_hist)
            
            # --- ¡MEJORA DE IMPACTO! ---
            # 1. Dibuja la línea
            self.ax.plot(xs, ys, color=ACCENT_COLOR, marker='o', markersize=2, linewidth=2)
            # 2. Dibuja el relleno semitransparente
            self.ax.fill_between(xs, ys, color=ACCENT_COLOR, alpha=0.3)
            
            # Límites Y automáticos con margen
            max_y = max(ys)
            padding = max(max_y * 0.1, 10) # 10% de padding o 10cm
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
                self.ax.legend(loc='upper right', facecolor=FRAME_COLOR, labelcolor=TEXT_COLOR, frameon=False)
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
        self.conectado = False
        if self.hilo_lectura:
            self.hilo_lectura.join(timeout=1)
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
            print("Puerto serial cerrado.")
        self.root.quit()
        self.root.destroy()
        sys.exit()

# --- Punto de entrada principal ---
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ArduinoDashboard(root)
        root.mainloop()
    except Exception as e:
        print(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Aplicación cerrada.")