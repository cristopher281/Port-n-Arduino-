# Dashboard Portón — guía de despliegue y resolución de problemas

Este documento explica cómo levantar el proyecto localmente (GUI de escritorio) y cómo preparar la versión web para deploy en servicios como Render. Incluye soluciones a los problemas que ya hemos encontrado y comandos listos para usar en Windows (cmd.exe).

## Estructura importante
- `dashboard.py` — aplicación de escritorio (Tkinter + Matplotlib) que se comunica por serie con el Arduino.
- `Porton.ino` — sketch Arduino para el hardware (envía líneas `D:<dist>,M:<0|1>`).
- `web_app/` — versión web (Flask + SocketIO + Chart.js) pensada para deploy en la nube.

## Requisitos
- Windows 10/11 con Python 3.10+ en PATH.
- Arduino/Placa conectada por USB si vas a usar la app de escritorio.
- Opcional: `arduino-cli` o Arduino IDE para subir el sketch.

---

## 1) Preparar entorno virtual y dependencias

Abre cmd y sitúate en la carpeta del proyecto:

```cmd
cd /d "c:\Users\DELL\OneDrive\Escritorio\Porton-Arduino\Sketch_Porton"
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
```

Si `requirements.txt` no incluye `matplotlib` o `pyserial` instala:

```cmd
pip install pyserial matplotlib
```

---

## 2) Ejecutar el dashboard de escritorio (Tkinter)

```cmd
call venv\Scripts\activate.bat
python dashboard.py
```

La ventana se abrirá en tu escritorio. Usa el botón "Conectar" para abrir el puerto serie configurado en `dashboard.py` (por defecto `COM4`).

---

## 3) Problemas comunes y soluciones (rápidas)

- Error: `TclError: unknown option "-background"`
  - Causa: pasar `background=` a widgets `ttk.*` (no soportado por algunos temas).
  - Solución: eliminar `background=` en ttk; usar `ttk.Style().configure(...)` o `tk.Frame(..., bg=...)`.

- Error: `Too early to create variable: no default root window`
  - Causa: crear `tk.StringVar()` antes de `tk.Tk()`.
  - Solución: crear variables Tk sólo después de `root = tk.Tk()` (mover la creación dentro del constructor/initializer de la GUI).

- Matplotlib dibuja lento o bloquea
  - Recomendación: limitar `HISTORY_SIZE`, usar `canvas.draw_idle()`, reducir frecuencia de emisión desde Arduino o decimar puntos.

- Problema: paquetes instalados en otra instalación de Python
  - Diagnóstico: `where python` para ver los intérpretes; activa el `venv` antes de instalar.

- Puerto COM incorrecto
  - Verifica en el Administrador de dispositivos de Windows y actualiza `PUERTO_SERIAL` en `dashboard.py` si es necesario.

---

## 4) Subir y verificar el sketch Arduino

Abre `Porton.ino` en el IDE de Arduino y sube a la placa correcta. Si usas Mega preferir la variante que usa `Serial` por USB. Para Uno/Nano con Bluetooth usa la variante `SoftwareSerial`.

Ejemplo con `arduino-cli` (Mega):

```cmd
arduino-cli upload -p COM4 --fqbn arduino:avr:mega Porton.ino
```

Verifica que el Arduino envía líneas con el formato: `D:<dist>,M:<0|1>`.

---

## 5) Web-app (dev y deploy en Render)

### Ejecutar localmente (dev)

```cmd
cd web_app
python -m venv venv_web
call venv_web\Scripts\activate.bat
pip install -r requirements.txt
python app.py
```

### Deploy en Render (resumen)
- Build command: `pip install -r web_app/requirements.txt`
- Start command: `gunicorn -k eventlet -w 1 web_app.app:app`

Importante: Render no puede acceder a puertos USB de tu PC; para datos reales en la nube usa un ESP32/ESP8266 que envíe lecturas por HTTP/WebSocket al backend, o ejecuta el backend en un dispositivo local (Raspberry Pi) conectado al Arduino.

---

## 6) Empaquetar para Windows (.exe)

```cmd
call venv\Scripts\activate.bat
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed dashboard.py
```

Si hay problemas con recursos (matplotlib/Tk), prueba `--onedir` para depurar.

---

## 7) Siguientes pasos recomendados (yo puedo hacerlo)

## 🚀 Dashboard Portón Automatizado: Guía Maestra

Bienvenido a la documentación oficial del proyecto. Esta guía está diseñada para llevarte desde cero hasta la ejecución del dashboard, previniendo los errores más comunes.

## 🎯 ¿Qué hace este proyecto?

Este proyecto monitorea y controla un portón automatizado usando un Arduino. Consiste en tres componentes principales que trabajan juntos:

1.  **Firmware (Arduino):** El cerebro (`Porton.ino`) que lee sensores (distancia, movimiento) y controla el servo.
2.  **Dashboard de Escritorio (Python):** Una aplicación (`dashboard.py`) para tu PC que se conecta por USB al Arduino, muestra datos en tiempo real y te permite enviar comandos.
3.  **Dashboard Web (Python):** Una aplicación web (`web_app/`) que puede simular los datos o conectarse al Arduino, lista para desplegarse.

---

## 🗂️ Estructura de Archivos (Clave para evitar errores)

Para que los comandos funcionen, tus archivos **deben** estar organizados así. El error más común (`No such file or directory`) ocurre si `dashboard.py` no está en la carpeta raíz.

Porton-Arduino/
  ├── venv/  <-- Carpeta del entorno virtual (se crea en el Paso 2)
  ├── Sketch_Porton/
  │   ├── Porton.ino  <-- El código que va en tu Arduino
  │   ├── web_app/
  │   │   ├── app.py
  │   │   └── (otros archivos web...)
  │   ├── dashboard.py  <-- ¡IMPORTANTE! El script de la app de escritorio
  │   └── requirements.txt <-- Lista de librerías para la app de escritorio
  └── README.md  <-- Esta guía


---

## 🛠️ Paso 1: Configuración del Hardware (Arduino)

Antes de tocar Python, el Arduino debe estar listo.

1.  **Conecta** tu Arduino Mega (o Uno) a la PC.
2.  **Abre** el archivo `Sketch_Porton/Porton.ino` con tu IDE de Arduino.
3.  **Verifica** que los pines definidos en el código (ej. `pinServo = 9`, `pinPIR = 2`) coincidan con tu cableado físico.
4.  **Sube** el código a tu placa.
5.  **Comprueba** que el Arduino envía datos. Abre el **Monitor Serie** (en el IDE de Arduino) y asegúrate de que estás viendo líneas como:
    `D:150,M:0`
    `D:149,M:0`
    `D:45,M:1`
    *Si no ves esto, la app de Python no funcionará.*


---

## 🐍 Paso 2: Configuración del Entorno (Python)

Crearemos un "entorno virtual" (`venv`) para instalar las librerías de Python de forma limpia.

1.  Abre una terminal (`cmd` o `PowerShell`).
2.  Navega a la carpeta raíz de tu proyecto. (¡Aquí es donde está `dashboard.py`!)
    ```cmd
    cd C:\Users\DELL\OneDrive\Escritorio\Porton-Arduino
    ```
3.  **Crea el entorno virtual:** (Solo lo haces una vez)
    ```cmd
    python -m venv venv
    ```
4.  **Activa el entorno:** (Debes hacer esto **cada vez** que abras una nueva terminal)
    ```cmd
    call venv\Scripts\activate.bat
    ```
    *(Verás `(venv)` al inicio de tu línea de comandos)*.

5.  **Instala las librerías:**
    ```cmd
    pip install -r requirements.txt
    ```
    *(Esto instalará `pyserial`, `matplotlib` y todo lo necesario).* 


---

## ⚙️ Paso 3: Configuración Crítica (¡Evita el 99% de Errores!)

Casi todos los errores de ejecución se deben a un solo problema: el **Puerto COM**.

1.  **Encuentra tu Puerto COM:**
    * Con el Arduino conectado, ve al **Administrador de Dispositivos** de Windows.
    * Expande la sección **"Puertos (COM & LPT)"**.
    * Busca tu Arduino (ej. "USB Serial Port (COM4)"). Anota ese número `COM4`.

2.  **Configura el Script:**
    * Abre el archivo `dashboard.py` en tu editor (VS Code).
    * Busca la línea de `PUERTO_SERIAL` (cerca del inicio).
    * **Edita el valor** para que coincida exactamente con el puerto que encontraste.

    ```python
    # --- CONFIGURACIÓN GLOBAL ---
    # ¡CAMBIA ESTO! Revisa tu IDE de Arduino o Administrador de Dispositivos
    PUERTO_SERIAL = 'COM4' 
    ```


---

## 🔧 Comandos clave: qué hacen, por qué usarlos y errores comunes

Aquí tienes los dos comandos que usamos a menudo y una explicación práctica para que no te sorprenda ningún error.

- Instalar dependencias (recomendado dentro del `venv`):

```cmd
python -m pip install -r requirements.txt
```

Qué hace:
- Ejecuta el instalador `pip` usando el intérprete `python` activo. Esto garantiza que las librerías se instalen en el entorno de Python que estás usando (muy útil si tienes varias versiones de Python).
- Instala todas las dependencias listadas en `requirements.txt` (p. ej. `pyserial`, `matplotlib`).

Por qué usar `python -m pip` en lugar de `pip`:
- Evita confusiones con instalaciones globales o `pip` de otra versión de Python. Con `python -m pip` te aseguras de usar el `pip` del intérprete `python` que se ejecuta.

Errores comunes y soluciones:
- "ModuleNotFoundError: No module named 'serial'": significa que no instalaste `pyserial` en el entorno activo. Solución: activa `venv` y vuelve a ejecutar el comando.
- Permiso denegado / UAC / antivirus bloquea la instalación: ejecuta la terminal como Administrador o revisa el antivirus, o instala dentro del `venv` (no suele requerir permisos de admin).
- Problemas TLS/SSL al descargar paquetes: puede ser un pip viejo; ejecuta `python -m pip install --upgrade pip` y vuelve a intentar.

- Ejecutar el dashboard (desde la raíz del proyecto, con `venv` activo):

```cmd
python dashboard.py
```

Qué hace:
- Inicia la aplicación de escritorio (Tkinter) que muestra los datos y controla el Arduino.

Errores comunes y soluciones al ejecutar `dashboard.py`:
- `ModuleNotFoundError` para `matplotlib` o `serial`: activa el `venv` y ejecuta `python -m pip install -r requirements.txt`.
- `TclError: unknown option "-background"`: indica que el código pasó un argumento `background=` a widgets `ttk`. Solución: usa la versión del README para evitar ediciones que añadan `background=` a `ttk.*`, o usar `tk.Frame(..., bg=...)` o `ttk.Style()`.
- `Too early to create variable: no default root window`: significa que se creó `tk.StringVar()` (u otra variable de Tk) antes de `root = tk.Tk()`. Solución: abrir `dashboard.py` y mover la creación de variables Tk después de crear la ventana `root`.
- `Error: No se encuentra COM...` o `SerialException: could not open port 'COMx'`: revisa el **Paso 3** de este README (Administrador de dispositivos) y asegúrate de configurar `PUERTO_SERIAL` con el puerto correcto.
- La GUI arranca pero queda congelada o Matplotlib lanza excepciones en callbacks: puede deberse a que el refresco del gráfico hace demasiadas operaciones en el hilo principal. Solución: cerrar la app, editar `dashboard.py` para usar `canvas.draw_idle()` en lugar de `canvas.draw()` y limitar el tamaño de `HISTORY_SIZE`.

---


## ▶️ Paso 4: Ejecutar el Dashboard

Si completaste los pasos 1, 2 y 3, esto funcionará.

1.  Abre tu terminal (asegúrate de que `(venv)` esté activo).
    *Si no lo está, escribe: `call venv\Scripts\activate.bat`*

2.  Ejecuta el script de Python:
    ```cmd
    python dashboard.py
    ```

3.  ¡Listo! Se abrirá la ventana del dashboard. Presiona **"Conectar"** y deberías empezar a ver los datos de tu Arduino.


---

## 🚨 Guía de Solución de Errores

Si algo falla, busca tu error aquí.

| Problema / Error | Solución (Causa Más Común) |
| :--- | :--- |
| `[Errno 2] No such file or directory` | **Estás en la carpeta incorrecta.** Asegúrate de que tu terminal esté en la carpeta raíz `Porton-Arduino` (donde está `dashboard.py`) antes de ejecutar `python dashboard.py`. |
| `ModuleNotFoundError: No module named 'serial'` (o `matplotlib`) | **Olvidaste activar el entorno virtual.** Cierra la terminal, ábrela de nuevo, y ejecuta `call venv\Scripts\activate.bat` antes de correr el script. |
| El dashboard dice: `Error: No se encuentra COM...` | **El `PUERTO_SERIAL` está mal.** Revisa el **Paso 3**. Asegúrate de que el COM en el código es el mismo que el del Administrador de Dispositivos. |
| La app conecta, pero no llegan datos (todo en `---`) | **El Arduino no envía datos.** Revisa el **Paso 1**. Abre el Monitor Serie del IDE de Arduino. Si no ves líneas `D:...,M:...`, el problema está en el código o cableado del Arduino. |
| `TclError: unknown option "-background"` | **Error de estilo en el código.** Estás usando `background=` en un widget `ttk`. Debes usar `ttk.Style().configure(...)` para cambiar la apariencia de esos widgets. |
| `Too early to create variable: no default root window` | **Error de código.** Creaste una variable de Tkinter (como `tk.StringVar()`) *antes* de la línea `root = tk.Tk()`. Debes crear `root` primero. |


---

## 📎 Notas de despliegue rápido (web / Render)

- El directorio `web_app/` contiene una versión web (Flask + SocketIO + Chart.js). Está pensada para deploy en Render, pero recuerda que los hosts en la nube no ven tu USB local. Si quieres datos reales en la nube necesitas un ESP32/ESP8266 o un gateway local.

### Ejecutar localmente (resumen)

```cmd
cd Sketch_Porton\web_app
python -m venv venv_web
call venv_web\Scripts\activate.bat
pip install -r requirements.txt
python app.py
```

### Deploy (comandos para Render)

- Build: `pip install -r web_app/requirements.txt`
- Start: `gunicorn -k eventlet -w 1 web_app.app:app`


---

## ✅ Siguientes pasos recomendados (puedo hacerlo por ti)

- Limpiar los prints/diagnósticos en `dashboard.py` para dejarlo listo para producción.
- Añadir un endpoint HTTP `/ingest` en `web_app/app.py` y ejemplo de código para ESP32 que haga POST con JSON {dist, mov} — así podrás enviar datos reales desde WiFi.
- Generar `build_exe.bat` con la línea de PyInstaller y opciones recomendadas.

Indica cuál de estas tres acciones quieres que haga ahora y me pongo a ello.

---

### Contacto rápido

Si necesitas que prepare un instalador `.exe`, el endpoint para ESP32 o el deploy en Render paso a paso, dime cuál prefieres y lo implemento.
