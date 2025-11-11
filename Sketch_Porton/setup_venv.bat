@echo off
REM Crea un entorno virtual 'venv' e instala las dependencias del proyecto
cd /d "%~dp0"

echo Creando entorno virtual en .\venv ...
python -m venv venv

echo Activando entorno virtual e instalando dependencias...
call "venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo Entorno virtual creado y dependencias instaladas.
echo Para ejecutar el dashboard active el entorno con:
echo     call venv\Scripts\activate.bat
echo y luego:
echo     python dashboard.py

pause
