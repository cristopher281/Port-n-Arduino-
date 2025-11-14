@echo off
REM Cambia al directorio del script y ejecuta el dashboard
cd /d "%~dp0"

REM Si existe un virtualenv local, actívalo para aislar dependencias
if exist "venv\Scripts\activate.bat" (
	echo Activando entorno virtual venv...
	call "venv\Scripts\activate.bat"
@echo off
REM Cambia al directorio del script y ejecuta el dashboard
cd /d "%~dp0"

REM Si existe un virtualenv local, actívalo para aislar dependencias



@echo off
REM run_dashboard.bat - versión limpia: activa venv, instala deps y arranca dashboard.py
cd /d "%~dp0"

REM Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
	echo Activando entorno virtual venv...
	call "venv\Scripts\activate.bat"
) else (
	echo No se detecto entorno virtual local (venv). Se usara Python del sistema.
)

REM Actualizar pip e instalar dependencias (si existe requirements.txt)
python -m pip install --upgrade pip
if exist requirements.txt (
	python -m pip install -r requirements.txt
)

REM Ejecutar dashboard
python "dashboard.py"

REM Mantener la ventana abierta para ver errores (quita 'pause' si no lo deseas)
pause
