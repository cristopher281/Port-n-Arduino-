@echo off
REM Cambia al directorio del script y ejecuta el dashboard
cd /d "%~dp0"

REM Si existe un virtualenv local, actívalo para aislar dependencias
if exist "venv\Scripts\activate.bat" (
	echo Activando entorno virtual venv...
	call "venv\Scripts\activate.bat"
) else (
	echo No se detecto entorno virtual local (venv). Se usara Python del sistema.
)

echo Instalando/actualizando dependencias (si es necesario)...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt

echo Iniciando dashboard...
python "dashboard.py"

echo El dashboard termino o fue cerrado.
pause
